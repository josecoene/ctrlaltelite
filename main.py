import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

from api_client import BEMApiClient
from analytics import calculate_imbalance, calculate_health_score, detect_risks, estimate_operational_loss
from alerts import send_discord_alert

load_dotenv()

def save_to_csv(data_dict, file_name="frostguard_data.csv"):
    """
    Saves a data row directly to a local CSV file.
    No external Google API credentials required.
    """
    headers = [
        "timestamp", "sensor_id", 
        "corrente_a", "corrente_b", "corrente_c", "desequilibrio_corrente",
        "tensao_a", "tensao_b", "tensao_c", "desequilibrio_tensao",
        "fator_potencia_medio", "temp_compressor", "temp_camara", "porta_aberta",
        "health_score", "status_risco", "prejuizo_previsto"
    ]
    file_exists = os.path.exists(file_name)
    row_values = []
    for h in headers:
        val = data_dict.get(h, "")
        if isinstance(val, datetime):
            val = val.strftime("%Y-%m-%d %H:%M:%S")
        row_values.append(val)
        
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow(row_values)
        print(f"   [Banco de Dados] Dados salvos no CSV local '{file_name}' com sucesso.")
        return True
    except Exception as e:
        print(f"   [Erro Banco de Dados] Falha ao salvar no CSV local: {e}")
        return False

def run_pipeline(simulated_anomaly=None):
    """
    Executes a single workflow cycle.
    If simulated_anomaly is set, it will manually inject fault parameters to trigger alerts.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando processamento de dados...")
    
    api = BEMApiClient()
    
    # 1. Fetch sensor data from BEM API sandbox
    # Using a 1-hour window to ensure we get the latest points
    comp_data = api.get_sensor_data("estoque_compressor_1", start="-1h", limit=100)
    temp_data = api.get_sensor_data("estoque_temperatura", start="-1h", limit=100)
    porta_data = api.get_sensor_data("estoque_porta", start="-1h", limit=100)
    
    # 2. Extract latest values
    # Default fallback values in case API returns empty lists
    curr_a, curr_b, curr_c = 135.0, 137.0, 134.0
    volt_a, volt_b, volt_c = 220.0, 220.0, 220.0
    pf_a, pf_b, pf_c = 0.95, 0.94, 0.96
    chamber_temp = -19.5
    door_seconds = 0.0
    
    # Extract from compressor points (last reading is the most recent)
    timestamp = datetime.now()
    if comp_data and comp_data.get("points"):
        latest_point = comp_data["points"][-1]
        curr_a = latest_point.get("corrente_fase_a", curr_a)
        curr_b = latest_point.get("corrente_fase_b", curr_b)
        curr_c = latest_point.get("corrente_fase_c", curr_c)
        volt_a = latest_point.get("tensao_fase_a", volt_a)
        volt_b = latest_point.get("tensao_fase_b", volt_b)
        volt_c = latest_point.get("tensao_fase_c", volt_c)
        pf_a = latest_point.get("fator_potencia_a", pf_a)
        pf_b = latest_point.get("fator_potencia_b", pf_b)
        pf_c = latest_point.get("fator_potencia_c", pf_c)
        
        # Use API point timestamp if available
        try:
            timestamp_str = latest_point.get("time")
            # Parse RFC3339 timestamp (e.g. 2026-05-22T16:55:12.539664Z)
            timestamp = datetime.strptime(timestamp_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass

    # Extract chamber temperature
    if temp_data and temp_data.get("points"):
        chamber_temp = temp_data["points"][-1].get("temperatura", chamber_temp)

    # Extract door status (interpreting value directly as seconds)
    if porta_data and porta_data.get("points"):
        door_seconds = porta_data["points"][-1].get("abertura_porta", door_seconds)

    # Convert door signal to boolean (open if open for more than 5 seconds)
    door_open = True if door_seconds > 5.0 else False
    door_open_duration = int(door_seconds / 60.0) # Duration in minutes for rules

    # Calculate how long the temperature was high in the fetched window (in minutes)
    temp_high_duration = 0
    if temp_data and temp_data.get("points"):
        temp_high_duration = sum(1 for pt in temp_data["points"] if pt.get("temperatura", -20.0) > -18.0)

    # 3. Inject Simulated Anomalies if requested (for live pitch demonstration)
    if simulated_anomaly == "motor":
        print("\n[SIMULACAO] Injetando falha eletrica no compressor (desequilibrio de corrente)...")
        curr_a = 110.0
        curr_b = 180.0 # High deviation
        curr_c = 125.0
    elif simulated_anomaly == "thermal":
        print("\n[SIMULACAO] Injetando perda termica na camara (temperatura elevada e porta aberta)...")
        chamber_temp = -7.5 # Very dangerous for ice cream
        door_open = True
        door_seconds = 900.0 # 15 minutes open (900 seconds)
        door_open_duration = 15 # 15 minutes open
        temp_high_duration = 45 # 45 minutes above limit
    elif simulated_anomaly == "reactive":
        print("\n[SIMULACAO] Injetando baixo fator de potencia...")
        pf_a, pf_b, pf_c = 0.82, 0.81, 0.80

    # 4. Perform Analytics Calculations
    imbalance_curr = calculate_imbalance(curr_a, curr_b, curr_c)
    imbalance_volt = calculate_imbalance(volt_a, volt_b, volt_c)
    
    avg_volt = (volt_a + volt_b + volt_c) / 3.0
    avg_pf = (abs(pf_a) + abs(pf_b) + abs(pf_c)) / 3.0
    
    metrics = {
        "current_imbalance": imbalance_curr,
        "voltage_imbalance": imbalance_volt,
        "avg_voltage": avg_volt,
        "avg_pf": avg_pf,
        "nominal_voltage": 220.0 # The compressor runs at 220V
    }
    
    health_score = calculate_health_score(metrics)
    status_risco, list_risks = detect_risks(
        metrics, 
        chamber_temp=chamber_temp, 
        door_open=door_open, 
        door_seconds=door_seconds
    )
    
    prejuizo_previsto = estimate_operational_loss(chamber_temp, temp_high_duration, stock_value=65000.0)

    # 5. Build final data row
    data_row = {
        "timestamp": timestamp,
        "sensor_id": "estoque_compressor_1",
        "corrente_a": curr_a,
        "corrente_b": curr_b,
        "corrente_c": curr_c,
        "desequilibrio_corrente": imbalance_curr,
        "tensao_a": volt_a,
        "tensao_b": volt_b,
        "tensao_c": volt_c,
        "desequilibrio_tensao": imbalance_volt,
        "fator_potencia_medio": round(avg_pf, 3),
        "temp_compressor": None, # Sensor doesn't provide compressor temp
        "temp_camara": chamber_temp,
        "porta_aberta": door_seconds,
        "health_score": health_score,
        "status_risco": status_risco,
        "prejuizo_previsto": prejuizo_previsto
    }
    
    # 6. Save data directly to local CSV
    save_to_csv(data_row)
    
    # 7. Print summary console logs
    print(f"--- Sumario Analitico ---")
    print(f"Imbalance Corrente: {imbalance_curr}%")
    print(f"Imbalance Tensao: {imbalance_volt}%")
    print(f"FP Medio: {avg_pf:.3f}")
    print(f"Temp Camara: {chamber_temp}°C")
    print(f"Porta Aberta: {door_open} ({door_seconds:.0f} seg / {door_open_duration} min)")
    print(f"Score de Saude: {health_score}%")
    print(f"Risco Operacional: {status_risco}")
    print(f"Prejuizo Estimado: R$ {prejuizo_previsto:.2f}")
    
    # 8. Send Instant Webhook Alert if warning or critical
    if status_risco in ["WARNING", "CRITICAL"]:
        send_discord_alert(status_risco, list_risks, metrics, chamber_temp)
        
    return status_risco

def main():
    print("====================================================")
    print("      FROSTGUARD AI - MONITORAMENTO PREVENTIVO      ")
    print("====================================================")
    print("Para simular cenarios anomalos na apresentacao:")
    print(" -> Digite '1' para simular desequilibrio de corrente no compressor")
    print(" -> Digite '2' para simular falha termica na camara fria")
    print(" -> Digite '3' para simular baixo fator de potencia")
    print(" -> Digite '0' para rodar com dados puros em tempo real")
    print("====================================================")
    
    option = input("Selecione uma opcao para iniciar (Padrao: 0): ").strip()
    
    anomaly = None
    if option == "1":
        anomaly = "motor"
    elif option == "2":
        anomaly = "thermal"
    elif option == "3":
        anomaly = "reactive"
        
    # Single execution for testing, or loop
    run_pipeline(simulated_anomaly=anomaly)
    
    print("\nExecucao concluida. Deseja rodar o loop de monitoramento continuo a cada 60s?")
    loop_choice = input("Iniciar loop? (s/n): ").strip().lower()
    
    if loop_choice == 's':
        print("\nIniciando monitoramento continuo... Pressione Ctrl+C para interromper.")
        try:
            while True:
                run_pipeline(simulated_anomaly=anomaly)
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuario.")

if __name__ == "__main__":
    main()
