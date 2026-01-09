"""
URLs - Módulo Colaboradores
"""

from django.urls import path
from . import views

app_name = 'colaboradores'

urlpatterns = [
    # Home - Redireciona para lista de colaboradores
    path('', views.colaborador_list, name='home'),

    # Colaboradores
    path('colaboradores/', views.colaborador_list, name='colaborador_list'),
    path('colaboradores/novo/', views.colaborador_create, name='colaborador_create'),
    path('colaboradores/<int:pk>/', views.colaborador_detail, name='colaborador_detail'),
    path('colaboradores/<int:pk>/editar/', views.colaborador_edit, name='colaborador_edit'),
    path('colaboradores/<int:pk>/pdf/', views.colaborador_pdf, name='colaborador_pdf'),
    path('colaboradores/<int:pk>/reativar/', views.colaborador_reativar, name='colaborador_reativar'),

    # Dependentes
    path('colaboradores/<int:colaborador_pk>/dependentes/novo/', views.dependente_create, name='dependente_create'),

    # Localizações
    path('colaboradores/<int:colaborador_pk>/localizacoes/novo/', views.localizacao_create, name='localizacao_create'),
    path('relatorio-localizacoes/', views.relatorio_localizacoes, name='relatorio_localizacoes'),

    # Férias
    path('ferias/', views.ferias_list, name='ferias_list'),
    path('colaboradores/<int:colaborador_pk>/ferias/novo/', views.ferias_create, name='ferias_create'),

    # Contratos
    path('contratos/', views.contratos_list, name='contratos_list'),

    # Empresas
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/nova/', views.empresa_create, name='empresa_create'),
    path('empresas/<int:pk>/editar/', views.empresa_edit, name='empresa_edit'),
    path('empresas/<int:pk>/excluir/', views.empresa_delete, name='empresa_delete'),

    # Blocklist
    path('blocklist/', views.blocklist, name='blocklist'),

    # Aniversariantes
    path('aniversariantes/', views.aniversariantes, name='aniversariantes'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Outros
    path('exportar/', views.exportar, name='exportar'),
    path('logs/', views.logs, name='logs'),
    path('sobre/', views.sobre, name='sobre'),
]
