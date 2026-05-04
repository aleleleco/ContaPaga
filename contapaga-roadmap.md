# Roadmap ContaPaga - Sistema de Gerenciamento Financeiro Local

Sistema em Python/Django para controle de contas pagas, esporádicas e parceladas, com suporte a comprovantes e relatórios gráficos.

## 🎯 Critérios de Sucesso
- [x] Ambiente configurado com venv e Django.
- [x] Gestão de competências (Abrir/Fechar/Editar).
- [x] Importação de contas fixas para novas competências.
- [x] Lógica de parcelamento funcional (divisão proporcional com ajuste na última parcela).
- [x] Upload de comprovantes com organização por `ANO/MÊS`.
- [x] Dashboard com gráficos comparativos e visibilidade financeira.
- [x] Edição de valores (juros/descontos) no momento do pagamento.
- [x] Gestão independente de Contas Parceladas (CRUD e Automação).
- [x] Exportação de Relatórios Profissionais em PDF.

## 🛠️ Tech Stack
- **Backend:** Python + Django
- **Banco de Dados:** SQLite3
- **Frontend:** HTML5 + Vanilla CSS (Estilo Premium)
- **Gráficos:** Chart.js
- **PDF:** xhtml2pdf
- **Icons:** Lucide Icons (via CDN)

## 📂 Estrutura de Arquivos Final
```
contapaga/
├── .venv/
├── core/                  # App principal do sistema
│   ├── models.py          # Competencia, Conta, Parcelamento, Categoria, Lancamento
│   ├── views.py           # Logica das views e exportação PDF
│   ├── services.py        # Importação e automação de parcelas
│   ├── forms.py           # Formulários dinâmicos
│   └── templates/         # UI Dashboard, Parcelamentos, Relatórios, Competências
├── media/                 # Comprovantes organizados
├── setup/                 # Settings do Django
└── manage.py
```

## 📝 Histórico de Implementação

### ✅ Fase 1: Setup & Infraestrutura
- [x] **Tarefa 1.1:** Criar ambiente virtual.
- [x] **Tarefa 1.2:** Instalar Django e dependências (widget-tweaks, python-dateutil, xhtml2pdf).
- [x] **Tarefa 1.3:** Inicializar projeto Django e App `core`.

### ✅ Fase 2: Modelagem de Dados
- [x] **Tarefa 2.1:** Criar modelo `Competencia`.
- [x] **Tarefa 2.2:** Criar modelo `Conta` e `Categoria`.
- [x] **Tarefa 2.3:** Criar modelo `Lancamento`.
- [x] **Tarefa 2.4:** Criar modelo `Parcelamento`.

### ✅ Fase 3: Lógica de Negócio
- [x] **Tarefa 3.1:** Implementar importação de contas fixas.
- [x] **Tarefa 3.2:** Implementar automação de parcelas.
- [x] **Tarefa 3.3:** Organização dinâmica de media.

### ✅ Fase 4: UI/UX & Dashboard
- [x] **Tarefa 4.1:** Layout Base Premium.
- [x] **Tarefa 4.2:** Dashboard dinâmico com filtros de competência.
- [x] **Tarefa 4.3:** Cadastro de parcelamentos com cálculo automático via JS.
- [x] **Tarefa 4.4:** Gestão de competências (Abrir/Fechar/Reabrir).

### ✅ Fase 5: Relatórios & Gráficos
- [x] **Tarefa 5.1:** Gráficos de categoria e tendência.
- [x] **Tarefa 5.2:** Comparativo mensal automático.

### ✅ Fase 6: Refinamentos Finais (Concluída)
- [x] **Tarefa 6.1:** Edição de parcelamentos e lançamentos.
- [x] **Tarefa 6.2:** Bloqueio de segurança (Mês Fechado).
- [x] **Tarefa 6.3:** Exportação de PDF profissional para todas as competências.

---
### Fase 7: Novos recursos e implementações
- [x] **Salvamento dropbox** Lógica de salvamento integrada ao Dropbox local (C:\Users\PC-Leleco\Dropbox\Pessoal\ContasPagas)
- [x] **carga de legado** Carga de dados legados

### implementação futuras e melhorias
- [x] **Lista de contas parceladas**: Melhorar visualização com progresso gráfico.
- [x] **Histórico de contas parceladas**: Novo relatório com histórico de parcelas pagas e a pagar.
- [x] **Parâmetros do Sistema**: Nova tela para gerenciar categorias, contas e agentes sem o admin.
- [x] **Agentes Pagadores**: Controle de salário e gastos por pessoa.
- [x] **Importação OFX**: Módulo profissional de importação de extratos bancários com staging e reconciliação.

### ✅ Fase 8: Inteligência Bancária & Multicontas (Concluída)
- [x] **Multicontas por Agente**: Suporte a múltiplos bancos e contas por pagador.
- [x] **Gestão de Chaves PIX**: Cadastro e organização de chaves vinculadas às contas.
- [x] **Detecção de Transferências**: Algoritmo para identificar e ignorar movimentações entre contas (evita duplicidade).
- [x] **Salário Dinâmico**: Soma automática de receitas em contas marcadas como "Salário".
- [x] **Ações em Massa**: Bulk actions para categorias e contas na área de staging.
- [x] **Central de Conciliação Persistente**: Área de importação com abas de status (Pendentes, Validados, Processados, Ignorados).

### Fase 9: Automação Avançada & Insights (Próximos Passos)
- [ ] **Ajuste de Regras PIX**: Identificação inteligente de nomes em transações PIX para categorização automática.
- [ ] **Relatório por Agente**: Visão detalhada do saldo individual (Receitas - Despesas) por pessoa na competência.
- [ ] **Dashboard de Projeção**: Previsão de saldo final do mês baseado em contas pendentes e média de gastos.
- [ ] **Notificações de Vencimento**: Alertas visuais para contas próximas do vencimento não pagas.

## 🏁 Status Atual: **98% Operacional**
O sistema agora possui um hub completo de reconciliação bancária persistente. Próximo foco é inteligência preditiva e relatórios individuais por agente.
