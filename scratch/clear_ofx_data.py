import os
import sys
import django

# Adiciona o diretório raiz ao path para encontrar o módulo 'setup'
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from core.models import OfxArquivo, OfxTransacao, Lancamento

def clear_data():
    print("Iniciando limpeza profunda de importações...")
    
    # 1. Identificar lançamentos que possuem vínculos com OFX
    lancs_afetados = Lancamento.objects.filter(ofx_transacoes__isnull=False).distinct()
    print(f"Lançamentos afetados encontrados: {lancs_afetados.count()}")
    
    for lanc in lancs_afetados:
        if lanc.conta.tipo == 'fixa':
            # Contas fixas voltamos ao estado original
            lanc.valor_pago = 0
            lanc.status = 'pendente'
            # Resetamos o previsto para o padrão da conta
            lanc.valor_previsto = lanc.conta.valor_padrao or 0
            lanc.data_pagamento = None
            lanc.save()
            print(f"  - Resetado lançamento fixo: {lanc.conta.nome}")
        else:
            # Contas variáveis/esporádicas deletamos (serão recriadas na importação)
            print(f"  - Deletando lançamento variável: {lanc.conta.nome}")
            lanc.delete()
            
    # 2. Deletar Arquivos e Transações (Cascade)
    arquivos = OfxArquivo.objects.all()
    count_arq = arquivos.count()
    arquivos.delete()
    print(f"Arquivos OFX deletados: {count_arq}")
    
    print("Limpeza concluída com sucesso. O sistema está pronto para novos testes.")

if __name__ == '__main__':
    clear_data()
