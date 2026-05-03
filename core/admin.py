from django.contrib import admin
from .models import Competencia, Categoria, Conta, Lancamento

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('mes', 'ano', 'status')
    list_filter = ('ano', 'status')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'tipo', 'valor_padrao', 'dia_vencimento')
    list_filter = ('tipo', 'categoria')

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('conta', 'competencia', 'valor_previsto', 'vencimento', 'status')
    list_filter = ('status', 'competencia')
    search_fields = ('conta__nome',)
