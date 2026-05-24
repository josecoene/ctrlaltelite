# 🧊 ColdGuardian AI

Sistema inteligente de monitoramento industrial com detecção de anomalias em tempo real baseado em sensores de temperatura, energia e estado de portas.

Este projeto foi desenvolvido como um MVP para hackathon, com foco em **simplicidade, explicabilidade e detecção leve de anomalias** usando estatística e um autoencoder simplificado.

---

# 🎯 Objetivo

O ColdGuardian AI monitora sistemas industriais e identifica comportamentos anômalos que podem indicar problemas operacionais.

Ele analisa:

- 🌡️ Temperatura
- ⚡ Consumo energético
- 🚪 Estado de portas (aberta/fechada)
- 📊 Desvios de comportamento ao longo do tempo

E transforma isso em:

- Score de risco
- Status operacional (NORMAL / ATENÇÃO / CRÍTICO)
- Diagnóstico automático
- Visualização gráfica

---

# 🧠 Escopo

✔ MVP funcional para hackathon  
✔ Integração com APIs externas de sensores  
✔ Processamento de dados em tempo real  
✔ Detecção leve de anomalias (autoencoder simplificado)  
✔ API REST com FastAPI  
✔ Visualização de dados com gráfico PNG  

---

# 🏗️ Arquitetura

ColdGuardian AI
│
├── main.py → API FastAPI (endpoints)
├── analyzer.py → lógica de análise + autoencoder leve
├── detector.py → detecção do estado da porta
├── api_client.py → consumo de APIs externas
├── config.py → variáveis de ambiente (.env)
├── visualizer.py → geração de gráficos (PNG)


---

# ⚙️ Stack utilizada

- Python 3.11
- FastAPI
- Uvicorn
- Requests
- NumPy
- Matplotlib
- Python-dotenv

---

# 🚀 Instalação

## 1. Criar ambiente virtual

```bash
python -m venv venv

2. Ativar ambiente
Windows
venv\Scripts\activate
Linux / Mac
source venv/bin/activate
3. Instalar dependências
pip install -r requirements.txt
📦 requirements.txt
fastapi
uvicorn
requests
numpy
python-dotenv
matplotlib
🔐 Configuração (.env)

Crie um arquivo .env na raiz do projeto:

API_KEY=sua_api_key
PORTA_URL=url_sensor_porta
TEMPERATURA_URL=url_sensor_temperatura
MOTOR2_URL=url_sensor_motor
▶️ Executar o projeto
uvicorn main:app --reload

A API ficará disponível em:

http://127.0.0.1:8000
📡 Endpoints
🟢 GET /

Health check da API.

{
  "project": "ColdGuardian AI",
  "status": "running"
}
📊 GET /analyze

Executa análise completa dos sensores.

Exemplo de resposta:
{
  "score": 90,
  "status": "CRITICO",
  "anomalias_detectadas": 70,
  "anomalia_ratio": 0.7,
  "temperatura_media": -6.28,
  "energia_media_total": 9276.95,
  "porta_aberta_count": 100,
  "total_amostras": 100,
  "diagnostic": "Anomalia consistente no padrão energético/térmico."
}
📈 GET /chart

Retorna um gráfico PNG com:

Temperatura
Energia
Erro do autoencoder
Threshold de anomalia

Abra no navegador:

http://127.0.0.1:8000/chart
📚 GET /docs

Swagger automático do FastAPI:

http://127.0.0.1:8000/docs

Permite:

Testar endpoints
Visualizar schemas
Executar requisições
🤖 Autoencoder (versão leve)

Este projeto utiliza um autoencoder simplificado (proxy estatístico):

Como funciona:
Reconstrução dos dados usando média móvel
Cálculo do erro entre valor real e reconstruído
Definição de threshold:
threshold = média + 2 * desvio padrão
Objetivo:

Detectar padrões anômalos como:

Picos de energia
Instabilidade térmica
Comportamento fora do padrão
📊 Lógica de decisão
Status	Condição
NORMAL	baixa taxa de anomalias
ATENÇÃO	variação moderada
CRÍTICO	anomalias persistentes
🔄 Fluxo do sistema
Coleta dados dos sensores via API
Processamento no analyzer
Detecção de estado da porta
Cálculo de energia e temperatura média
Execução do autoencoder leve
Geração de score de risco
Classificação do status
(Opcional) geração de gráfico /chart
🧪 Funcionalidades

✔ Integração com APIs externas
✔ Processamento de dados em tempo real
✔ Detecção de porta aberta/fechada
✔ Cálculo de consumo energético
✔ Autoencoder leve para anomalias
✔ Score de risco dinâmico
✔ Classificação de status
✔ Endpoint de análise
✔ Endpoint de gráfico
✔ Visualização PNG

🏁 Objetivo final

Criar um sistema simples, explicável e funcional para:

Monitoramento industrial inteligente com detecção leve de anomalias em tempo real.