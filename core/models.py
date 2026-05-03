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
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

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

class Parcelamento(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    )
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    total_parcelas = models.PositiveSmallIntegerField()
    parcelas_pagas = models.PositiveSmallIntegerField(default=0)
    data_inicio = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ativo')
    observacao = models.TextField(blank=True, null=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.nome} ({self.parcelas_pagas}/{self.total_parcelas})"

class AgentePagador(models.Model):
    nome = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    info_bancaria = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

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

    def __str__(self):
        label = f"{self.conta.nome} - {self.competencia}"
        if self.parcela_atual:
            label += f" ({self.parcela_atual}/{self.total_parcelas})"
        return label
