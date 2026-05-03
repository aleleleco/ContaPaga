from django.shortcuts import render, redirect, get_object_or_404, reverse
from .models import Competencia, Lancamento, Conta, Categoria, Parcelamento, AgentePagador
from django.utils import timezone
from datetime import date
from django.db.models import Sum, Min
from .services import importar_contas_fixas
from .forms import ContaForm, LancamentoForm, PagamentoForm, ParcelamentoModelForm, AgentePagadorForm
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
import sqlite3

def dashboard(request):
    now = timezone.now()
    comp_id = request.GET.get('comp_id')
    
    if comp_id:
        competencia = get_object_or_404(Competencia, id=comp_id)
    else:
        competencia, created = Competencia.objects.get_or_create(
            mes=now.month, 
            ano=now.year,
            defaults={'status': 'aberto'}
        )
    
    # Lista de todas as competências para o filtro
    todas_competencias = Competencia.objects.all().order_by('-ano', '-mes')
    
    if request.method == 'POST':
        if 'importar_fixas' in request.POST:
            importar_contas_fixas(competencia.id)
            return redirect(f"{reverse('core:dashboard')}?comp_id={competencia.id}")
        if 'fechar_mes' in request.POST:
            competencia.status = 'fechado'
            competencia.save()
            return redirect(f"{reverse('core:dashboard')}?comp_id={competencia.id}")
    
    lancamentos = Lancamento.objects.filter(competencia=competencia).order_by('vencimento')
    
    stats = {
        'total_a_pagar': lancamentos.filter(status='pendente').aggregate(Sum('valor_previsto'))['valor_previsto__sum'] or 0,
        'total_pago': lancamentos.filter(status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0,
        'total_descontos': lancamentos.aggregate(Sum('desconto'))['desconto__sum'] or 0,
    }
    
    context = {
        'competencia': competencia,
        'lancamentos': lancamentos,
        'stats': stats,
        'form_conta': ContaForm(),
        'form_lancamento': LancamentoForm(initial={'vencimento': timezone.now().date()}),
        'todas_competencias': todas_competencias,
        'agentes_pagadores': AgentePagador.objects.all().order_by('nome'),
    }
    return render(request, 'core/dashboard.html', context)

def conta_create(request):
    if request.method == 'POST':
        form = ContaForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))

def conta_edit(request, pk):
    conta = get_object_or_404(Conta, pk=pk)
    if request.method == 'POST':
        form = ContaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
    return redirect('core:configuracoes')

def conta_delete(request, pk):
    conta = get_object_or_404(Conta, pk=pk)
    # Proteção: só deleta se não tiver lançamentos
    if not Lancamento.objects.filter(conta=conta).exists():
        conta.delete()
    return redirect('core:configuracoes')

def lancamento_create(request):
    if request.method == 'POST':
        form = LancamentoForm(request.POST)
        if form.is_valid():
            lancamento = form.save(commit=False)
            
            # Lógica para nova conta on-the-fly
            conta = form.cleaned_data.get('conta')
            novo_nome = form.cleaned_data.get('novo_nome_conta')
            nova_cat = form.cleaned_data.get('nova_categoria')
            
            if not conta and novo_nome:
                # Tenta buscar uma conta existente com o mesmo nome para evitar duplicatas
                conta = Conta.objects.filter(nome__iexact=novo_nome).first()
                
                if not conta:
                    if not nova_cat:
                        nova_cat, _ = Categoria.objects.get_or_create(nome='Outros')
                    
                    conta = Conta.objects.create(
                        nome=novo_nome,
                        categoria=nova_cat,
                        tipo='esporadica',
                        valor_padrao=lancamento.valor_previsto
                    )
            
            if conta:
                lancamento.conta = conta
                now = lancamento.vencimento
                comp, _ = Competencia.objects.get_or_create(mes=now.month, ano=now.year)
                lancamento.competencia = comp
                lancamento.save()
                return redirect(f"{reverse('core:dashboard')}?comp_id={comp.id}")
            
    return redirect('core:dashboard')

def pagamento_registrar(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        form = PagamentoForm(request.POST, request.FILES, instance=lancamento)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.status = 'pago'
            if not pagamento.data_pagamento:
                pagamento.data_pagamento = timezone.now().date()
            pagamento.save()
            
            # Atualiza o status do parcelamento se houver um vinculado
            if pagamento.parcelamento:
                p = pagamento.parcelamento
                pagos = Lancamento.objects.filter(parcelamento=p, status='pago').count()
                p.parcelas_pagas = pagos
                if pagos >= p.total_parcelas:
                    p.status = 'finalizado'
                p.save()
            
            return redirect(f"{reverse('core:dashboard')}?comp_id={lancamento.competencia.id}")
                
    return redirect('core:dashboard')

def relatorios(request):
    now = timezone.now()
    comp_id = request.GET.get('comp_id')
    conta_id = request.GET.get('conta_id')
    
    if comp_id:
        comp_atual = get_object_or_404(Competencia, id=comp_id)
    else:
        comp_atual, _ = Competencia.objects.get_or_create(mes=now.month, ano=now.year)
    
    prev_month_dt = date(comp_atual.ano, comp_atual.mes, 1) - relativedelta(months=1)
    comp_anterior = Competencia.objects.filter(mes=prev_month_dt.month, ano=prev_month_dt.year).first()
    
    todas_competencias = Competencia.objects.all().order_by('-ano', '-mes')
    todas_contas = Conta.objects.values('nome').annotate(id=Min('id')).order_by('nome')
    
    # 1. Gastos por Categoria (Gráfico Rosca)
    gastos_por_categoria = Lancamento.objects.filter(
        competencia=comp_atual
    ).values('conta__categoria__nome').annotate(total=Sum('valor_previsto'))
    
    labels_categorias = [item['conta__categoria__nome'] for item in gastos_por_categoria]
    valores_categorias = [float(item['total']) for item in gastos_por_categoria]
    
    total_atual = Lancamento.objects.filter(competencia=comp_atual, status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
    total_anterior = 0
    diff_valor = 0
    if comp_anterior:
        total_anterior = Lancamento.objects.filter(competencia=comp_anterior, status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
        diff_valor = abs(total_atual - total_anterior)
    
    # 2. Comparativo de Contas Fixas (Tabela + Gráfico Barras)
    # Agrupa por nome para evitar duplicatas na visualização
    nomes_fixas = Conta.objects.filter(tipo='fixa').values_list('nome', flat=True).distinct()
    comparativo_fixas = []
    labels_fixas = []
    valores_fixas_atual = []
    valores_fixas_ant = []
    
    for nome in nomes_fixas:
        # Busca todos os IDs de contas com este nome
        ids_conta = Conta.objects.filter(nome=nome).values_list('id', flat=True)
        
        v_atual = Lancamento.objects.filter(competencia=comp_atual, conta_id__in=ids_conta).aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
        v_anterior = 0
        if comp_anterior:
            v_anterior = Lancamento.objects.filter(competencia=comp_anterior, conta_id__in=ids_conta).aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
        
        comparativo_fixas.append({
            'nome': nome,
            'atual': v_atual,
            'anterior': v_anterior,
            'diff': v_atual - v_anterior
        })
        labels_fixas.append(nome)
        valores_fixas_atual.append(float(v_atual))
        valores_fixas_ant.append(float(v_anterior))

    # 3. Histórico de Conta Específica
    conta_selecionada = None
    historico_conta = []
    labels_historico = []
    valores_historico = []
    
    if conta_id:
        conta_selecionada = get_object_or_404(Conta, id=conta_id)
        # Pega os IDs de todas as contas que compartilham o mesmo nome para unificar o histórico
        ids_mesmo_nome = Conta.objects.filter(nome=conta_selecionada.nome).values_list('id', flat=True)
        
        # Agrupa lançamentos por competência para não duplicar pontos no gráfico se houver lançamentos em contas diferentes no mesmo mês
        historico_objs = Lancamento.objects.filter(
            conta_id__in=ids_mesmo_nome
        ).values(
            'competencia__ano', 'competencia__mes'
        ).annotate(
            total_pago=Sum('valor_pago'),
            total_previsto=Sum('valor_previsto')
        ).order_by('-competencia__ano', '-competencia__mes')[:6]

        # Reverte para ordem cronológica
        for h in reversed(historico_objs):
            # Cria um objeto fictício para o template manter compatibilidade ou passa os dados brutos
            mes_display = f"{h['competencia__mes']:02d}/{h['competencia__ano']}"
            historico_conta.append({
                'competencia': mes_display,
                'valor_pago': h['total_pago'],
                'valor_previsto': h['total_previsto']
            })
            labels_historico.append(mes_display)
            valores_historico.append(float(h['total_pago'] or h['total_previsto']))

    # 4. Previsão de Gastos (Próximos 3 meses)
    previsoes = []
    for i in range(1, 4):
        data_futura = date(comp_atual.ano, comp_atual.mes, 1) + relativedelta(months=i)
        total_fixas = Conta.objects.filter(tipo='fixa').aggregate(Sum('valor_padrao'))['valor_padrao__sum'] or 0
        total_parcelas = 0
        parcelamentos = Parcelamento.objects.filter(status='ativo')
        for p in parcelamentos:
            m_diff = (data_futura.year - p.data_inicio.year) * 12 + (data_futura.month - p.data_inicio.month)
            p_n = m_diff + 1
            if 1 <= p_n <= p.total_parcelas:
                total_parcelas += p.valor_parcela
        
        previsoes.append({
            'mes': data_futura.strftime('%m/%Y'),
            'total': total_fixas + total_parcelas,
            'fixas': total_fixas,
            'parcelas': total_parcelas
        })

    # 5. Gastos por Agente Pagador (Nova Funcionalidade)
    agentes_stats = []
    for agente in AgentePagador.objects.all():
        gasto_agente = Lancamento.objects.filter(competencia=comp_atual, agente_pagador=agente).aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
        saldo = agente.salario - gasto_agente
        agentes_stats.append({
            'nome': agente.nome,
            'salario': agente.salario,
            'gasto': gasto_agente,
            'saldo': saldo,
            'perc': (float(gasto_agente) / float(agente.salario) * 100) if agente.salario > 0 else 0
        })

    context = {
        'labels_categorias': labels_categorias,
        'valores_categorias': valores_categorias,
        'total_atual': total_atual,
        'total_anterior': total_anterior,
        'diff_valor': diff_valor,
        'comparativo_fixas': comparativo_fixas,
        'labels_fixas': labels_fixas,
        'valores_fixas_atual': valores_fixas_atual,
        'valores_fixas_ant': valores_fixas_ant,
        'previsoes': previsoes,
        'todas_competencias': todas_competencias,
        'todas_contas': todas_contas,
        'conta_selecionada': conta_selecionada,
        'historico_conta': historico_conta,
        'labels_historico': labels_historico,
        'valores_historico': valores_historico,
        'comp_atual': comp_atual,
        'comp_anterior': comp_anterior,
        'agentes_stats': agentes_stats,
    }
    return render(request, 'core/relatorios.html', context)

def parcelamentos_list(request):
    parcelamentos = Parcelamento.objects.all().order_by('-status', 'data_inicio')
    
    if request.method == 'POST':
        form = ParcelamentoModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:parcelamentos_list')
    else:
        form = ParcelamentoModelForm()
        
    context = {
        'parcelamentos': parcelamentos,
        'form': form,
    }
    return render(request, 'core/parcelamentos.html', context)

def parcelamento_edit(request, pk):
    parcelamento = get_object_or_404(Parcelamento, pk=pk)
    if request.method == 'POST':
        form = ParcelamentoModelForm(request.POST, instance=parcelamento)
        if form.is_valid():
            form.save()
            return redirect('core:parcelamentos_list')
    return redirect('core:parcelamentos_list')

def parcelamento_delete(request, pk):
    parcelamento = get_object_or_404(Parcelamento, pk=pk)
    parcelamento.delete()
    return redirect('core:parcelamentos_list')

def parcelamento_detalhe(request, pk):
    parcelamento = get_object_or_404(Parcelamento, pk=pk)
    # Busca todos os lançamentos vinculados a este parcelamento
    lancamentos = Lancamento.objects.filter(parcelamento=parcelamento).order_by('parcela_atual')
    
    # Cálculos para o dashboard do parcelamento
    pago = lancamentos.filter(status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
    pendente = lancamentos.filter(status='pendente').aggregate(Sum('valor_previsto'))['valor_previsto__sum'] or 0
    total_efetivo = pago + pendente
    
    desconto_total = lancamentos.aggregate(Sum('desconto'))['desconto__sum'] or 0
    juros_total = lancamentos.aggregate(Sum('juros'))['juros__sum'] or 0
    
    context = {
        'parcelamento': parcelamento,
        'lancamentos': lancamentos,
        'stats': {
            'pago': pago,
            'pendente': pendente,
            'total_efetivo': total_efetivo,
            'desconto_total': desconto_total,
            'juros_total': juros_total,
            'progresso_perc': (parcelamento.parcelas_pagas / parcelamento.total_parcelas * 100) if parcelamento.total_parcelas else 0
        }
    }
    return render(request, 'core/parcelamento_detalhe.html', context)

def configuracoes(request):
    categorias = Categoria.objects.all().order_by('nome')
    contas = Conta.objects.all().order_by('tipo', 'nome')
    agentes = AgentePagador.objects.all().order_by('nome')
    
    # Adiciona contagem de usos para segurança na exclusão
    for cat in categorias:
        cat.usos = Conta.objects.filter(categoria=cat).count() + Parcelamento.objects.filter(categoria=cat).count()
    
    for conta in contas:
        conta.usos = Lancamento.objects.filter(conta=conta).count()
        
    for agente in agentes:
        agente.usos = Lancamento.objects.filter(agente_pagador=agente).count()

    context = {
        'categorias': categorias,
        'contas': contas,
        'agentes': agentes,
        'form_conta': ContaForm(),
        'form_agente': AgentePagadorForm(),
    }
    return render(request, 'core/configuracoes.html', context)

def agente_create(request):
    if request.method == 'POST':
        form = AgentePagadorForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('core:configuracoes')

def agente_edit(request, pk):
    agente = get_object_or_404(AgentePagador, pk=pk)
    if request.method == 'POST':
        form = AgentePagadorForm(request.POST, instance=agente)
        if form.is_valid():
            form.save()
    return redirect('core:configuracoes')

def agente_delete(request, pk):
    agente = get_object_or_404(AgentePagador, pk=pk)
    if not Lancamento.objects.filter(agente_pagador=agente).exists():
        agente.delete()
    return redirect('core:configuracoes')

def categoria_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Categoria.objects.get_or_create(nome=nome)
    return redirect('core:configuracoes')

def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    # Proteção: só deleta se não tiver nada vinculado
    if not Conta.objects.filter(categoria=categoria).exists() and not Parcelamento.objects.filter(categoria=categoria).exists():
        categoria.delete()
    return redirect('core:configuracoes')

def competencias_list(request):
    competencias = Competencia.objects.all().order_by('-ano', '-mes')
    
    # Adiciona totais para cada competência para exibir na lista
    for comp in competencias:
        comp.total_previsto = Lancamento.objects.filter(competencia=comp).aggregate(Sum('valor_previsto'))['valor_previsto__sum'] or 0
        comp.total_pago = Lancamento.objects.filter(competencia=comp, status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
        
    context = {
        'competencias': competencias,
    }
    return render(request, 'core/competencias.html', context)

def competencia_reabrir(request, pk):
    competencia = get_object_or_404(Competencia, pk=pk)
    competencia.status = 'aberto'
    competencia.save()
    return redirect('core:competencias_list')

def exportar_pdf(request, pk):
    competencia = get_object_or_404(Competencia, pk=pk)
    lancamentos = Lancamento.objects.filter(competencia=competencia).order_by('vencimento')
    
    total_previsto = lancamentos.aggregate(Sum('valor_previsto'))['valor_previsto__sum'] or 0
    total_pago = lancamentos.filter(status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0
    total_descontos = lancamentos.aggregate(Sum('desconto'))['desconto__sum'] or 0
    
    template_path = 'core/pdf_report.html'
    context = {
        'competencia': competencia,
        'lancamentos': lancamentos,
        'total_previsto': total_previsto,
        'total_pago': total_pago,
        'total_descontos': total_descontos,
        'data_emissao': timezone.now(),
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Relatorio_{competencia.mes}_{competencia.ano}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('Erro ao gerar PDF', status=500)
    return response

def legacy_hub(request):
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    
    # Busca IDs já migrados para marcar na interface
    contas_migradas_ids = list(Conta.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))
    lancamentos_migrados_ids = list(Lancamento.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))
    parcelamentos_migrados_ids = list(Parcelamento.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))

    # Busca contas que ainda não foram migradas
    cursor.execute("SELECT id, nome, data_vencimento, mensal, observacoes FROM gestor_contas_conta")
    contas_legado = []
    for row in cursor.fetchall():
        contas_legado.append({
            'id': row[0], 'nome': row[1], 'dia': row[2], 'mensal': row[3], 'obs': row[4],
            'migrada': row[0] in contas_migradas_ids
        })
            
    # Busca lançamentos agrupados por competência
    cursor.execute("""
        SELECT cp.id, cp.data_pagamento, cp.valor_pago, c.nome, comp.mes, comp.ano, cp.comprovante, comp.id as comp_id
        FROM gestor_contas_contapaga cp
        JOIN gestor_contas_conta c ON cp.conta_id = c.id
        JOIN gestor_contas_competencia comp ON cp.competencia_id = comp.id
        ORDER BY comp.ano DESC, comp.mes DESC
    """)
    
    competencias_dict = {}
    for row in cursor.fetchall():
        key = f"{row[4]}/{row[5]}" # MM/YYYY
        if key not in competencias_dict:
            competencias_dict[key] = {
                'id': row[7],
                'mes': row[4],
                'ano': row[5],
                'label': key,
                'lancamentos': []
            }
        competencias_dict[key]['lancamentos'].append({
            'id': row[0], 'data': row[1], 'valor': row[2], 'conta': row[3], 
            'mes': row[4], 'ano': row[5], 'comprovante': row[6],
            'migrado': row[0] in lancamentos_migrados_ids
        })

    # Busca parcelamentos legados
    cursor.execute("""
        SELECT id, nome, qtd_parcelas, valor_total 
        FROM gestor_contas_conta 
        WHERE parcelas = 1
    """)
    parcelamentos_legado = []
    for row in cursor.fetchall():
        # Busca quantas parcelas já foram pagas no legado
        cursor.execute("SELECT COUNT(*) FROM gestor_contas_contapaga WHERE conta_id = ?", (row[0],))
        pagos = cursor.fetchone()[0]
        
        # Valor da parcela estimado
        valor_parc = row[3] / row[2] if row[2] and row[3] else 0
        
        parcelamentos_legado.append({
            'id': row[0], 'nome': row[1], 'total': row[2], 'pagas': pagos, 
            'valor_total': row[3], 'valor_parcela': valor_parc,
            'migrado': row[0] in parcelamentos_migrados_ids
        })

    conn.close()
    
    context = {
        'contas_legado': contas_legado,
        'competencias_legado': competencias_dict.values(),
        'parcelamentos_legado': parcelamentos_legado,
    }
    return render(request, 'core/legacy_hub.html', context)

def legacy_migrate_competencia(request, legacy_comp_id):
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cp.id
        FROM gestor_contas_contapaga cp
        WHERE cp.competencia_id=?
    """, (legacy_comp_id,))
    lancamentos_ids = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    for l_id in lancamentos_ids:
        # Reutiliza a lógica individual para garantir consistência
        legacy_migrate_lancamento(request, l_id)
        
    return redirect('core:legacy_hub')

def legacy_migrate_conta(request, legacy_id):
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, data_vencimento, mensal, observacoes FROM gestor_contas_conta WHERE id=?", (legacy_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        cat_legado, _ = Categoria.objects.get_or_create(nome='Legado')
        # Tenta recuperar ou criar para evitar erros se o usuário clicar duas vezes
        Conta.objects.get_or_create(
            legacy_id=legacy_id,
            defaults={
                'nome': row[0],
                'categoria': cat_legado,
                'dia_vencimento': row[1] or 1,
                'tipo': 'fixa' if row[2] else 'esporadica',
                'observacoes': row[3]
            }
        )
    return redirect('core:legacy_hub')

def legacy_migrate_lancamento(request, legacy_id):
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cp.valor_pago, cp.data_pagamento, c.nome, comp.mes, comp.ano, cp.comprovante
        FROM gestor_contas_contapaga cp
        JOIN gestor_contas_conta c ON cp.conta_id = c.id
        JOIN gestor_contas_competencia comp ON cp.competencia_id = comp.id
        WHERE cp.id=?
    """, (legacy_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        valor, data_pag, conta_nome, mes, ano, comprovante = row
        cat_legado, _ = Categoria.objects.get_or_create(nome='Legado')
        # Busca a conta de forma mais segura (tentando legacy_id primeiro, depois nome)
        conta = Conta.objects.filter(nome=conta_nome).first()
        if not conta:
            conta = Conta.objects.create(nome=conta_nome, categoria=cat_legado)
        
        competencia, _ = Competencia.objects.get_or_create(mes=int(mes), ano=int(ano))
        
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
    return redirect('core:legacy_hub')

def legacy_migrate_parcelamento(request, legacy_id):
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    conn = sqlite3.connect(legado_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, qtd_parcelas, valor_total, data_cadastro, observacoes
        FROM gestor_contas_conta 
        WHERE id=?
    """, (legacy_id,))
    row = cursor.fetchone()
    
    # Busca quantas parcelas já foram pagas no legado
    cursor.execute("SELECT COUNT(*) FROM gestor_contas_contapaga WHERE conta_id = ?", (legacy_id,))
    pagos = cursor.fetchone()[0]
    conn.close()
    
    if row:
        nome, total_parc, valor_total, data_cad, obs = row
        cat_legado, _ = Categoria.objects.get_or_create(nome='Legado')
        
        # Calcula valor da parcela
        valor_parc = valor_total / total_parc if total_parc and valor_total else 0
        
        # Cria o contrato de parcelamento
        p, created = Parcelamento.objects.get_or_create(
            legacy_id=legacy_id,
            defaults={
                'nome': nome,
                'categoria': cat_legado,
                'valor_total': valor_total,
                'valor_parcela': valor_parc,
                'total_parcelas': total_parc,
                'parcelas_pagas': pagos,
                'data_inicio': data_cad[:10] if data_cad else timezone.now().date(),
                'status': 'ativo' if pagos < total_parc else 'finalizado',
                'observacao': obs
            }
        )
        
        # Importante: O usuário agora pode migrar os lançamentos individuais deste parcelamento
        # na seção de lançamentos do Hub para preencher o histórico.
        
    return redirect('core:legacy_hub')
