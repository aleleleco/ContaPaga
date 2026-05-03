import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from core.models import Categoria

def create_categories():
    categorias = [
        'Moradia', 'Alimentação', 'Lazer', 'Transporte', 
        'Saúde', 'Educação', 'Outros', 'Legado'
    ]
    for cat_nome in categorias:
        obj, created = Categoria.objects.get_or_create(nome=cat_nome)
        if created:
            print(f"Categoria '{cat_nome}' criada.")
        else:
            print(f"Categoria '{cat_nome}' já existe.")

if __name__ == "__main__":
    create_categories()
