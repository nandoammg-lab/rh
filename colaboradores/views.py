"""
Views - Módulo RH
"""

from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Sum, Q
from django.http import HttpResponse

from .models import (
    Empresa, Colaborador, Dependente, Localizacao,
    Ferias, PeriodoFerias, ContratoExperiencia, Blocklist,
    Configuracao, HistoricoAlteracao, DocumentoColaborador, LogSistema
)


# =============================================================================
# COLABORADORES
# =============================================================================

def colaborador_list(request):
    """Lista de colaboradores"""
    colaboradores = Colaborador.objects.select_related('empresa').prefetch_related(
        'localizacoes', 'documentos', 'contratos_experiencia'
    ).order_by('nome_completo')

    # Filtros
    empresa_id = request.GET.get('empresa')
    localizacao = request.GET.get('localizacao')
    search = request.GET.get('q')

    if empresa_id:
        colaboradores = colaboradores.filter(empresa_id=empresa_id)

    if localizacao:
        colaboradores = colaboradores.filter(
            localizacoes__local_nome=localizacao,
            localizacoes__data_fim__isnull=True
        )

    if search:
        colaboradores = colaboradores.filter(
            Q(nome_completo__icontains=search) | Q(cpf__icontains=search)
        )

    # Adicionar propriedades calculadas
    for colab in colaboradores:
        # Localização atual
        loc_atual = colab.localizacoes.filter(data_fim__isnull=True).first()
        colab.localizacao_atual = loc_atual.local_nome if loc_atual else None

        # Tipo de contrato
        contrato = colab.contratos_experiencia.filter(status='VIGENTE').first()
        if contrato:
            colab.contrato_tipo = 'Experiência'
        else:
            colab.contrato_tipo = 'CLT' if colab.status == 'ATIVO' else None

        # Documentos obrigatórios (placeholder)
        colab.docs_obrigatorios = 5

    # Paginação
    paginator = Paginator(colaboradores, 20)
    page = request.GET.get('page', 1)
    colaboradores_page = paginator.get_page(page)

    # Dados para filtros
    empresas = Empresa.objects.filter(ativa=True)
    localizacoes = Localizacao.objects.filter(
        data_fim__isnull=True
    ).values_list('local_nome', flat=True).distinct()

    # Alertas
    hoje = date.today()
    contratos_vencendo = ContratoExperiencia.objects.filter(
        status='VIGENTE',
        data_fim_inicial__lte=hoje + timedelta(days=5),
        data_fim_inicial__gte=hoje
    ).count()

    ferias_vencendo = Ferias.objects.filter(
        status__in=['PENDENTE', 'PROGRAMADA'],
        periodo_concessivo_limite__lte=hoje + timedelta(days=90),
        periodo_concessivo_limite__gte=hoje
    ).count()

    context = {
        'colaboradores': colaboradores_page,
        'empresas': empresas,
        'localizacoes': localizacoes,
        'contratos_vencendo': contratos_vencendo,
        'ferias_vencendo': ferias_vencendo,
        'is_paginated': colaboradores_page.has_other_pages(),
        'page_obj': colaboradores_page,
    }
    return render(request, 'colaboradores/colaborador_list.html', context)


def colaborador_detail(request, pk):
    """Detalhes do colaborador"""
    colaborador = get_object_or_404(
        Colaborador.objects.select_related('empresa').prefetch_related(
            'dependentes', 'localizacoes', 'ferias', 'documentos', 'contratos_experiencia'
        ),
        pk=pk
    )
    return render(request, 'colaboradores/colaborador_detail.html', {'colaborador': colaborador})


def colaborador_create(request):
    """Criar novo colaborador"""
    if request.method == 'POST':
        # Processar formulário
        colaborador = Colaborador()
        _save_colaborador_from_post(colaborador, request.POST, request.FILES)
        messages.success(request, 'Colaborador cadastrado com sucesso!')
        return redirect('colaboradores:colaborador_detail', pk=colaborador.pk)

    empresas = Empresa.objects.filter(ativa=True)
    return render(request, 'colaboradores/colaborador_form.html', {
        'form': type('Form', (), {'instance': Colaborador()})(),
        'empresas': empresas,
    })


def colaborador_edit(request, pk):
    """Editar colaborador"""
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if request.method == 'POST':
        _save_colaborador_from_post(colaborador, request.POST, request.FILES)
        messages.success(request, 'Colaborador atualizado com sucesso!')
        return redirect('colaboradores:colaborador_detail', pk=colaborador.pk)

    empresas = Empresa.objects.filter(ativa=True)
    return render(request, 'colaboradores/colaborador_form.html', {
        'form': type('Form', (), {'instance': colaborador})(),
        'empresas': empresas,
    })


def _save_colaborador_from_post(colaborador, post_data, files):
    """Helper para salvar colaborador do POST"""
    # Dados básicos
    colaborador.nome_completo = post_data.get('nome_completo', '')
    colaborador.cpf = post_data.get('cpf', '')
    colaborador.status = post_data.get('status', 'ATIVO')

    # Empresa
    empresa_id = post_data.get('empresa')
    if empresa_id:
        colaborador.empresa_id = int(empresa_id)

    # Foto
    if 'foto' in files:
        colaborador.foto = files['foto']

    colaborador.save()


def colaborador_pdf(request, pk):
    """Gerar PDF do colaborador"""
    colaborador = get_object_or_404(Colaborador, pk=pk)
    # TODO: Implementar geração de PDF
    messages.info(request, 'Geração de PDF será implementada em breve.')
    return redirect('colaboradores:colaborador_detail', pk=pk)


def colaborador_reativar(request, pk):
    """Reativar colaborador"""
    colaborador = get_object_or_404(Colaborador, pk=pk)
    colaborador.status = 'ATIVO'
    colaborador.save()
    messages.success(request, f'Colaborador {colaborador.nome_completo} reativado com sucesso!')
    return redirect('colaboradores:colaborador_list')


# =============================================================================
# EMPRESAS
# =============================================================================

def empresa_list(request):
    """Lista de empresas"""
    empresas = Empresa.objects.all().order_by('razao_social')
    return render(request, 'colaboradores/empresa_list.html', {'empresas': empresas})


def empresa_create(request):
    """Criar nova empresa"""
    if request.method == 'POST':
        empresa = Empresa(
            razao_social=request.POST.get('razao_social', ''),
            cnpj=request.POST.get('cnpj', ''),
            endereco=request.POST.get('endereco', ''),
            numero=request.POST.get('numero', ''),
            complemento=request.POST.get('complemento', ''),
            bairro=request.POST.get('bairro', ''),
            cep=request.POST.get('cep', ''),
            cidade=request.POST.get('cidade', ''),
            uf=request.POST.get('uf', ''),
            telefone=request.POST.get('telefone', ''),
            email=request.POST.get('email', ''),
            ativa=request.POST.get('ativa') == 'on',
        )
        if 'logo' in request.FILES:
            empresa.logo = request.FILES['logo']
        empresa.save()
        messages.success(request, 'Empresa cadastrada com sucesso!')
        return redirect('colaboradores:empresa_list')

    return render(request, 'colaboradores/empresa_form.html', {
        'form': type('Form', (), {'instance': Empresa()})(),
    })


def empresa_edit(request, pk):
    """Editar empresa"""
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        empresa.razao_social = request.POST.get('razao_social', empresa.razao_social)
        empresa.cnpj = request.POST.get('cnpj', empresa.cnpj)
        empresa.endereco = request.POST.get('endereco', '')
        empresa.numero = request.POST.get('numero', '')
        empresa.complemento = request.POST.get('complemento', '')
        empresa.bairro = request.POST.get('bairro', '')
        empresa.cep = request.POST.get('cep', '')
        empresa.cidade = request.POST.get('cidade', '')
        empresa.uf = request.POST.get('uf', '')
        empresa.telefone = request.POST.get('telefone', '')
        empresa.email = request.POST.get('email', '')
        empresa.ativa = request.POST.get('ativa') == 'on'
        if 'logo' in request.FILES:
            empresa.logo = request.FILES['logo']
        empresa.save()
        messages.success(request, 'Empresa atualizada com sucesso!')
        return redirect('colaboradores:empresa_list')

    return render(request, 'colaboradores/empresa_form.html', {
        'form': type('Form', (), {'instance': empresa})(),
    })


def empresa_delete(request, pk):
    """Excluir empresa"""
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('colaboradores:empresa_list')
    return render(request, 'colaboradores/empresa_confirm_delete.html', {'empresa': empresa})


# =============================================================================
# CONTRATOS DE EXPERIÊNCIA
# =============================================================================

def contratos_list(request):
    """Lista de contratos de experiência"""
    contratos = ContratoExperiencia.objects.select_related(
        'colaborador', 'colaborador__empresa'
    ).filter(status='VIGENTE').order_by('data_fim_inicial')

    hoje = date.today()
    for contrato in contratos:
        contrato.dias_restantes = (contrato.data_fim_inicial - hoje).days

    return render(request, 'colaboradores/contratos_list.html', {'contratos': contratos})


# =============================================================================
# FÉRIAS
# =============================================================================

def ferias_list(request):
    """Lista de férias"""
    ferias = Ferias.objects.select_related(
        'colaborador', 'colaborador__empresa'
    ).exclude(status='CONCLUIDA').order_by('periodo_concessivo_limite')

    hoje = date.today()
    for f in ferias:
        f.dias_restantes = (f.periodo_concessivo_limite - hoje).days

    return render(request, 'colaboradores/ferias_list.html', {'ferias_list': ferias})


def ferias_create(request, colaborador_pk):
    """Criar novo período de férias"""
    colaborador = get_object_or_404(Colaborador, pk=colaborador_pk)
    # TODO: Implementar formulário
    messages.info(request, 'Cadastro de férias será implementado em breve.')
    return redirect('colaboradores:colaborador_detail', pk=colaborador_pk)


# =============================================================================
# DEPENDENTES
# =============================================================================

def dependente_create(request, colaborador_pk):
    """Criar novo dependente"""
    colaborador = get_object_or_404(Colaborador, pk=colaborador_pk)
    # TODO: Implementar formulário
    messages.info(request, 'Cadastro de dependente será implementado em breve.')
    return redirect('colaboradores:colaborador_detail', pk=colaborador_pk)


# =============================================================================
# LOCALIZAÇÕES
# =============================================================================

def localizacao_create(request, colaborador_pk):
    """Criar nova localização"""
    colaborador = get_object_or_404(Colaborador, pk=colaborador_pk)
    # TODO: Implementar formulário
    messages.info(request, 'Cadastro de localização será implementado em breve.')
    return redirect('colaboradores:colaborador_detail', pk=colaborador_pk)


def relatorio_localizacoes(request):
    """Relatório de localizações"""
    localizacoes = Localizacao.objects.select_related(
        'colaborador', 'colaborador__empresa'
    ).filter(data_fim__isnull=True).order_by('local_nome', 'colaborador__nome_completo')

    return render(request, 'colaboradores/relatorio_localizacoes.html', {
        'localizacoes': localizacoes
    })


# =============================================================================
# BLOCKLIST
# =============================================================================

def blocklist(request):
    """Lista de blocklist"""
    blocklist_items = Blocklist.objects.select_related('empresa').order_by('-created_at')
    return render(request, 'colaboradores/blocklist.html', {'blocklist': blocklist_items})


# =============================================================================
# ANIVERSARIANTES
# =============================================================================

def aniversariantes(request):
    """Lista de aniversariantes"""
    hoje = date.today()
    mes = int(request.GET.get('mes', hoje.month))

    aniversariantes_list = Colaborador.objects.filter(
        status='ATIVO',
        data_nascimento__month=mes
    ).order_by('data_nascimento__day')

    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
        (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
        (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
        (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    return render(request, 'colaboradores/aniversariantes.html', {
        'aniversariantes': aniversariantes_list,
        'meses': meses,
        'mes_atual': mes,
    })


# =============================================================================
# DASHBOARD
# =============================================================================

def dashboard(request):
    """Dashboard com estatísticas"""
    hoje = date.today()

    # KPIs básicos
    total_ativos = Colaborador.objects.filter(status='ATIVO').count()
    total_empresas = Empresa.objects.filter(ativa=True).count()

    # Contratos vencendo
    contratos_vencendo = ContratoExperiencia.objects.filter(
        status='VIGENTE',
        data_fim_inicial__lte=hoje + timedelta(days=30),
        data_fim_inicial__gte=hoje
    ).count()

    contratos_lista = ContratoExperiencia.objects.select_related(
        'colaborador', 'colaborador__empresa'
    ).filter(
        status='VIGENTE',
        data_fim_inicial__lte=hoje + timedelta(days=30),
        data_fim_inicial__gte=hoje
    ).order_by('data_fim_inicial')[:10]

    for c in contratos_lista:
        c.dias_restantes = (c.data_fim_inicial - hoje).days

    # Férias vencendo
    ferias_vencendo = Ferias.objects.filter(
        status__in=['PENDENTE', 'PROGRAMADA'],
        periodo_concessivo_limite__lte=hoje + timedelta(days=90),
        periodo_concessivo_limite__gte=hoje
    ).count()

    ferias_lista = Ferias.objects.select_related(
        'colaborador', 'colaborador__empresa'
    ).filter(
        status__in=['PENDENTE', 'PROGRAMADA'],
        periodo_concessivo_limite__lte=hoje + timedelta(days=90),
        periodo_concessivo_limite__gte=hoje
    ).order_by('periodo_concessivo_limite')[:10]

    for f in ferias_lista:
        f.dias_restantes = (f.periodo_concessivo_limite - hoje).days

    # Em férias agora
    em_ferias = Colaborador.objects.filter(status='FERIAS').count()

    # Salários
    salario_stats = Colaborador.objects.filter(
        status='ATIVO', salario__isnull=False
    ).aggregate(
        media=Avg('salario'),
        total=Sum('salario')
    )
    salario_medio = salario_stats['media'] or 0
    folha_total = salario_stats['total'] or 0

    # Aniversariantes do mês
    aniversariantes_mes = Colaborador.objects.filter(
        status='ATIVO',
        data_nascimento__month=hoje.month
    ).count()

    # Por empresa
    por_empresa = Colaborador.objects.filter(
        status='ATIVO', empresa__isnull=False
    ).values('empresa__razao_social').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    max_empresa = por_empresa[0]['total'] if por_empresa else 1

    # Por localização
    por_localizacao = Localizacao.objects.filter(
        data_fim__isnull=True,
        colaborador__status='ATIVO'
    ).values('local_nome').annotate(
        total=Count('colaborador_id', distinct=True)
    ).order_by('-total')[:10]
    max_localizacao = por_localizacao[0]['total'] if por_localizacao else 1

    # Por função
    por_funcao = Colaborador.objects.filter(
        status='ATIVO', funcao__isnull=False
    ).exclude(funcao='').values('funcao').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    max_funcao = por_funcao[0]['total'] if por_funcao else 1

    # Por departamento
    por_departamento = Colaborador.objects.filter(
        status='ATIVO', departamento__isnull=False
    ).exclude(departamento='').values('departamento').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    max_departamento = por_departamento[0]['total'] if por_departamento else 1

    # Demografia - Sexo
    por_sexo = Colaborador.objects.filter(
        status='ATIVO'
    ).values('sexo').annotate(total=Count('id')).order_by('-total')

    # Demografia - Estado Civil
    por_estado_civil = Colaborador.objects.filter(
        status='ATIVO'
    ).values('estado_civil').annotate(total=Count('id')).order_by('-total')

    # Demografia - Escolaridade
    por_escolaridade = Colaborador.objects.filter(
        status='ATIVO'
    ).values('grau_instrucao').annotate(total=Count('id')).order_by('-total')

    # Demografia - Faixa Etária
    por_faixa_etaria = []
    faixas = [
        ('18-25', 18, 25),
        ('26-35', 26, 35),
        ('36-45', 36, 45),
        ('46-55', 46, 55),
        ('56+', 56, 100),
    ]
    for nome, min_idade, max_idade in faixas:
        min_nasc = hoje.replace(year=hoje.year - max_idade - 1)
        max_nasc = hoje.replace(year=hoje.year - min_idade)
        count = Colaborador.objects.filter(
            status='ATIVO',
            data_nascimento__gte=min_nasc,
            data_nascimento__lte=max_nasc
        ).count()
        if count > 0:
            por_faixa_etaria.append({'faixa': nome, 'total': count})

    context = {
        'total_ativos': total_ativos,
        'total_empresas': total_empresas,
        'contratos_vencendo': contratos_vencendo,
        'contratos_lista': contratos_lista,
        'ferias_vencendo': ferias_vencendo,
        'ferias_lista': ferias_lista,
        'em_ferias': em_ferias,
        'salario_medio': salario_medio,
        'folha_total': folha_total,
        'aniversariantes_mes': aniversariantes_mes,
        'por_empresa': por_empresa,
        'max_empresa': max_empresa,
        'por_localizacao': por_localizacao,
        'max_localizacao': max_localizacao,
        'por_funcao': por_funcao,
        'max_funcao': max_funcao,
        'por_departamento': por_departamento,
        'max_departamento': max_departamento,
        'por_sexo': por_sexo,
        'por_estado_civil': por_estado_civil,
        'por_escolaridade': por_escolaridade,
        'por_faixa_etaria': por_faixa_etaria,
    }
    return render(request, 'colaboradores/dashboard.html', context)


# =============================================================================
# OUTROS
# =============================================================================

def exportar(request):
    """Página de exportação"""
    return render(request, 'colaboradores/exportar.html')


def logs(request):
    """Logs do sistema"""
    logs_list = LogSistema.objects.all().order_by('-data_hora')[:100]
    return render(request, 'colaboradores/logs.html', {'logs': logs_list})


def sobre(request):
    """Página sobre"""
    return render(request, 'colaboradores/sobre.html')
