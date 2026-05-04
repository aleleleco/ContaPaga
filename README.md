# 💰 ContaPaga - Gestão Financeira Inteligente

**ContaPaga** é um sistema robusto de gestão financeira pessoal desenvolvido com **Django 6.0** e **JavaScript**, focado em simplicidade, automação e visualização premium de dados. O sistema evoluiu de um simples controlador de gastos para um hub completo de inteligência bancária.

![Aesthetics](https://img.shields.io/badge/Aesthetics-Premium-blue)
![Django](https://img.shields.io/badge/Framework-Django%206.0-green)
![Python](https://img.shields.io/badge/Language-Python%203.13-yellow)
![Status](https://img.shields.io/badge/Status-98%25%20Operacional-success)

## 🚀 Funcionalidades Principais

### 🏦 Inteligência Bancária & Conciliação (Novo!)
- **Conciliação OFX Profissional:** Central de importação persistente com sistema de abas (Pendentes, Validados, Processados e Ignorados).
- **Multicontas por Agente:** Suporte a múltiplos bancos e contas para cada pagador cadastrado.
- **Gestão de Chaves PIX:** Cadastro e organização de chaves bancárias (CPF, E-mail, Celular, Aleatória).
- **Identificação de Transferências:** Algoritmo inteligente que detecta e ignora movimentações entre suas próprias contas, evitando duplicidade no saldo.
- **Ações em Massa (Bulk):** Atribuição rápida de categorias e vínculos de contas para múltiplos lançamentos simultaneamente.

### 📊 Dashboards & Visualização
- **Visão Mensal:** Resumo de gastos, pagamentos e economia do mês atual.
- **Gráficos Dinâmicos:** Visualização por categoria (Donut) e comparativo de contas fixas (Bar) via Chart.js.
- **Salário Dinâmico:** Monitoramento em tempo real de receitas em contas marcadas como "Salário".
- **Gestão de Parcelamentos:** Cards interativos com progresso de quitação e gráficos de pizza.

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
Este projeto é de **uso estritamente pessoal e privado**. Veja o arquivo [LICENSE.md](LICENSE.md) para mais detalhes.

---
**Desenvolvido por [Leleco]** - 2026
