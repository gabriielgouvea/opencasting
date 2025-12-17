from django import template
from django.db.models import Count
from django.utils import timezone
from core.models import UserProfile, Job, Candidatura

register = template.Library()

@register.simple_tag
def get_kpis():
    # --- 1. CARDS PRINCIPAIS (KPIs) ---
    total_promotores = UserProfile.objects.count()
    pendentes = UserProfile.objects.filter(status='pendente').count()
    
    # Verifica se existem vagas e conta as abertas
    # Se o seu model Job não tiver o campo 'status', conte todos ou ajuste o filtro
    try:
        vagas_abertas = Job.objects.filter(status='aberta').count()
    except:
        vagas_abertas = Job.objects.count() # Fallback se não tiver status
    
    # Candidaturas de hoje
    hoje = timezone.now().date()
    candidaturas_hoje = Candidatura.objects.filter(data_candidatura__date=hoje).count()

    # --- 2. DADOS PARA OS GRÁFICOS ---
    
    # -- Gráfico 1: Status (Pizza) --
    # Pega os dados brutos do banco
    qs_status = UserProfile.objects.values('status').annotate(total=Count('status'))
    
    # Transforma em listas simples para o gráfico
    labels_status = [x['status'].upper() if x['status'] else 'INDEFINIDO' for x in qs_status]
    data_status = [x['total'] for x in qs_status]
    
    # Define cores baseadas no status
    colors_status = []
    for label in labels_status:
        if 'APROVADO' in label: colors_status.append('#28a745') # Verde
        elif 'PENDENTE' in label: colors_status.append('#ffc107') # Amarelo
        elif 'REPROVADO' in label: colors_status.append('#dc3545') # Vermelho
        else: colors_status.append('#6c757d') # Cinza (Outros)

    # -- Gráfico 2: Gênero (Barra) --
    qs_genero = UserProfile.objects.values('genero').annotate(total=Count('genero'))
    
    # Filtra vazios e cria as listas
    labels_genero = [x['genero'] for x in qs_genero if x['genero']]
    data_genero = [x['total'] for x in qs_genero if x['genero']]

    # Retorna tudo num dicionário organizado
    return {
        'total_promotores': total_promotores,
        'pendentes': pendentes,
        'vagas_abertas': vagas_abertas,
        'candidaturas_hoje': candidaturas_hoje,
        'chart_status': {
            'labels': labels_status,
            'data': data_status,
            'colors': colors_status
        },
        'chart_genero': {
            'labels': labels_genero,
            'data': data_genero
        }
    }