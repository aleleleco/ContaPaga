import sqlite3
import json

def analyze_installments(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Busca contas que são parcelamentos no legado
    cursor.execute("""
        SELECT id, nome, qtd_parcelas, valor_total 
        FROM gestor_contas_conta 
        WHERE parcelas = 1
    """)
    contas_parceladas = cursor.fetchall()
    
    report = []
    for c_id, nome, qtd, total in contas_parceladas:
        # Busca quantas parcelas já foram pagas (entradas na gestor_contas_contapaga)
        cursor.execute("""
            SELECT COUNT(*), SUM(valor_pago) 
            FROM gestor_contas_contapaga 
            WHERE conta_id = ?
        """, (c_id,))
        pagos, soma_pago = cursor.fetchone()
        
        # Busca detalhes na tabela de parcelamento
        cursor.execute("""
            SELECT MAX(parcelas_totais), MAX(valor_total), AVG(valor_pago)
            FROM gestor_contas_parcelamento
            WHERE conta_id_id = ?
        """, (c_id,))
        p_totais, p_total, p_valor_parc = cursor.fetchone()
        
        report.append({
            'legacy_conta_id': c_id,
            'nome': nome,
            'total_parcelas': p_totais or qtd,
            'parcelas_pagas': pagos,
            'valor_total': float(p_total or total or 0),
            'valor_parcela': float(p_valor_parc or 0)
        })
        
    conn.close()
    return report

if __name__ == "__main__":
    db_path = r'E:\Gestor_Contas\db.sqlite3'
    result = analyze_installments(db_path)
    print(json.dumps(result, indent=2))
