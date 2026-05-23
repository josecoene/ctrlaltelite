import sys
import os
from main import run_pipeline

def run_tests():
    print("====================================================")
    print("      INICIANDO TESTES AUTOMATIZADOS - FROSTGUARD    ")
    print("====================================================")
    
    # Test Scenario 1: Normal Flow
    print("\n--- CASO DE TESTE 1: Fluxo Normal (Dados em Tempo Real) ---")
    try:
        status = run_pipeline(simulated_anomaly=None)
        print(f"Resultado do Caso 1: Concluido. Status retornado: {status}")
    except Exception as e:
        print(f"ERRO no Caso 1: {e}")
        
    # Test Scenario 2: Motor current imbalance anomaly
    print("\n--- CASO DE TESTE 2: Simulação de Desequilíbrio Elétrico no Compressor ---")
    try:
        status = run_pipeline(simulated_anomaly="motor")
        print(f"Resultado do Caso 2: Concluido. Status retornado: {status}")
        assert status == "CRITICAL" or status == "WARNING", "Deveria detectar alerta elétrico!"
    except Exception as e:
        print(f"ERRO no Caso 2: {e}")
        
    # Test Scenario 3: Thermal loss anomaly
    print("\n--- CASO DE TESTE 3: Simulação de Perda Térmica (Porta Aberta e Temp Quente) ---")
    try:
        status = run_pipeline(simulated_anomaly="thermal")
        print(f"Resultado do Caso 3: Concluido. Status retornado: {status}")
        assert status == "CRITICAL", "Deveria detectar risco crítico de perda térmica!"
    except Exception as e:
        print(f"ERRO no Caso 3: {e}")

    print("\n====================================================")
    print("      TESTES FINALIZADOS! VERIFIQUE OS LOGS ACIMA   ")
    print("====================================================")

if __name__ == "__main__":
    run_tests()
