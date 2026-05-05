from django.contrib import admin
from .models import (
    Competencia, Categoria, Conta, Lancamento, AgentePagador, 
    ContaBancaria, ChavePix, RegraImportacao, OfxArquivo, OfxTransacao
)

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('mes', 'ano', 'status')
    list_filter = ('ano', 'status')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)

@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'tipo', 'valor_padrao', 'dia_vencimento')
    list_filter = ('tipo', 'categoria')

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('conta', 'competencia', 'valor_previsto', 'vencimento', 'status')
    list_filter = ('status', 'competencia')
    search_fields = ('conta__nome',)

@admin.register(AgentePagador)
class AgentePagadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'salario')

class ChavePixInline(admin.TabularInline):
    model = ChavePix
    extra = 1

@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ('banco', 'conta', 'agente', 'tipo', 'considerar_como_salario')
    list_filter = ('tipo', 'considerar_como_salario', 'agente')
    inlines = [ChavePixInline]

@admin.register(RegraImportacao)
class RegraImportacaoAdmin(admin.ModelAdmin):
    list_display = ('padrao', 'conta', 'nome_exibicao')

@admin.register(OfxArquivo)
class OfxArquivoAdmin(admin.ModelAdmin):
    list_display = ('banco_nome', 'agente', 'data_upload')

@admin.register(OfxTransacao)
class OfxTransacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'descricao', 'valor', 'status')
    list_filter = ('status', 'data')
