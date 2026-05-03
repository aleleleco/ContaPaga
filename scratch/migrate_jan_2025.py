import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from core.models import Lancamento, Conta, Competencia, Categoria

def migrate_jan_2025():
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    
    # Busca lançamentos de Jan/2025
    cursor.execute("""
        SELECT cp.id, cp.valor_pago, cp.data_pagamento, c.nome, comp.mes, comp.ano, cp.comprovante, c.data_vencimento, c.mensal
        FROM gestor_contas_contapaga cp
        JOIN gestor_contas_conta c ON cp.conta_id = c.id
        JOIN gestor_contas_competencia comp ON cp.competencia_id = comp.id
        WHERE comp.mes = '01' AND comp.ano = 2025
    """)
    rows = cursor.fetchall()
    
    cat_legado, _ = Categoria.objects.get_or_create(nome='Legado')
    competencia, _ = Competencia.objects.get_or_create(mes=1, ano=2025)
    
    migrados = 0
    for row in rows:
        legacy_id, valor, data_pag, conta_nome, mes, ano, comprovante, dia_venc, mensal = row
        
        # Garante a conta
        conta, _ = Conta.objects.get_or_create(
            nome=conta_nome, 
            defaults={
                'categoria': cat_legado,
                'dia_vencimento': dia_venc or 1,
                'tipo': 'fixa' if mensal else 'esporadica'
            }
        )
        
        # Cria o lançamento com legacy_id
        Lancamento.objects.get_or_create(
            legacy_id=legacy_id,
            defaults={
                'competencia': competencia,
                'conta': conta,
                'valor_previsto': valor,
                'valor_pago': valor,
                'vencimento': data_pag,
                'data_pagamento': data_pag,
                'status': 'pago',
                'comprovante': comprovante
            }
        )
        migrados += 1
        
    conn.close()
    print(f"Migração concluída: {migrados} lançamentos importados para 01/2025.")

if __name__ == "__main__":
    migrate_jan_2025()
