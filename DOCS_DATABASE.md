# 🗄️ Estrutura de Dados - ContaPaga

Este documento descreve a modelagem de dados do sistema, focando nas relações entre Agentes, Contas Bancárias e o Módulo de Conciliação.

---

## 👥 Agentes e Bancos

### `AgentePagador`
Representa uma pessoa ou entidade que realiza pagamentos e recebe rendimentos no sistema.
- `nome`: Nome identificador.
- `salario`: Valor base de rendimento (opcional).
- `info_bancaria`: Observações gerais.

### `ContaBancaria`
Um agente pode possuir múltiplas contas em diferentes instituições.
- `agente`: Relacionamento 1:N com AgentePagador.
- `banco`: Nome da instituição (ex: Bradesco, Nubank).
- `agencia` / `conta`: Dados identificadores.
- `tipo`: Corrente, Poupança, Investimento ou Outros.
- `considerar_como_salario`: Flag crítico. Se ativo, qualquer entrada financeira identificada via OFX nesta conta será somada ao rendimento mensal do agente no Dashboard.

### `ChavePix`
Vínculo de chaves de recebimento para as contas.
- `conta_bancaria`: Relacionamento 1:N com ContaBancaria.
- `tipo`: CPF, CNPJ, E-mail, Telefone ou Aleatória.
- `chave`: Valor da chave.

---

## 🏦 Módulo Bancário (OFX)

### `OfxArquivo`
Registro do upload físico dos arquivos de extrato.
- `arquivo`: Caminho do arquivo .ofx em `media/ofx/`.
- `agente`: Agente vinculado no momento da importação.
- `conta_bancaria`: Conta específica vinculada.
- `banco_nome`: Identificado automaticamente pelo parser ou via conta.

### `OfxTransacao` (Central de Conciliação)
Registros persistidos das transações para processamento assíncrono.
- `arquivo`: Vínculo com o upload de origem.
- `fitid`: ID único universal da transação bancária (Garante que a mesma conta não seja importada duas vezes).
- `status`: 
    - `lido`: Recém importado (Aba Pendentes).
    - `validado`: Pronto para gerar lançamento (Aba Validados).
    - `processado`: Já gerou um lançamento financeiro.
    - `ignorado`: Desconsiderado pelo usuário.
    - `transferencia`: Identificado automaticamente como movimentação entre contas do sistema.
- `conta_sugerida`: Sugestão automática baseada em histórico ou regras.
- `categoria_manual`: Categoria sugerida via `RegraImportacao`.

### `RegraImportacao`
Automação de categorias baseada em termos no extrato.
- `padrao`: Termo de busca (ex: "UBER", "IFOOD").
- `categoria`: Categoria a ser sugerida automaticamente.

---

## 📊 Categorias e Lançamentos

### `Categoria`
- `tipo`: entrada (Receita) ou saida (Gasto).
- `is_salary`: Flag que identifica se a categoria representa o salário principal.

### `Lancamento`
- `agente_pagador`: Vínculo com quem pagou/recebeu.
- `transacao_id`: Armazena o `fitid` do banco para rastreabilidade e evitar duplicidade na competência.
