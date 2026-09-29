# 🌱 EcoSynk — Plataforma de Monitoramento Modular de Resíduos Orgânicos

MVP Fase 2 desenvolvido em Python + Flask para apresentação acadêmica e demonstração do conceito de **Sistema do Produto** e **Performance do Produto**.

---

## 🚀 Como Executar o Projeto

1. Certifique-se de ter o Python instalado.
2. Instale o Flask (caso ainda não esteja instalado):
   ```bash
   pip install flask
   ```
3. Inicie o servidor da aplicação:
   ```bash
   python app.py
   ```
4. Abra o navegador no endereço:
   👉 **http://127.0.0.1:5000**

---

## ✨ Recursos Implementados no MVP (Opção 2)

- **Identidade Visual**: Logotipo oficial da EcoSynk no cabeçalho e paleta moderna voltada à sustentabilidade.
- **Indicadores Globais**:
  - Total processado acumulado (125 kg).
  - Quantidade de módulos ativos (3 módulos).
  - Status geral da operação (Normal / Atenção).
- **Múltiplos Módulos Instalados**:
  - `EC-001`: Restaurante Central (🟢 Normal)
  - `EC-002`: Cozinha Industrial (🟢 Normal)
  - `EC-003`: Refeitório Anexo (🟡 Atenção - Temperatura elevada)
  - Navegação entre módulos ao clicar na lista lateral.
- **Métricas do Módulo em Tempo Real**:
  - Resíduos processados hoje (kg).
  - Temperatura interna (°C) com threshold de segurança.
  - Umidade (%).
  - Status individual automático.
- **Gráfico de Evolução (Chart.js)**:
  - Curva de resíduos processados ao longo dos dias.
- **Tabela de Histórico**:
  - Registros de datas anteriores com resíduos, temperatura, umidade e status.
- **Alertas Automáticos**:
  - Notificação de aviso visual quando a temperatura ultrapassa 50 °C (ex: `⚠️ Temperatura acima do limite no módulo EC-003`).
- **Botão "Atualizar dados" interativo**:
  - Simula novas leituras de sensores em tempo real via chamada assíncrona (AJAX / API).
