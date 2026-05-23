def calculate_imbalance(phase_a, phase_b, phase_c):
    """
    Calculates the NEMA percentage imbalance for a three-phase system.
    Formula: (Max deviation from average / Average) * 100
    """
    # Filter out None values
    phases = [p for p in [phase_a, phase_b, phase_c] if p is not None]
    if len(phases) < 3:
        return 0.0 # Can't calculate imbalance with missing phases
        
    avg = sum(phases) / 3.0
    if avg == 0.0:
        return 0.0
        
    max_deviation = max(abs(p - avg) for p in phases)
    imbalance = (max_deviation / avg) * 100.0
    return round(imbalance, 2)

def calculate_power_factor_score(avg_pf):
    """
    Scores the power factor (0-100). Brazillian regulation requires >= 0.92.
    """
    if avg_pf is None:
        return 100.0
    
    avg_pf = abs(avg_pf) # Ensure positive
    if avg_pf >= 0.92:
        return 100.0
    elif avg_pf >= 0.80:
        # Scale between 50 and 100
        return 50.0 + (avg_pf - 0.80) / (0.92 - 0.80) * 50.0
    else:
        # Critical, below 0.80 is very low
        return max(0.0, avg_pf / 0.80 * 50.0)

def calculate_health_score(metrics):
    """
    Calculates a comprehensive operational health score (0-100) for a compressor.
    metrics dictionary keys:
      - current_imbalance (float)
      - voltage_imbalance (float)
      - avg_voltage (float)
      - avg_pf (float)
      - compressor_temp (float, optional)
      - nominal_voltage (float, default 127.0)
    """
    # 1. Current Imbalance Score (Weight: 35%)
    curr_imb = metrics.get("current_imbalance", 0.0)
    if curr_imb <= 5.0:
        curr_score = 100.0
    elif curr_imb <= 10.0:
        # Scale 100 to 70
        curr_score = 100.0 - (curr_imb - 5.0) / 5.0 * 30.0
    elif curr_imb <= 15.0:
        # Scale 70 to 30
        curr_score = 70.0 - (curr_imb - 10.0) / 5.0 * 40.0
    else:
        curr_score = max(0.0, 30.0 - (curr_imb - 15.0) / 5.0 * 30.0)

    # 2. Voltage Imbalance Score (Weight: 20%)
    volt_imb = metrics.get("voltage_imbalance", 0.0)
    if volt_imb <= 1.0:
        volt_imb_score = 100.0
    elif volt_imb <= 2.0:
        volt_imb_score = 100.0 - (volt_imb - 1.0) * 20.0 # 100 to 80
    elif volt_imb <= 3.0:
        volt_imb_score = 80.0 - (volt_imb - 2.0) * 30.0 # 80 to 50
    else:
        volt_imb_score = max(0.0, 50.0 - (volt_imb - 3.0) * 25.0)

    # 3. Voltage Level Deviation Score (Weight: 15%)
    avg_volt = metrics.get("avg_voltage", 127.0)
    nom_volt = metrics.get("nominal_voltage", 127.0)
    volt_dev = abs(avg_volt - nom_volt) / nom_volt * 100.0 # Percentage deviation
    if volt_dev <= 5.0:
        volt_dev_score = 100.0
    elif volt_dev <= 10.0:
        volt_dev_score = 100.0 - (volt_dev - 5.0) / 5.0 * 40.0 # 100 to 60
    else:
        volt_dev_score = max(0.0, 60.0 - (volt_dev - 10.0) / 10.0 * 60.0)

    # 4. Power Factor Score (Weight: 15%)
    pf_score = calculate_power_factor_score(metrics.get("avg_pf", 0.95))

    # 5. Compressor Temperature Score (Weight: 15%)
    temp = metrics.get("compressor_temp")
    if temp is None:
        # If no temperature is available, redistribute its weight (15%) to current and power factor
        score = (curr_score * 0.45) + (volt_imb_score * 0.20) + (volt_dev_score * 0.15) + (pf_score * 0.20)
    else:
        if temp <= 65.0:
            temp_score = 100.0
        elif temp <= 80.0:
            temp_score = 100.0 - (temp - 65.0) / 15.0 * 50.0 # 100 to 50
        elif temp <= 95.0:
            temp_score = 50.0 - (temp - 80.0) / 15.0 * 40.0 # 50 to 10
        else:
            temp_score = max(0.0, 10.0 - (temp - 95.0) / 10.0 * 10.0)
            
        score = (curr_score * 0.35) + (volt_imb_score * 0.20) + (volt_dev_score * 0.15) + (pf_score * 0.15) + (temp_score * 0.15)

    return round(score, 1)

def detect_risks(metrics, chamber_temp=None, door_open=False, door_seconds=0.0):
    """
    Analyzes metrics and returns active warnings, alerts and overall operational risk state.
    """
    risks = []
    status = "NORMAL" # NORMAL, WARNING, CRITICAL
    
    # Check current imbalance
    curr_imb = metrics.get("current_imbalance", 0.0)
    if curr_imb > 12.0:
        risks.append(f"ALERTA: Alto desequilíbrio de corrente ({curr_imb}%). Risco de queima do motor!")
        status = "CRITICAL"
    elif curr_imb > 7.0:
        risks.append(f"AVISO: Desequilíbrio de corrente elevado ({curr_imb}%).")
        status = "WARNING" if status != "CRITICAL" else "CRITICAL"
        
    # Check Power Factor
    avg_pf = metrics.get("avg_pf", 1.0)
    if avg_pf < 0.92:
        risks.append(f"AVISO: Fator de potência baixo ({avg_pf:.3f}). Risco de multa por energia reativa.")
        if status == "NORMAL":
            status = "WARNING"

    # Check compressor temperature
    temp = metrics.get("compressor_temp")
    if temp is not None:
        if temp > 85.0:
            risks.append(f"ALERTA: Superaquecimento no compressor ({temp}°C).")
            status = "CRITICAL"
        elif temp > 72.0:
            risks.append(f"AVISO: Temperatura do compressor elevada ({temp}°C).")
            status = "WARNING" if status != "CRITICAL" else "CRITICAL"

    # Check Cold Chamber temperature (very critical for ice cream!)
    if chamber_temp is not None:
        if chamber_temp > -10.0:
            risks.append(f"CRÍTICO: Temperatura da câmara elevada ({chamber_temp}°C). Degradação imediata de sorvetes!")
            status = "CRITICAL"
        elif chamber_temp > -15.0:
            risks.append(f"AVISO: Temperatura da câmara subindo ({chamber_temp}°C). Ideal é abaixo de -18°C.")
            status = "WARNING" if status != "CRITICAL" else "CRITICAL"

    # Check Door open
    if door_open:
        door_mins = int(door_seconds / 60.0)
        if door_seconds > 600: # 10 minutes
            risks.append(f"CRÍTICO: Porta aberta há {door_seconds:.0f} segundos ({door_mins} min). Alta perda térmica!")
            status = "CRITICAL"
        elif door_seconds > 180: # 3 minutes
            risks.append(f"AVISO: Porta aberta há {door_seconds:.0f} segundos ({door_mins} min).")
            status = "WARNING" if status != "CRITICAL" else "CRITICAL"
        else:
            risks.append(f"AVISO: Porta aberta há {door_seconds:.0f} segundos.")
            if status == "NORMAL":
                status = "WARNING"
            
    return status, risks

def estimate_operational_loss(chamber_temp, duration_minutes, stock_value=50000.0):
    """
    Estimates the potential loss in Reais (R$) if the freezer chamber is outside the safety threshold.
    Standard safety threshold for ice cream: <= -18°C.
    Melt/Loss process starts accelerating above -10°C.
    We assume the entire stock (worth stock_value, default R$ 50,000) is lost in 4 hours (240 mins) if temp stays > -10°C.
    """
    if chamber_temp is None or chamber_temp <= -18.0 or duration_minutes <= 0:
        return 0.0
        
    # Scale degradation factor based on how high the temperature is above -18°C
    # Max degradation occurs at 0°C or higher
    temp_factor = min(1.0, (chamber_temp - (-18.0)) / (0.0 - (-18.0)))
    
    # 4 hours (240 minutes) is the typical threshold where ice cream melts and loses texture permanently
    time_factor = min(1.0, duration_minutes / 240.0)
    
    estimated_loss = stock_value * temp_factor * time_factor
    return round(estimated_loss, 2)
