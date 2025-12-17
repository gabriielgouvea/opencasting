from django import template
from django.db.models import Count
from django.utils import timezone
from datetime import date
from core.models import UserProfile, Job, Candidatura

register = template.Library()

@register.simple_tag
def get_kpis():
    # --- 1. CARDS PRINCIPAIS ---
    total_promotores = UserProfile.objects.count()
    pendentes = UserProfile.objects.filter(status='pendente').count()
    try:
        vagas_abertas = Job.objects.filter(status='aberta').count()
    except:
        vagas_abertas = Job.objects.count()
    
    hoje = timezone.now().date()
    candidaturas_hoje = Candidatura.objects.filter(data_candidatura__date=hoje).count()

    # --- 2. DADOS PARA OS GRÁFICOS ---
    
    # STATUS (Pizza)
    qs_status = UserProfile.objects.values('status').annotate(total=Count('status'))
    labels_status = [x['status'].upper() if x['status'] else 'INDEFINIDO' for x in qs_status]
    data_status = [x['total'] for x in qs_status]
    colors_status = []
    for label in labels_status:
        if 'APROVADO' in label: colors_status.append('#2ecc71')
        elif 'PENDENTE' in label: colors_status.append('#f1c40f')
        elif 'REPROVADO' in label: colors_status.append('#e74c3c')
        else: colors_status.append('#95a5a6')

    # --- 3. DADOS DEMOGRÁFICOS (Para o Gráfico Dinâmico) ---
    
    # GÊNERO
    qs_genero = UserProfile.objects.values('genero').annotate(total=Count('genero'))
    chart_genero = {
        'labels': [x['genero'] for x in qs_genero if x['genero']],
        'data': [x['total'] for x in qs_genero if x['genero']]
    }

    # CAMISETA
    qs_camiseta = UserProfile.objects.values('tamanho_camiseta').annotate(total=Count('tamanho_camiseta'))
    # Ordenar tamanhos: PP, P, M, G, GG...
    order = {'PP':0, 'P':1, 'M':2, 'G':3, 'GG':4, 'XG':5}
    # Filtra e Ordena
    dados_cam = sorted(
        [x for x in qs_camiseta if x['tamanho_camiseta']], 
        key=lambda k: order.get(k['tamanho_camiseta'], 99)
    )
    chart_camiseta = {
        'labels': [x['tamanho_camiseta'] for x in dados_cam],
        'data': [x['total'] for x in dados_cam]
    }

    # CALÇADO
    qs_calcado = UserProfile.objects.values('calcado').annotate(total=Count('calcado')).order_by('calcado')
    chart_calcado = {
        'labels': [str(x['calcado']) for x in qs_calcado if x['calcado']],
        'data': [x['total'] for x in qs_calcado if x['calcado']]
    }

    # ETNIA
    qs_etnia = UserProfile.objects.values('etnia').annotate(total=Count('etnia'))
    chart_etnia = {
        'labels': [x['etnia'] for x in qs_etnia if x['etnia']],
        'data': [x['total'] for x in qs_etnia if x['etnia']]
    }

    # IDADE (Cálculo aproximado baseado no ano de nascimento)
    # Vamos agrupar em faixas: 18-24, 25-34, 35+
    ano_atual = date.today().year
    perfis = UserProfile.objects.filter(data_nascimento__isnull=False).values_list('data_nascimento', flat=True)
    idades = []
    for nasc in perfis:
        if nasc: idades.append(ano_atual - nasc.year)
    
    faixas = {'18-24': 0, '25-34': 0, '35-44': 0, '45+': 0}
    for idade in idades:
        if 18 <= idade <= 24: faixas['18-24'] += 1
        elif 25 <= idade <= 34: faixas['25-34'] += 1
        elif 35 <= idade <= 44: faixas['35-44'] += 1
        elif idade >= 45: faixas['45+'] += 1
    
    chart_idade = {
        'labels': list(faixas.keys()),
        'data': list(faixas.values())
    }

    return {
        'kpi': {
            'total': total_promotores,
            'pendentes': pendentes,
            'vagas': vagas_abertas,
            'candidaturas': candidaturas_hoje
        },
        'status': { 'labels': labels_status, 'data': data_status, 'colors': colors_status },
        'demografia': {
            'genero': chart_genero,
            'camiseta': chart_camiseta,
            'calcado': chart_calcado,
            'etnia': chart_etnia,
            'idade': chart_idade
        }
    }