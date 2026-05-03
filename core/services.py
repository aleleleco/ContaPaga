from .models import Competencia, Conta, Lancamento, Parcelamento
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.db import transaction
from datetime import date
import calendar

def get_or_create_competencia(mes, ano):
    competencia, created = Competencia.objects.get_or_create(mes=mes, ano=ano)
    return competencia

@transaction.atomic
def importar_contas_fixas(competencia_id):
    competencia = Competencia.objects.get(id=competencia_id)
    contas_fixas = Conta.objects.filter(tipo='fixa')
    
    importados = 0
    # 1. Contas Fixas
    for conta in contas_fixas:
        if not Lancamento.objects.filter(competencia=competencia, conta=conta).exists():
            try:
                dia = min(conta.dia_vencimento, calendar.monthrange(competencia.ano, competencia.mes)[1])
                dt_vencimento = date(competencia.ano, competencia.mes, dia)
            except Exception:
                dt_vencimento = date(competencia.ano, competencia.mes, 1)

            Lancamento.objects.create(
                competencia=competencia,
                conta=conta,
                valor_previsto=conta.valor_padrao,
                vencimento=dt_vencimento,
                status='pendente'
            )
            importados += 1
            
    # 2. Parcelamentos Ativos
    parcelamentos = Parcelamento.objects.filter(status='ativo')
    for p in parcelamentos:
        # Verifica se já existe lançamento para este contrato nesta competência
        if not Lancamento.objects.filter(competencia=competencia, parcelamento=p).exists():
            # Cálculo da parcela atual
            meses_diff = (competencia.ano - p.data_inicio.year) * 12 + (competencia.mes - p.data_inicio.month)
            parcela_n = meses_diff + 1
            
            # Só importa se a competência estiver dentro do intervalo do parcelamento
            if 1 <= parcela_n <= p.total_parcelas:
                # Garante que existe uma "Conta" para este parcelamento
                # Busca a conta de forma mais segura (tentando pelo nome, mas lidando com duplicatas)
                conta_obj = Conta.objects.filter(nome__iexact=p.nome).first()
                if not conta_obj:
                    conta_obj = Conta.objects.create(
                        nome=p.nome, 
                        categoria=p.categoria, 
                        tipo='esporadica'
                    )
                
                try:
                    dia = min(p.data_inicio.day, calendar.monthrange(competencia.ano, competencia.mes)[1])
                    dt_vencimento = date(competencia.ano, competencia.mes, dia)
                except Exception:
                    dt_vencimento = date(competencia.ano, competencia.mes, 1)

                Lancamento.objects.create(
                    competencia=competencia,
                    conta=conta_obj,
                    parcelamento=p,
                    valor_previsto=p.valor_parcela,
                    vencimento=dt_vencimento,
                    parcela_atual=parcela_n,
                    total_parcelas=p.total_parcelas,
                    status='pendente'
                )
                importados += 1
                
    return importados

@transaction.atomic
def gerar_parcelas(conta_id, valor_total, num_parcelas, mes_inicial, ano_inicial):
    # (Mantido por compatibilidade, mas o sistema agora usa o modelo Parcelamento)
    conta = Conta.objects.get(id=conta_id)
    valor_parcela = (valor_total / num_parcelas).quantize(Decimal('0.01'))
    diferenca = valor_total - (valor_parcela * num_parcelas)
    
    data_cursor = date(ano_inicial, mes_inicial, min(conta.dia_vencimento, 28))
    
    lancamentos = []
    for i in range(1, num_parcelas + 1):
        comp = get_or_create_competencia(data_cursor.month, data_cursor.year)
        valor = valor_parcela + (diferenca if i == num_parcelas else 0)
            
        lancamento = Lancamento.objects.create(
            competencia=comp,
            conta=conta,
            valor_previsto=valor,
            vencimento=data_cursor,
            parcela_atual=i,
            total_parcelas=num_parcelas,
            status='pendente'
        )
        lancamentos.append(lancamento)
        data_cursor = data_cursor + relativedelta(months=1)
        
    return lancamentos
