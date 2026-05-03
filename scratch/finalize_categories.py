import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from core.models import Categoria, Conta

def finalize_categories():
    cat_transporte = Categoria.objects.get(nome='Transporte')
    cat_saude = Categoria.objects.get(nome='Saúde')
    cat_alimentacao = Categoria.objects.get(nome='Alimentação')
    cat_mensais = Categoria.objects.get(nome='Contas Mensais')
    
    # Mapeamento final
    mapping = {
        cat_transporte: ['ipva', 'manutenção', 'seguro', 'gasolina', 'sandero'],
        cat_saude: ['pscologa', 'psicologa', 'dentista', 'médico'],
        cat_alimentacao: ['compra mensal', 'mercado', 'padaria'],
        cat_mensais: ['iptv', 'netflix', 'spotify']
    }
    
    updated_count = 0
    for category, keywords in mapping.items():
        for kw in keywords:
            contas = Conta.objects.filter(nome__icontains=kw)
            for conta in contas:
                conta.categoria = category
                conta.save()
                updated_count += 1
                print(f"Conta '{conta.nome}' finalizada em '{category.nome}'")

    # Verifica se restou algo
    sobras = Conta.objects.filter(categoria__nome='Legado')
    if not sobras.exists():
        print("\nSucesso: Categoria 'Legado' está vazia!")
    else:
        print("\nAinda restam alguns itens ignorados:")
        for s in sobras:
            print(f"- {s.nome}")

if __name__ == "__main__":
    finalize_categories()
