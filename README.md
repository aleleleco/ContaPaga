# 💰 ContaPaga - Gestão Financeira Inteligente

**ContaPaga** é um sistema robusto de gestão financeira pessoal desenvolvido com **Django 6.0** e **JavaScript**, focado em simplicidade, automação e visualização premium de dados. O sistema evoluiu de um simples controlador de gastos para um hub completo de inteligência bancária.

![Aesthetics](https://img.shields.io/badge/Aesthetics-Premium-blue)
![Django](https://img.shields.io/badge/Framework-Django%206.0-green)
![Python](https://img.shields.io/badge/Language-Python%203.13-yellow)
![Status](https://img.shields.io/badge/Status-100%25%20Operacional-success)

## 🚀 Funcionalidades Principais

### 🏦 Inteligência Bancária & Conciliação (Premium)
- **Conciliação OFX Profissional:** Central de importação persistente com sistema de abas (Pendentes, Validados, Processados e Ignorados).
- **Recurso de Ignorar (OFX):** Ferramenta para descartar transações irrelevantes ou duplicadas, individualmente ou em massa.
- **Multicontas por Agente:** Suporte a múltiplos bancos e contas para cada pagador cadastrado.
- **Identificação de Transferências:** Algoritmo inteligente que detecta e ignora movimentações entre suas próprias contas.
- **Ações em Massa (Bulk):** Atribuição rápida de categorias e vínculos de contas para múltiplos lançamentos.

### 📊 Dashboards & Analytics Avançado
- **Visão por Agente:** Cálculo preciso de Saldo Disponível considerando (Salário + Rendas Extras - Gastos) por pessoa.
- **Análise por Conta:** Novo gráfico horizontal com agrupamento cromático (tons de cor por categoria).
- **Filtros Dinâmicos:** Drill-down instantâneo por categoria dentro dos gráficos de contas.
- **Regime de Caixa:** Gráficos e totais baseados estritamente em contas com status "Pago".
- **Dashboard Financeiro:** Resumo de gastos, pagamentos e economia do mês atual.

### ⚙️ Governança Financeira
- **Agentes Pagadores:** Controle de quem realizou o pagamento, com monitoramento de consumo de salário e saldo restante.
- **Configurações Centralizadas:** Gestão de Contas, Categorias e Agentes sem necessidade do painel administrativo.
- **Contas Fixas e Esporádicas:** Automação de importação de contas recorrentes para novas competências.

### 📂 Integração e Backup
- **Integração Dropbox:** Salvamento de comprovantes em pastas sincronizadas (C:\Users\PC-Leleco\Dropbox\Pessoal\ContasPagas).
- **Relatórios PDF:** Geração de relatórios profissionais de fechamento de mês.
- **Migração de Legado:** Ferramentas prontas para importar dados de sistemas anteriores (SQLite).

## 🛠️ Stack Tecnológica
- **Backend:** Python 3.13 / Django 6.0
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript
- **Icons:** Lucide Icons
- **Charts:** Chart.js
- **Database:** SQLite (Desenvolvimento/Uso Pessoal)
- **Parser:** ofxparse

## 📦 Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd ContaPaga
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute as migrações:**
   ```bash
   python manage.py migrate
   ```

5. **Inicie o servidor:**
   ```bash
   python manage.py runserver
   ```

## 📚 Documentação Técnica
- [Estrutura de Dados & Modelos](DOCS_DATABASE.md): Detalhamento do banco de dados e lógica de conciliação.
- [Roadmap de Desenvolvimento](contapaga-roadmap.md): Histórico de versões e próximos passos.

---

## 🗺️ Roadmap
O progresso detalhado do desenvolvimento pode ser acompanhado no arquivo `contapaga-roadmap.md`. Atualmente o sistema está em sua fase final de refinamento avançado.

---

## 📄 Licença
Este projeto é de **uso livre para fins estritamente pessoais e não profissionais**. É proibida a comercialização ou o uso por empresas sem permissão. Veja o arquivo [LICENSE.md](LICENSE.md) para mais detalhes.

---
**Desenvolvido por [Leleco]** - 2026
