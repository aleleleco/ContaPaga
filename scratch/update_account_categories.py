import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from core.models import Categoria, Conta

def update_categories():
    # 1. Garantir que as novas categorias existam
    cat_moradia, _ = Categoria.objects.get_or_create(nome='Moradia')
    cat_transporte, _ = Categoria.objects.get_or_create(nome='Transporte')
    cat_lazer, _ = Categoria.objects.get_or_create(nome='Lazer')
    cat_mensais, _ = Categoria.objects.get_or_create(nome='Contas Mensais')
    cat_cartao, _ = Categoria.objects.get_or_create(nome='Cartao Credito')
    
    # 2. Mapeamento de nomes
    mapping = {
        cat_transporte: ['gastos harley', 'harley - emprestimo', 'hb20'],
        cat_mensais: ['celular', 'internet', 'vivo', 'net'],
        cat_cartao: ['cartão nu bank', 'nubank', 'cartão'],
        cat_moradia: ['energia', 'gaz', 'condominio', 'iptu 2026', 'iptu', 'luz', 'água'],
        cat_lazer: ['viagem', 'restaurante', 'cinema']
    }
    
    updated_count = 0
    for category, keywords in mapping.items():
        for kw in keywords:
            # Busca insensível a maiúsculas/minúsculas e parcial
            contas = Conta.objects.filter(nome__icontains=kw)
            for conta in contas:
                conta.categoria = category
                conta.save()
                updated_count += 1
                print(f"Conta '{conta.nome}' movida para '{category.nome}'")

    # 3. Verificar o que sobrou no Legado ou sem categoria
    sobras = Conta.objects.filter(categoria__nome='Legado')
    
    print(f"\nTotal de contas atualizadas: {updated_count}")
    
    if sobras.exists():
        print("\nContas que ainda permanecem em 'Legado':")
        for s in sobras:
            print(f"- {s.nome}")
    else:
        print("\nNenhuma conta pendente na categoria 'Legado'!")

if __name__ == "__main__":
    update_categories()
