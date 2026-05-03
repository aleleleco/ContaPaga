from core.models import Conta, Lancamento
from django.db import transaction
from django.db.models import Count

def merge_duplicate_accounts():
    # Encontra nomes duplicados
    dups = Conta.objects.values('nome').annotate(count=Count('id')).filter(count__gt=1)
    
    for item in dups:
        nome = item['nome']
        contas = list(Conta.objects.filter(nome=nome).order_by('-tipo', 'legacy_id', 'id'))
        
        # O primeiro da lista (ordenado por tipo 'fixa' primeiro, depois legacy_id) será o principal
        principal = contas[0]
        secundarios = contas[1:]
        
        print(f"Mesclando conta '{nome}': Principal ID {principal.id}, Duplicatas: {[c.id for c in secundarios]}")
        
        with transaction.atomic():
            for sec in secundarios:
                # Move todos os lançamentos
                lancamentos = Lancamento.objects.filter(conta=sec)
                count = lancamentos.update(conta=principal)
                print(f"  - Movidos {count} lançamentos do ID {sec.id} para {principal.id}")
                
                # Deleta a conta secundária
                sec.delete()
                print(f"  - Conta ID {sec.id} removida.")

if __name__ == "__main__":
    merge_duplicate_accounts()
