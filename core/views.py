from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from .models import (
    Competencia, Lancamento, Conta, Categoria, Parcelamento, 
    AgentePagador, RegraImportacao, OfxArquivo, OfxTransacao, 
    ContaBancaria, ChavePix
)
from django.utils import timezone
from datetime import date
from django.db.models import Sum, Min
from .services import importar_contas_fixas
from .forms import ContaForm, LancamentoForm, PagamentoForm, ParcelamentoModelForm, AgentePagadorForm, RegraImportacaoForm
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
import sqlite3
from ofxparse import OfxParser

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
    
    lancamentos = Lancamento.objects.filter(competencia=competencia).select_related('conta__categoria').order_by('vencimento')
    
    # Filtros por tipo de categoria
    saidas = lancamentos.filter(conta__categoria__tipo='saida')
    entradas = lancamentos.filter(conta__categoria__tipo='entrada')

    stats = {
        'total_a_pagar': saidas.filter(status='pendente').aggregate(Sum('valor_previsto'))['valor_previsto__sum'] or 0,
        'total_pago': saidas.filter(status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0,
        'total_descontos': saidas.aggregate(Sum('desconto'))['desconto__sum'] or 0,
        'total_salarios': entradas.filter(conta__categoria__is_salary=True, status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0,
        'outras_receitas': entradas.filter(conta__categoria__is_salary=False, status='pago').aggregate(Sum('valor_pago'))['valor_pago__sum'] or 0,
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
            
            return redirect(reverse('core:dashboard') + f'?comp_id={lancamento.competencia.id}')
    return render(request, 'core/pagamento_form.html', {'form': form, 'lancamento': lancamento})

def lancamento_edit(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        form = LancamentoForm(request.POST, instance=lancamento)
        if form.is_valid():
            form.save()
            return redirect(reverse('core:dashboard') + f'?comp_id={lancamento.competencia.id}')
    else:
        form = LancamentoForm(instance=lancamento)
    return render(request, 'core/lancamento_form.html', {'form': form, 'edit': True})

def lancamento_delete(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    comp_id = lancamento.competencia.id
    if request.method == 'POST':
        lancamento.delete()
        return redirect(reverse('core:dashboard') + f'?comp_id={comp_id}')
    return render(request, 'core/confirm_delete.html', {'object': lancamento, 'type': 'Lançamento'})

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
    regras = RegraImportacao.objects.all().order_by('padrao')
    
    for conta in contas:
        conta.usos = Lancamento.objects.filter(conta=conta).count()
        
    for agente in agentes:
        agente.usos = Lancamento.objects.filter(agente_pagador=agente).count()

    context = {
        'categorias': categorias,
        'contas': contas,
        'agentes': agentes,
        'regras': regras,
        'form_conta': ContaForm(),
        'form_agente': AgentePagadorForm(),
        'form_regra': RegraImportacaoForm(),
    }
    return render(request, 'core/configuracoes.html', context)

def agente_create(request):
    if request.method == 'POST':
        form = AgentePagadorForm(request.POST)
        if form.is_valid():
            agente = form.save()
            return redirect('core:agente_detail', pk=agente.pk)
    return redirect('core:configuracoes')

def agente_detail(request, pk):
    agente = get_object_or_404(AgentePagador, pk=pk)
    contas_bancarias = agente.contas_bancarias.all()
    context = {
        'agente': agente,
        'contas_bancarias': contas_bancarias,
        'form_agente': AgentePagadorForm(instance=agente),
    }
    return render(request, 'core/agente_detail.html', context)

def agente_edit(request, pk):
    agente = get_object_or_404(AgentePagador, pk=pk)
    if request.method == 'POST':
        form = AgentePagadorForm(request.POST, instance=agente)
        if form.is_valid():
            form.save()
            return redirect('core:agente_detail', pk=agente.pk)
    return redirect('core:agente_detail', pk=agente.pk)

def agente_delete(request, pk):
    agente = get_object_or_404(AgentePagador, pk=pk)
    if not Lancamento.objects.filter(agente_pagador=agente).exists():
        agente.delete()
    return redirect('core:configuracoes')

# Banking Views
def conta_bancaria_create(request, agente_id):
    agente = get_object_or_404(AgentePagador, id=agente_id)
    if request.method == 'POST':
        banco = request.POST.get('banco')
        conta = request.POST.get('conta')
        agencia = request.POST.get('agencia')
        tipo = request.POST.get('tipo', 'corrente')
        considerar = request.POST.get('considerar_como_salario') == 'on'
        
        ContaBancaria.objects.create(
            agente=agente,
            banco=banco,
            conta=conta,
            agencia=agencia,
            tipo=tipo,
            considerar_como_salario=considerar
        )
    return redirect('core:agente_detail', pk=agente.pk)

def conta_bancaria_edit(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk)
    if request.method == 'POST':
        conta.banco = request.POST.get('banco')
        conta.conta = request.POST.get('conta')
        conta.agencia = request.POST.get('agencia')
        conta.tipo = request.POST.get('tipo', 'corrente')
        conta.considerar_como_salario = request.POST.get('considerar_como_salario') == 'on'
        conta.save()
    return redirect('core:agente_detail', pk=conta.agente.pk)

def conta_bancaria_delete(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk)
    agente_pk = conta.agente.pk
    conta.delete()
    return redirect('core:agente_detail', pk=agente_pk)

def chave_pix_create(request, conta_id):
    conta = get_object_or_404(ContaBancaria, id=conta_id)
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        chave = request.POST.get('chave')
        ChavePix.objects.create(conta_bancaria=conta, tipo=tipo, chave=chave)
    return redirect('core:agente_detail', pk=conta.agente.pk)

def chave_pix_delete(request, pk):
    chave = get_object_or_404(ChavePix, pk=pk)
    agente_pk = chave.conta_bancaria.agente.pk
    chave.delete()
    return redirect('core:agente_detail', pk=agente_pk)

def categoria_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo', 'saida')
        is_salary = request.POST.get('is_salary') == 'on'
        if nome:
            Categoria.objects.get_or_create(nome=nome, defaults={'tipo': tipo, 'is_salary': is_salary})
    return redirect('core:configuracoes')

def categoria_edit(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        is_salary = request.POST.get('is_salary') == 'on'
        if nome:
            categoria.nome = nome
            categoria.tipo = tipo
            categoria.is_salary = is_salary
            categoria.save()
    return redirect('core:configuracoes')

def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    # Proteção: só deleta se não tiver nada vinculado
    if not Conta.objects.filter(categoria=categoria).exists() and not Parcelamento.objects.filter(categoria=categoria).exists():
        categoria.delete()
    return redirect('core:configuracoes')
def regra_create(request):
    if request.method == 'POST':
        form = RegraImportacaoForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('core:configuracoes')

def regra_delete(request, pk):
    regra = get_object_or_404(RegraImportacao, pk=pk)
    regra.delete()
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

def importar_dados(request):
    ofx_results = []
    agente_selecionado = None
    
    # 1. Processamento OFX (Se houver upload)
    # 1. Processamento de OFX (Staging)
    if request.method == 'POST' and request.FILES.getlist('ofx_files'):
        agente_id = request.POST.get('agente_id')
        conta_bancaria_id = request.POST.get('conta_bancaria_id')
        
        if agente_id:
            agente_selecionado = get_object_or_404(AgentePagador, id=agente_id)
            
        conta_bancaria = None
        if conta_bancaria_id:
            conta_bancaria = get_object_or_404(ContaBancaria, id=conta_bancaria_id)
            
        files = request.FILES.getlist('ofx_files')
        if agente_selecionado:
            transacoes_criadas = 0
            transacoes_puladas = 0
            transacoes_transferencia = 0
            for f in files:
                # Salva o arquivo fisicamente
                ofx_arq = OfxArquivo.objects.create(
                    arquivo=f, 
                    agente=agente_selecionado, 
                    conta_bancaria=conta_bancaria,
                    banco_nome='Detectando...'
                )
            
                # Identificação do Banco
                fname = f.name.lower()
                bank_name = 'Banco'
                if conta_bancaria:
                    bank_name = conta_bancaria.banco
                else:
                    if 'bradesco' in fname: bank_name = 'Bradesco'
                    elif 'nubank' in fname or 'nu bank' in fname: bank_name = 'Nubank'
                    elif 'itau' in fname: bank_name = 'Itaú'
                    elif 'santander' in fname: bank_name = 'Santander'
                    elif 'inter' in fname: bank_name = 'Inter'
                
                ofx_arq.banco_nome = bank_name
                ofx_arq.save()

                try:
                    f.seek(0)
                    ofx = OfxParser.parse(f)
                    statement = ofx.account.statement
                    for transaction in statement.transactions:
                        # 1. Prevenção de duplicatas por FITID
                        if OfxTransacao.objects.filter(fitid=transaction.id).exists():
                            transacoes_puladas += 1
                            continue

                        t_val = transaction.amount
                        t_date = transaction.date.date()
                        t_memo = transaction.memo
                        
                        # 2. Detecção de Transferência Interna (ENTRE CONTAS/BANCOS)
                        # Busca espelho: mesmo valor (invertido) no mesmo dia ou próximo
                        espelho = OfxTransacao.objects.filter(
                            valor=-t_val,
                            data__range=[t_date - timezone.timedelta(days=1), t_date + timezone.timedelta(days=1)]
                        ).exclude(arquivo__conta_bancaria=conta_bancaria).first()
                        
                        status = 'lido'
                        if espelho:
                            status = 'transferencia'
                            espelho.status = 'transferencia'
                            espelho.save()
                            transacoes_transferencia += 1

                        # 3. Busca Sugestão por Regra
                        sugestao_regra = None
                        memo_upper = t_memo.upper()
                        for regra in RegraImportacao.objects.all():
                            if regra.padrao.upper() in memo_upper:
                                sugestao_regra = regra
                                break
                        
                        # 4. Busca Sugestão por Conciliação (Data/Valor)
                        match = None
                        abs_val = abs(float(t_val))
                        comp = Competencia.objects.filter(mes=t_date.month, ano=t_date.year).first()
                        if comp:
                            posiveis = Lancamento.objects.filter(competencia=comp)
                            for p in posiveis:
                                p_val = float(p.valor_pago or p.valor_previsto)
                                if abs(abs_val - p_val) < 1.0 and abs((t_date - p.vencimento).days) <= 3:
                                    match = p
                                    break

                        OfxTransacao.objects.create(
                            arquivo=ofx_arq,
                            fitid=transaction.id,
                            data=t_date,
                            valor=t_val,
                            descricao=t_memo,
                            tipo=transaction.type,
                            status=status,
                            conta_sugerida=match.conta if match else None,
                            categoria_manual=sugestao_regra.categoria if sugestao_regra else None
                        )
                        transacoes_criadas += 1
                except Exception as e:
                    messages.error(request, f"Erro ao processar arquivo {f.name}: {str(e)}")
                    continue
            
            if transacoes_criadas > 0:
                messages.success(request, f"Importação concluída! {transacoes_criadas} novas transações importadas.")
            if transacoes_puladas > 0:
                messages.warning(request, f"{transacoes_puladas} transações foram ignoradas por já terem sido importadas anteriormente.")
            if transacoes_transferencia > 0:
                messages.info(request, f"{transacoes_transferencia} transações foram identificadas como transferências entre suas contas e movidas para a aba de Ignorados.")
                
        return redirect(reverse('core:importar_dados') + '#ofx')

    # Busca transações (Removido logicade ofx_results redundante)
    legado_path = r'E:\Gestor_Contas\db.sqlite3'
    try:
        conn = sqlite3.connect(legado_path)
        cursor = conn.cursor()
        
        # Busca IDs já migrados
        contas_migradas_ids = list(Conta.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))
        lancamentos_migrados_ids = list(Lancamento.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))
        parcelamentos_migrados_ids = list(Parcelamento.objects.filter(legacy_id__isnull=False).values_list('legacy_id', flat=True))

        # Contas
        cursor.execute("SELECT id, nome, data_vencimento, mensal, observacoes FROM gestor_contas_conta")
        contas_legado = [{
            'id': row[0], 'nome': row[1], 'dia': row[2], 'mensal': row[3], 'obs': row[4],
            'migrada': row[0] in contas_migradas_ids
        } for row in cursor.fetchall()]

        # Lançamentos agrupados
        cursor.execute("""
            SELECT cp.id, cp.data_pagamento, cp.valor_pago, c.nome, comp.mes, comp.ano, cp.comprovante, comp.id as comp_id
            FROM gestor_contas_contapaga cp
            JOIN gestor_contas_conta c ON cp.conta_id = c.id
            JOIN gestor_contas_competencia comp ON cp.competencia_id = comp.id
            ORDER BY comp.ano DESC, comp.mes DESC
        """)
        
        competencias_dict = {}
        for row in cursor.fetchall():
            key = f"{row[4]}/{row[5]}"
            if key not in competencias_dict:
                competencias_dict[key] = {'id': row[7], 'mes': row[4], 'ano': row[5], 'label': key, 'lancamentos': []}
            competencias_dict[key]['lancamentos'].append({
                'id': row[0], 'data': row[1], 'valor': row[2], 'conta': row[3], 
                'migrado': row[0] in lancamentos_migrados_ids
            })

        # Parcelamentos
        cursor.execute("SELECT id, nome, qtd_parcelas, valor_total FROM gestor_contas_conta WHERE parcelas = 1")
        parcelamentos_legado = []
        for row in cursor.fetchall():
            cursor.execute("SELECT COUNT(*) FROM gestor_contas_contapaga WHERE conta_id = ?", (row[0],))
            pagos = cursor.fetchone()[0]
            parcelamentos_legado.append({
                'id': row[0], 'nome': row[1], 'total': row[2], 'pagas': pagos, 
                'migrado': row[0] in parcelamentos_migrados_ids
            })
        
        conn.close()
    except Exception:
        contas_legado = []
        competencias_dict = {}
        parcelamentos_legado = []

    # 2. Busca de todos os registros persistidos para a visualização (Central de Conciliação)
    tab = request.GET.get('tab', 'pendentes')
    agente_id_filter = request.GET.get('agente_id')
    conta_id_filter = request.GET.get('conta_id')
    
    transacoes_qs = OfxTransacao.objects.all().select_related(
        'arquivo__agente', 
        'arquivo__conta_bancaria', 
        'conta_sugerida', 
        'categoria_manual',
        'lancamento_criado'
    ).order_by('-data', '-id')
    
    # Filtros Globais
    if agente_id_filter:
        transacoes_qs = transacoes_qs.filter(arquivo__agente_id=agente_id_filter)
    if conta_id_filter:
        transacoes_qs = transacoes_qs.filter(arquivo__conta_bancaria_id=conta_id_filter)
        
    # Filtragem por Aba
    if tab == 'pendentes':
        transacoes_qs = transacoes_qs.filter(status='lido')
    elif tab == 'validados':
        transacoes_qs = transacoes_qs.filter(status='validado')
    elif tab == 'processados':
        transacoes_qs = transacoes_qs.filter(status='processado')
    elif tab == 'ignorar':
        transacoes_qs = transacoes_qs.filter(status__in=['ignorado', 'transferencia'])

    context = {
        'transacoes': transacoes_qs,
        'current_tab': tab,
        'agente_id_filter': agente_id_filter,
        'conta_id_filter': conta_id_filter,
        'agentes': AgentePagador.objects.all().order_by('nome'),
        'categorias': Categoria.objects.all().order_by('nome'),
        'categorias_entrada': Categoria.objects.filter(tipo='entrada').order_by('nome'),
        'categorias_saida': Categoria.objects.filter(tipo='saida').order_by('nome'),
        'contas': Conta.objects.all().order_by('nome'),
        'contas_bancarias': ContaBancaria.objects.all().select_related('agente').order_by('agente__nome', 'banco'),
        'contas_legado': contas_legado,
        'parcelamentos_legado': parcelamentos_legado,
        'competencias_legado': competencias_dict.values(),
    }
    return render(request, 'core/importar_dados.html', context)

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
        
    return redirect('core:importar_dados')

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
    return redirect('core:importar_dados')

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
    return redirect('core:importar_dados')

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
        
    return redirect('core:importar_dados')

def ofx_validar(request):
    # Marca todos os 'lido' como 'validado'
    OfxTransacao.objects.filter(status='lido').update(status='validado')
    return redirect(reverse('core:importar_dados') + '#ofx')

def ofx_vincular_conta(request, pk):
    tab = request.GET.get('tab', 'pendentes')
    if request.method == 'POST':
        transacao = get_object_or_404(OfxTransacao, pk=pk)
        conta_id = request.POST.get('conta_id')
        if conta_id:
            transacao.conta_sugerida = get_object_or_404(Conta, id=conta_id)
            transacao.status = 'validado'
            transacao.save()
    return redirect(reverse('core:importar_dados') + f'?tab={tab}#ofx')

def processar_vinculados(request):
    # Processa apenas transações validadas que tenham conta_sugerida
    transacoes = OfxTransacao.objects.filter(status='validado', conta_sugerida__isnull=False)
    
    processados_count = 0
    for t in transacoes:
        # Busca a competência aberta para o mês da transação
        comp = Competencia.objects.filter(mes=t.data.month, ano=t.data.year, status='aberto').first()
        if not comp:
            continue
            
        # REGRA: Verificar se já existe um lançamento para esta conta nesta competência
        lanc = Lancamento.objects.filter(conta=t.conta_sugerida, competencia=comp).first()
        
        if lanc:
            # ATUALIZA lançamento existente com dados do banco
            lanc.valor_pago = abs(t.valor)
            lanc.data_pagamento = t.data
            lanc.status = 'pago'
            lanc.transacao_id = t.fitid
            # Se não tinha valor previsto, assume o do banco
            if not lanc.valor_previsto:
                lanc.valor_previsto = abs(t.valor)
            lanc.save()
        else:
            # CRIA novo lançamento se não existir
            lanc = Lancamento.objects.create(
                conta=t.conta_sugerida,
                competencia=comp,
                valor_previsto=abs(t.valor),
                valor_pago=abs(t.valor),
                vencimento=t.data,
                data_pagamento=t.data,
                descricao=f"Importado OFX: {t.descricao}",
                status='pago',
                agente_pagador=t.arquivo.agente,
                transacao_id=t.fitid
            )

        # Marca a transação OFX como processada
        t.status = 'processado'
        t.lancamento_criado = lanc
        t.save()
        processados_count += 1
        
    return redirect(reverse('core:importar_dados') + '#ofx')

def ofx_limpar_staging(request):
    tab = request.GET.get('tab', 'pendentes')
    # Mapeia tab para status
    status_map = {
        'pendentes': 'lido',
        'validados': 'validado',
        'ignorar': 'ignorado'
    }
    
    target_status = status_map.get(tab)
    if target_status:
        OfxTransacao.objects.filter(status=target_status).delete()
    else:
        # Se não tiver tab ou for desconhecida, limpa apenas os não processados
        OfxTransacao.objects.filter(status__in=['lido', 'validado']).delete()
        
    return redirect(reverse('core:importar_dados') + f'?tab={tab}#ofx')

    return HttpResponse(status=204)

def ofx_update_categoria(request, pk):
    if request.method == 'POST':
        transacao = get_object_or_404(OfxTransacao, pk=pk)
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = get_object_or_404(Categoria, id=categoria_id)
            transacao.categoria_manual = categoria
            transacao.save()
    return HttpResponse(status=204)

def ofx_desvincular(request, pk):
    tab = request.GET.get('tab', 'pendentes')
    transacao = get_object_or_404(OfxTransacao, pk=pk)
    transacao.conta_sugerida = None
    transacao.status = 'lido'
    transacao.save()
    return redirect(reverse('core:importar_dados') + f'?tab={tab}#ofx')

def ofx_bulk_action(request):
    tab = request.POST.get('current_tab', 'pendentes')
    if request.method == 'POST':
        ids = request.POST.getlist('transacao_ids')
        action_type = request.POST.get('action_type') # 'categoria' ou 'conta'
        target_id = request.POST.get('target_id')
        
        if not ids or not target_id:
            return redirect(reverse('core:importar_dados') + f'?tab={tab}#ofx')
            
        transacoes = OfxTransacao.objects.filter(pk__in=ids)
        
        if action_type == 'categoria':
            categoria = get_object_or_404(Categoria, id=target_id)
            transacoes.update(categoria_manual=categoria)
        elif action_type == 'conta':
            conta = get_object_or_404(Conta, id=target_id)
            transacoes.update(conta_sugerida=conta, status='validado')
            
    return redirect(reverse('core:importar_dados') + f'?tab={tab}#ofx')
