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

def run_monitoring_cycle(last_statuses):
    """
    Runs a real-time monitoring and diagnostic cycle for both compressors.
    last_statuses is a dictionary tracking the previous state of each compressor.
    """
    api = BEMApiClient()
    
    # 1. Fetch common chamber readings (start=-30m, stop=now, limit=10)
    print("\n[PASSO 1: Chamada API - Ambiente]")
    print(f" -> GET https://desafio.beminteligencia.com.br/api/v1/data?sensor=estoque_temperatura&start=-30m&stop=now&limit=10")
    temp_data = api.get_sensor_data("estoque_temperatura", start="-30m", stop="now", limit=10)
    
    print(f" -> GET https://desafio.beminteligencia.com.br/api/v1/data?sensor=estoque_porta&start=-30m&stop=now&limit=10")
    porta_data = api.get_sensor_data("estoque_porta", start="-30m", stop="now", limit=10)
    
    # Default values for chamber
    chamber_temp = -19.5
    door_seconds = 0.0
    
    # Parse latest chamber temperature reading
    if temp_data and temp_data.get("points"):
        pt_count = len(temp_data["points"])
        chamber_temp = temp_data["points"][-1].get("temperatura", chamber_temp)
        print(f"   [Tratamento: Temperatura] Extraido ponto mais recente ({temp_data['points'][-1]['time']}) de {pt_count} pontos recebidos: {chamber_temp}C")
    else:
        print("   [Tratamento: Temperatura] Nenhum ponto recebido. Utilizando fallback: -19.5C")

    # Parse latest door opening duration (seconds)
    if porta_data and porta_data.get("points"):
        pt_count = len(porta_data["points"])
        door_seconds = porta_data["points"][-1].get("abertura_porta", door_seconds)
        print(f"   [Tratamento: Porta] Extraido ponto mais recente ({porta_data['points'][-1]['time']}) de {pt_count} pontos recebidos: {door_seconds} seg")
    else:
        print("   [Tratamento: Porta] Nenhum ponto recebido. Utilizando fallback: 0.0 seg")

    door_open = True if door_seconds > 5.0 else False
    door_open_duration = int(door_seconds / 60.0) # converted to minutes for alerts
    
    # Count how many minutes in the last 30 min the temperature was above safe limits (-18°C)
    temp_high_duration = 0
    if temp_data and temp_data.get("points"):
        temp_high_duration = sum(1 for pt in temp_data["points"] if pt.get("temperatura", -20.0) > -18.0)
    print(f"   [Tratamento: Perda Termica] Minutos acima de -18C nos ultimos 30 min: {temp_high_duration} min")

    # Calculate operational financial loss if temperature is high
    prejuizo_previsto = estimate_operational_loss(chamber_temp, temp_high_duration, stock_value=65000.0)
    print(f"   [Tratamento: Perda Financeira] Formula: R$65.000 * ((Temp - (-18)) / 18) * (Minutos_Anomalia / 240)")

    # List of compressors to monitor
    compressors = ["estoque_compressor_1", "estoque_compressor_2"]
    new_statuses = {}

    print("\n" + "="*60)
    print(f"FrostGuard AI | Monitoramento em Tempo Real - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"Ambiente Camara Fria:")
    print(f"   - Temperatura: {chamber_temp}C (Alvo: <-18C)")
    print(f"   - Porta Aberta: {'Sim' if door_open else 'Nao'} ({door_seconds:.0f}s / {door_open_duration} min)")
    print(f"   - Prejuizo Projetado do Estoque: R$ {prejuizo_previsto:.2f}")
    print("-" * 60)

    for comp_id in compressors:
        # Fetch individual compressor electrical data (start=-30m, stop=now, limit=10)
        print(f"\n[PASSO 2: Chamada API - Eletrica {comp_id.upper()}]")
        print(f" -> GET https://desafio.beminteligencia.com.br/api/v1/data?sensor={comp_id}&start=-30m&stop=now&limit=10")
        comp_data = api.get_sensor_data(comp_id, start="-30m", stop="now", limit=10)
        
        # Default electrical values
        curr_a, curr_b, curr_c = 135.0, 137.0, 134.0
        volt_a, volt_b, volt_c = 220.0, 220.0, 220.0
        pf_a, pf_b, pf_c = 0.95, 0.94, 0.96
        timestamp = datetime.now()
        
        if comp_data and comp_data.get("points"):
            pt_count = len(comp_data["points"])
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
            
            try:
                timestamp_str = latest_point.get("time")
                timestamp = datetime.strptime(timestamp_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                print(f"   [Tratamento: Eletrico] Extraido ponto mais recente ({timestamp_str}) de {pt_count} pontos recebidos.")
            except Exception:
                pass
        else:
            print("   [Tratamento: Eletrico] Nenhum ponto recebido. Utilizando fallback estatico de operacao segura.")

        # Calculations
        imbalance_curr = calculate_imbalance(curr_a, curr_b, curr_c)
        imbalance_volt = calculate_imbalance(volt_a, volt_b, volt_c)
        print(f"   [Calculo: NEMA] Desequilibrio de Corrente: (Desvio_Max / Media) * 100 = {imbalance_curr}%")
        
        avg_volt = (volt_a + volt_b + volt_c) / 3.0
        avg_pf = (abs(pf_a) + abs(pf_b) + abs(pf_c)) / 3.0
        
        metrics = {
            "current_imbalance": imbalance_curr,
            "voltage_imbalance": imbalance_volt,
            "avg_voltage": avg_volt,
            "avg_pf": avg_pf,
            "nominal_voltage": 220.0
        }
        
        health_score = calculate_health_score(metrics)
        print(f"   [Calculo: Health Score] Media ponderada (Corrente 35%, FP 15%, Tensao 20%, Desvio 15%) = {health_score}%")
        
        status_risco, list_risks = detect_risks(
            metrics, 
            chamber_temp=chamber_temp, 
            door_open=door_open, 
            door_seconds=door_seconds
        )

        # Prepare database row
        data_row = {
            "timestamp": timestamp,
            "sensor_id": comp_id,
            "corrente_a": curr_a,
            "corrente_b": curr_b,
            "corrente_c": curr_c,
            "desequilibrio_corrente": imbalance_curr,
            "tensao_a": volt_a,
            "tensao_b": volt_b,
            "tensao_c": volt_c,
            "desequilibrio_tensao": imbalance_volt,
            "fator_potencia_medio": round(avg_pf, 3),
            "temp_compressor": None,
            "temp_camara": chamber_temp,
            "porta_aberta": door_seconds,
            "health_score": health_score,
            "status_risco": status_risco,
            "prejuizo_previsto": prejuizo_previsto
        }
        
        # Save directly to local CSV
        save_to_csv(data_row)
        
        # Output compressor metrics to console
        print(f"Motor: {comp_id.upper()}")
        print(f"   - Correntes: A={curr_a}A, B={curr_b}A, C={curr_c}A (Desequilibrio: {imbalance_curr}%)")
        print(f"   - Tensoes: A={volt_a}V, B={volt_b}V, C={volt_c}V (Desequilibrio: {imbalance_volt}%)")
        print(f"   - Fator de Potencia: {avg_pf:.3f}")
        print(f"   - Score de Saude: {health_score}% | Risco: {status_risco}")
        
        # Check alerts
        last_status = last_statuses.get(comp_id, "NORMAL")
        new_statuses[comp_id] = status_risco
        
        if status_risco in ["WARNING", "CRITICAL"]:
            if status_risco != last_status:
                print(f"   [ALERTA] Novo alerta para {comp_id}! Enviando para o Discord...")
                # Format list of risks to prefix with compressor name
                labeled_risks = [f"[{comp_id.upper()}] {r}" for r in list_risks]
                send_discord_alert(status_risco, labeled_risks, metrics, chamber_temp)
            else:
                print("   [INFO] Alerta ativo ja disparado anteriormente. Evitando spam.")
        elif status_risco == "NORMAL" and last_status in ["WARNING", "CRITICAL"]:
            print(f"   [OK] Normalizacao para {comp_id}! Enviando para o Discord...")
            send_discord_alert("NORMAL", [f"[{comp_id.upper()}] Operação normalizada. Equipamento operando em faixa segura."], metrics, chamber_temp)
        
        print("-" * 60)

    return new_statuses

def main():
    print("====================================================")
    print("      FROSTGUARD AI - DAEMON DE MONITORAMENTO       ")
    print("====================================================")
    print("Iniciando monitoramento de 2 compressores em tempo real...")
    print("Parâmetros de leitura (start=-30m, stop=now, limit=10)...")
    print("Para sair, pressione Ctrl+C.")
    print("====================================================")
    
    last_statuses = {"estoque_compressor_1": "NORMAL", "estoque_compressor_2": "NORMAL"}
    interval = 60 # Check every 60 seconds
    
    try:
        while True:
            last_statuses = run_monitoring_cycle(last_statuses)
            print(f"\n[Aguardando {interval}s para a próxima leitura...]")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nDaemon de monitoramento encerrado pelo operador.")

if __name__ == "__main__":
    main()
