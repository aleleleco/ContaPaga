from core.models import Conta, Lancamento
names = ['Cartão Nu Bank', 'Celular', 'Condominio', 'Energia', 'Gaz', 'Internet', 'harley - emprestimo']
for n in names:
    ids = list(Conta.objects.filter(nome=n).values_list('id', flat=True))
    for i in ids:
        count = Lancamento.objects.filter(conta_id=i).count()
        conta = Conta.objects.get(id=i)
        print(f"ID {i} ({conta.nome} - {conta.tipo}): {count} lancamentos")
