# 💰 ContaPaga - Gestão Financeira Inteligente

**ContaPaga** é um sistema robusto de gestão financeira pessoal desenvolvido com **Django 6.0** e **JavaScript**, focado em simplicidade, automação e visualização premium de dados.

![Aesthetics](https://img.shields.io/badge/Aesthetics-Premium-blue)
![Django](https://img.shields.io/badge/Framework-Django%206.0-green)
![Python](https://img.shields.io/badge/Language-Python%203.13-yellow)

## 🚀 Funcionalidades Principais

### 📊 Dashboards & Visualização
- **Visão Mensal:** Resumo de gastos, pagamentos e economia do mês atual.
- **Gráficos Dinâmicos:** Visualização por categoria (Donut) e comparativo de contas fixas (Bar) via Chart.js.
- **Gestão de Parcelamentos:** Cards interativos com progresso de quitação e gráficos de pizza.

### ⚙️ Governança Financeira
- **Agentes Pagadores:** Controle de quem realizou o pagamento, com monitoramento de consumo de salário e saldo restante.
- **Configurações Centralizadas:** Gestão de Contas, Categorias e Agentes sem necessidade do painel administrativo.
- **Contas Fixas e Esporádicas:** Automação de importação de contas recorrentes para novas competências.

### 📂 Integração e Backup
- **Integração Dropbox:** Lógica preparada para salvamento de comprovantes em pastas sincronizadas.
- **Relatórios PDF:** Geração de relatórios profissionais de fechamento de mês.
- **Migração de Legado:** Ferramentas prontas para importar dados de sistemas anteriores.

## 🛠️ Stack Tecnológica
- **Backend:** Python 3.13 / Django 6.0
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript
- **Icons:** Lucide Icons
- **Charts:** Chart.js
- **Database:** SQLite (Desenvolvimento) / PostgreSQL (Recomendado para Produção)

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

---

## 🗺️ Roadmap
O progresso detalhado do desenvolvimento pode ser acompanhado no arquivo `contapaga-roadmap.md`. Atualmente o sistema está em sua versão estável 1.0.

---
**Desenvolvido por [Leleco]** - 2026
