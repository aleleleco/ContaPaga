from django.db import models
from django.utils import timezone
import os

def upload_comprovante_path(instance, filename):
    # Organização: YYYY/MM-mes/filename
    ano = instance.competencia.ano
    mes_num = str(instance.competencia.mes).zfill(2)
    mes_nome = instance.competencia.get_mes_display().lower()
    return os.path.join(str(ano), f"{mes_num}-{mes_nome}", filename)

class Competencia(models.Model):
    STATUS_CHOICES = (
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
    )
    MESES_CHOICES = (
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
    )
    mes = models.PositiveSmallIntegerField(choices=MESES_CHOICES)
    ano = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aberto')

    class Meta:
        unique_together = ('mes', 'ano')
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"{self.get_mes_display()}/{self.ano}"

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada (Receita)'),
        ('saida', 'Saída (Gasto)'),
    ]
    nome = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='saida')
    is_salary = models.BooleanField(default=False, help_text="Marque se esta categoria representa recebimento de salário")

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

class Conta(models.Model):
    TIPO_CHOICES = (
        ('fixa', 'Fixa'),
        ('esporadica', 'Esporádica'),
    )
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='esporadica')
    valor_padrao = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    dia_vencimento = models.PositiveSmallIntegerField(default=1)
    observacoes = models.TextField(blank=True, null=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.nome

def upload_parcelamento_boleto_path(instance, filename):
    ext = filename.split('.')[-1]
    nome_slug = instance.nome.replace(' ', '_').lower()
    return os.path.join('parcelamentos', 'boletos', f"{nome_slug}_boleto.{ext}")

class Parcelamento(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    )
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    valor_entrada = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_parcela_final = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_parcelas = models.PositiveSmallIntegerField()
    parcelas_pagas = models.PositiveSmallIntegerField(default=0)
    data_inicio = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ativo')
    observacao = models.TextField(blank=True, null=True)
    boleto = models.FileField(upload_to=upload_parcelamento_boleto_path, null=True, blank=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    # Associação de outros gastos informativos
    lancamentos_extras = models.ManyToManyField('Lancamento', blank=True, related_name='parcelamentos_como_extra')
    
    # Vínculos específicos para Entrada e Parcela Final
    lancamento_entrada = models.ForeignKey('Lancamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='parcelamento_entrada')
    lancamento_parcela_final = models.ForeignKey('Lancamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='parcelamento_final')

    @property
    def total_pago_efetivo(self):
        # Soma das parcelas pagas (regulares)
        total_parcelas_pagas = float(self.parcelas_pagas) * float(self.valor_parcela)
        
        # Valor da Entrada: Prioriza o lançamento vinculado, senão usa o valor fixo
        v_entrada = float(self.lancamento_entrada.valor_pago or 0) if self.lancamento_entrada else float(self.valor_entrada)
        
        # Valor da Parcela Final: Prioriza o lançamento vinculado, senão usa o valor fixo
        v_final = float(self.lancamento_parcela_final.valor_pago or 0) if self.lancamento_parcela_final else float(self.valor_parcela_final)
        
        # Soma dos lançamentos extras vinculados
        total_extras = sum(float(l.valor_pago or 0) for l in self.lancamentos_extras.all())
        
        return v_entrada + total_parcelas_pagas + v_final + total_extras

    def __str__(self):
        return f"{self.nome} ({self.parcelas_pagas}/{self.total_parcelas})"

class AgentePagador(models.Model):
    nome = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    info_bancaria = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class ContaBancaria(models.Model):
    TIPO_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
        ('investimento', 'Conta Investimento'),
        ('outros', 'Outros'),
    ]
    agente = models.ForeignKey(AgentePagador, on_delete=models.CASCADE, related_name='contas_bancarias')
    banco = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='corrente')
    considerar_como_salario = models.BooleanField(default=False, help_text="Entradas nesta conta somam no salário do agente")
    
    def __str__(self):
        return f"{self.banco} - {self.conta} ({self.agente.nome})"

class ChavePix(models.Model):
    TIPO_CHOICES = [
        ('cpf', 'CPF'),
        ('cnpj', 'CNPJ'),
        ('email', 'E-mail'),
        ('telefone', 'Telefone'),
        ('aleatoria', 'Chave Aleatória'),
    ]
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.CASCADE, related_name='chaves_pix')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    chave = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.chave}"

class Lancamento(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
    )
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, related_name='lancamentos')
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='lancamentos')
    descricao = models.CharField(max_length=255, blank=True, null=True) # Para detalhes extras
    valor_previsto = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    juros = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    comprovante = models.FileField(upload_to=upload_comprovante_path, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    
    # Controle de Agente Pagador
    agente_pagador = models.ForeignKey(AgentePagador, on_delete=models.SET_NULL, null=True, blank=True, related_name='lancamentos')

    # Controle de Parcelamento no Lançamento
    parcelamento = models.ForeignKey(Parcelamento, on_delete=models.CASCADE, null=True, blank=True, related_name='lancamentos')
    parcela_atual = models.PositiveSmallIntegerField(null=True, blank=True)
    total_parcelas = models.PositiveSmallIntegerField(null=True, blank=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    
    # Identificador único do Banco (para evitar duplicatas no OFX)
    transacao_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        label = f"{self.conta.nome} - {self.competencia}"
        if self.parcela_atual:
            label += f" ({self.parcela_atual}/{self.total_parcelas})"
        return label

class RegraImportacao(models.Model):
    padrao = models.CharField(max_length=100, help_text="Termo contido no extrato (ex: UBER, IFOOD)")
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE)
    nome_exibicao = models.CharField(max_length=100, blank=True, help_text="Nome amigável para o lançamento (opcional)")

    def __str__(self):
        return f"{self.padrao} -> {self.conta.nome}"

    class Meta:
        verbose_name = "Regra de Importação"
        verbose_name_plural = "Regras de Importação"

class OfxArquivo(models.Model):
    arquivo = models.FileField(upload_to='ofx_imports/')
    data_upload = models.DateTimeField(auto_now_add=True)
    agente = models.ForeignKey(AgentePagador, on_delete=models.CASCADE)
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.CASCADE, null=True, blank=True)
    banco_nome = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.banco_nome} - {self.data_upload} ({self.agente.nome})"

class OfxTransacao(models.Model):
    STATUS_CHOICES = [
        ('lido', 'Lido'),
        ('validado', 'Validado'),
        ('processado', 'Processado'),
        ('ignorado', 'Ignorado'),
        ('transferencia', 'Transferência Interna'),
    ]
    arquivo = models.ForeignKey(OfxArquivo, on_delete=models.CASCADE, related_name='transacoes')
    fitid = models.CharField(max_length=255, unique=True) # ID único do banco
    data = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lido')
    
    # Vínculo temporário antes de processar
    conta_sugerida = models.ForeignKey(Conta, on_delete=models.SET_NULL, null=True, blank=True)
    vinculo_por_regra = models.BooleanField(default=False)
    lancamento_criado = models.ForeignKey(Lancamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='ofx_transacoes')

def upload_produto_doc_path(instance, filename):
    # Organização: produtos/YYYY/MM-mes/nome_produto_TIPO.ext
    ano = instance.data_aquisicao.year
    mes_num = str(instance.data_aquisicao.month).zfill(2)
    meses = [
        'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
    mes_nome = meses[instance.data_aquisicao.month - 1]
    
    ext = filename.split('.')[-1].lower()
    nome_slug = instance.nome.replace(' ', '_').lower()
    
    # Identifica o tipo de arquivo baseado na extensão ou contexto
    # Como a função é chamada pelo FileField, não sabemos o campo diretamente aqui de forma simples,
    # então vamos usar uma lógica baseada no nome original ou extensão para sugerir o sufixo.
    # Se for XML, geralmente é NFE. Se for PDF, pode ser DANFE ou Garantia.
    # NOTA: No formulário/view faremos o tratamento para garantir o sufixo correto se necessário.
    
    suffix = "documento"
    if ext == 'xml':
        suffix = "nfe"
    elif 'garantia' in filename.lower() or 'contrato' in filename.lower():
        suffix = "garantia"
    else:
        suffix = "DANFE"

    novo_nome = f"{nome_slug}_{suffix}.{ext}"
    return os.path.join('produtos', str(ano), f"{mes_num}-{mes_nome}", novo_nome)

class ProdutoGarantia(models.Model):
    GARANTIA_UNIDADE_CHOICES = [
        ('meses', 'Meses'),
        ('anos', 'Anos'),
    ]
    nome = models.CharField(max_length=255)
    data_aquisicao = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    tempo_garantia = models.PositiveIntegerField(help_text="Quantidade de meses ou anos")
    unidade_garantia = models.CharField(max_length=10, choices=GARANTIA_UNIDADE_CHOICES, default='meses')
    
    nota_fiscal = models.FileField(upload_to=upload_produto_doc_path, null=True, blank=True, help_text="XML da NF-e ou PDF do DANFE")
    contrato_garantia = models.FileField(upload_to=upload_produto_doc_path, null=True, blank=True, help_text="PDF do contrato de garantia")
    
    # Vínculos
    lancamento = models.ForeignKey('Lancamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    parcelamento = models.ForeignKey('Parcelamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    
    def __str__(self):
        return self.nome

    @property
    def data_fim_garantia(self):
        from dateutil.relativedelta import relativedelta
        if self.unidade_garantia == 'meses':
            return self.data_aquisicao + relativedelta(months=self.tempo_garantia)
        return self.data_aquisicao + relativedelta(years=self.tempo_garantia)

    @property
    def garantia_ativa(self):
        return timezone.now().date() <= self.data_fim_garantia

    class Meta:
        verbose_name = "Produto e Garantia"
        verbose_name_plural = "Produtos e Garantias"
        ordering = ['-data_aquisicao']
