from django import forms
from .models import Conta, Lancamento, Categoria, Parcelamento, AgentePagador, RegraImportacao

class RegraImportacaoForm(forms.ModelForm):
    class Meta:
        model = RegraImportacao
        fields = ['padrao', 'conta', 'nome_exibicao']
        widgets = {
            'padrao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: UBER, IFOOD'}),
            'conta': forms.Select(attrs={'class': 'form-control'}),
            'nome_exibicao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional: Nome Amigável'}),
        }

class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ['nome', 'categoria', 'tipo', 'valor_padrao', 'dia_vencimento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Aluguel'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
        }

class LancamentoForm(forms.ModelForm):
    novo_nome_conta = forms.CharField(
        max_length=200, 
        required=False, 
        label="Nome da Conta (Se não existir)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Manutenção Chuveiro'})
    )
    nova_categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoria (Para nova conta)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Lancamento
        fields = [
            'conta', 'novo_nome_conta', 'nova_categoria', 
            'valor_previsto', 'vencimento', 'descricao',
            'valor_pago', 'data_pagamento', 'comprovante'
        ]
        widgets = {
            'conta': forms.Select(attrs={'class': 'form-control'}),
            'valor_previsto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['conta'].required = False
        self.fields['conta'].label = "Selecionar Conta Existente"

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ['valor_pago', 'data_pagamento', 'juros', 'desconto', 'agente_pagador', 'comprovante']
        widgets = {
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'juros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'agente_pagador': forms.Select(attrs={'class': 'form-control'}),
            'comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }

from .models import AgentePagador

class AgentePagadorForm(forms.ModelForm):
    class Meta:
        model = AgentePagador
        fields = ['nome', 'salario', 'info_bancaria']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: João Silva'}),
            'salario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'info_bancaria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Chave PIX, Banco, etc.'}),
        }

class ParcelamentoModelForm(forms.ModelForm):
    class Meta:
        model = Parcelamento
        fields = ['nome', 'categoria', 'valor_total', 'valor_parcela', 'total_parcelas', 'data_inicio', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Notebook Gamer'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_parcela': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
