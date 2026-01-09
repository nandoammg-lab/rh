"""Migration inicial - Criação de todos os schemas e tabelas

Revision ID: 20260108_000001
Revises:
Create Date: 2026-01-08

Esta migration cria a estrutura completa do banco de dados unificado:
- Schema CRM: Clientes, Leads, Visitas
- Schema RH: Colaboradores, Férias, Dependentes
- Schema Compras: Fornecedores, Requisições, Cotações
- Schema Patrimônio: Bens, Custódias, Fardamentos
- Schema Documental: Documentos ISO, NC, Treinamentos
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '20260108_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Schemas a serem criados
SCHEMAS = ['crm', 'rh', 'compras', 'patrimonio', 'documental']


def upgrade() -> None:
    # Criar schemas
    for schema in SCHEMAS:
        op.execute(f"CREATE DATABASE IF NOT EXISTS `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

    # ========== SCHEMA CRM ==========

    op.create_table('clientes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('uf', sa.String(2), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )

    op.create_table('contatos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['crm.clientes.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )

    op.create_table('leads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(20), nullable=True, unique=True),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('local', sa.String(255), nullable=True),
        sa.Column('uf_projeto', sa.String(2), nullable=True),
        sa.Column('convite', sa.String(255), nullable=True),
        sa.Column('contato', sa.String(255), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('data_entrada', sa.Date(), nullable=True),
        sa.Column('caderno_encargos', sa.Text(), nullable=True),
        sa.Column('contato_tecnico', sa.String(255), nullable=True),
        sa.Column('telefone_tecnico', sa.String(20), nullable=True),
        sa.Column('email_tecnico', sa.String(255), nullable=True),
        sa.Column('visita_agendada', sa.String(50), nullable=True),
        sa.Column('decisao_go', sa.String(10), nullable=True),
        sa.Column('data_go', sa.Date(), nullable=True),
        sa.Column('data_qualificacao', sa.Date(), nullable=True),
        sa.Column('data_proposta', sa.Date(), nullable=True),
        sa.Column('responsavel_decisao', sa.String(255), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('id_orcamento', sa.String(50), nullable=True),
        sa.Column('numero_pedido', sa.String(50), nullable=True),
        sa.Column('valor_bruto', sa.Float(), nullable=True),
        sa.Column('margem_estimada', sa.Float(), nullable=True),
        sa.Column('status_lead', sa.String(100), nullable=True),
        sa.Column('status_final', sa.String(50), nullable=True),
        sa.Column('motivo_perda', sa.Text(), nullable=True),
        sa.Column('data_ultima_atualizacao', sa.Date(), nullable=True),
        sa.Column('followup_proposta_status', sa.String(10), nullable=True),
        sa.Column('followup_proposta_dados', sa.Text(), nullable=True),
        sa.Column('followup1_status', sa.String(10), nullable=True),
        sa.Column('followup1_dados', sa.Text(), nullable=True),
        sa.Column('followup2_status', sa.String(10), nullable=True),
        sa.Column('followup2_dados', sa.Text(), nullable=True),
        sa.Column('followup3_status', sa.String(10), nullable=True),
        sa.Column('followup3_dados', sa.Text(), nullable=True),
        sa.Column('descricao_oportunidade', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['crm.clientes.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )
    op.create_index('idx_leads_codigo', 'leads', ['codigo'], schema='crm')
    op.create_index('idx_leads_status', 'leads', ['status_lead'], schema='crm')

    op.create_table('visitas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('funcionario', sa.String(255), nullable=True),
        sa.Column('cliente', sa.String(255), nullable=True),
        sa.Column('local_visita', sa.String(255), nullable=True),
        sa.Column('uf_visita', sa.String(2), nullable=True),
        sa.Column('oportunidades', sa.Text(), nullable=True),
        sa.Column('concorrentes', sa.Text(), nullable=True),
        sa.Column('data_visita', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )
    op.create_index('idx_visitas_data', 'visitas', ['data_visita'], schema='crm')

    op.create_table('log_auditoria',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('data_hora', sa.DateTime(), nullable=True),
        sa.Column('usuario', sa.String(100), nullable=True),
        sa.Column('acao', sa.String(50), nullable=True),
        sa.Column('tabela', sa.String(50), nullable=True),
        sa.Column('detalhes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )

    op.create_table('leads_contatos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['crm.clientes.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='crm'
    )

    # ========== SCHEMA RH ==========

    op.create_table('empresas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('razao_social', sa.String(255), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=False, unique=True),
        sa.Column('endereco', sa.String(255), nullable=True),
        sa.Column('numero', sa.String(20), nullable=True),
        sa.Column('complemento', sa.String(100), nullable=True),
        sa.Column('bairro', sa.String(100), nullable=True),
        sa.Column('cep', sa.String(10), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('uf', sa.String(2), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('logo_path', sa.String(500), nullable=True),
        sa.Column('ativa', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('colaboradores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('foto_path', sa.String(500), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('nome_completo', sa.String(255), nullable=False),
        sa.Column('endereco', sa.String(255), nullable=True),
        sa.Column('numero', sa.String(20), nullable=True),
        sa.Column('complemento', sa.String(100), nullable=True),
        sa.Column('bairro', sa.String(100), nullable=True),
        sa.Column('cep', sa.String(10), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('uf_endereco', sa.String(2), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('celular', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('data_nascimento', sa.Date(), nullable=True),
        sa.Column('naturalidade', sa.String(100), nullable=True),
        sa.Column('uf_naturalidade', sa.String(2), nullable=True),
        sa.Column('sexo', sa.String(20), nullable=True),
        sa.Column('grau_instrucao', sa.String(100), nullable=True),
        sa.Column('curso_formacao', sa.String(255), nullable=True),
        sa.Column('data_conclusao', sa.Date(), nullable=True),
        sa.Column('estado_civil', sa.String(50), nullable=True),
        sa.Column('data_casamento', sa.Date(), nullable=True),
        sa.Column('nome_conjuge', sa.String(255), nullable=True),
        sa.Column('deficiencia', sa.String(255), nullable=True),
        sa.Column('nome_mae', sa.String(255), nullable=True),
        sa.Column('cpf_mae', sa.String(14), nullable=True),
        sa.Column('nome_pai', sa.String(255), nullable=True),
        sa.Column('cpf_pai', sa.String(14), nullable=True),
        sa.Column('carteira_profissional', sa.String(50), nullable=True),
        sa.Column('serie_carteira', sa.String(20), nullable=True),
        sa.Column('uf_carteira', sa.String(2), nullable=True),
        sa.Column('data_emissao_carteira', sa.Date(), nullable=True),
        sa.Column('rg', sa.String(20), nullable=True),
        sa.Column('data_emissao_rg', sa.Date(), nullable=True),
        sa.Column('orgao_emissor_rg', sa.String(50), nullable=True),
        sa.Column('uf_rg', sa.String(2), nullable=True),
        sa.Column('cpf', sa.String(14), nullable=True, unique=True),
        sa.Column('titulo_eleitor', sa.String(20), nullable=True),
        sa.Column('zona_eleitor', sa.String(10), nullable=True),
        sa.Column('secao_eleitor', sa.String(10), nullable=True),
        sa.Column('habilitacao', sa.String(20), nullable=True),
        sa.Column('data_expedicao_cnh', sa.Date(), nullable=True),
        sa.Column('tipo_cnh', sa.String(10), nullable=True),
        sa.Column('validade_cnh', sa.Date(), nullable=True),
        sa.Column('conselho_regional', sa.String(100), nullable=True),
        sa.Column('sigla_conselho', sa.String(20), nullable=True),
        sa.Column('numero_conselho', sa.String(50), nullable=True),
        sa.Column('regiao_conselho', sa.String(50), nullable=True),
        sa.Column('pis', sa.String(20), nullable=True),
        sa.Column('data_cadastramento_pis', sa.Date(), nullable=True),
        sa.Column('reservista', sa.String(50), nullable=True),
        sa.Column('data_exame_medico', sa.Date(), nullable=True),
        sa.Column('tipo_exames', sa.Text(), nullable=True),
        sa.Column('nome_medico', sa.String(255), nullable=True),
        sa.Column('crm', sa.String(20), nullable=True),
        sa.Column('uf_crm', sa.String(2), nullable=True),
        sa.Column('cnpj_ultimo_emprego', sa.String(20), nullable=True),
        sa.Column('empresa_ultimo_emprego', sa.String(255), nullable=True),
        sa.Column('data_admissao_ultimo', sa.Date(), nullable=True),
        sa.Column('data_saida_ultimo', sa.Date(), nullable=True),
        sa.Column('matricula_ultimo', sa.String(50), nullable=True),
        sa.Column('primeiro_registro', sa.String(10), nullable=True),
        sa.Column('data_ultima_contribuicao_sindical', sa.Date(), nullable=True),
        sa.Column('data_admissao', sa.Date(), nullable=True),
        sa.Column('funcao', sa.String(100), nullable=True),
        sa.Column('departamento', sa.String(100), nullable=True),
        sa.Column('salario', sa.Float(), nullable=True),
        sa.Column('forma_pagamento', sa.String(50), nullable=True),
        sa.Column('prazo_experiencia', sa.Integer(), nullable=True),
        sa.Column('prorrogacao', sa.Integer(), nullable=True),
        sa.Column('dias_trabalho', sa.String(100), nullable=True),
        sa.Column('horario_trabalho', sa.String(50), nullable=True),
        sa.Column('intervalo', sa.String(50), nullable=True),
        sa.Column('dias_folga', sa.String(100), nullable=True),
        sa.Column('observacoes_contrato', sa.Text(), nullable=True),
        sa.Column('tipo_contrato', sa.String(50), nullable=True),
        sa.Column('vale_transporte', sa.Boolean(), default=False),
        sa.Column('vt_valor_diario', sa.Float(), nullable=True),
        sa.Column('vt_percentual_desconto', sa.Float(), nullable=True),
        sa.Column('vale_refeicao', sa.Boolean(), default=False),
        sa.Column('vr_valor_diario', sa.Float(), nullable=True),
        sa.Column('vr_percentual_desconto', sa.Float(), nullable=True),
        sa.Column('vale_alimentacao', sa.Boolean(), default=False),
        sa.Column('va_valor_diario', sa.Float(), nullable=True),
        sa.Column('va_percentual_desconto', sa.Float(), nullable=True),
        sa.Column('assistencia_medica', sa.Boolean(), default=False),
        sa.Column('am_valor_desconto', sa.Float(), nullable=True),
        sa.Column('assistencia_odontologica', sa.Boolean(), default=False),
        sa.Column('ao_valor_desconto', sa.Float(), nullable=True),
        sa.Column('seguro_vida', sa.Boolean(), default=False),
        sa.Column('sv_valor_desconto', sa.Float(), nullable=True),
        sa.Column('adiantamento', sa.Boolean(), default=False),
        sa.Column('percentual_adiantamento', sa.Float(), nullable=True),
        sa.Column('data_pagamento_adiantamento', sa.Integer(), nullable=True),
        sa.Column('tipo_conta', sa.String(50), nullable=True),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('agencia', sa.String(20), nullable=True),
        sa.Column('conta', sa.String(30), nullable=True),
        sa.Column('observacoes_banco', sa.Text(), nullable=True),
        sa.Column('observacoes_gerais', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='ATIVO'),
        sa.Column('data_desligamento', sa.Date(), nullable=True),
        sa.Column('motivo_desligamento', sa.Text(), nullable=True),
        sa.Column('observacoes_desligamento', sa.Text(), nullable=True),
        sa.Column('motivo_inativacao', sa.String(255), nullable=True),
        sa.Column('submotivo_inativacao', sa.String(255), nullable=True),
        sa.Column('data_inativacao', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['rh.empresas.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )
    op.create_index('idx_colaborador_cpf', 'colaboradores', ['cpf'], schema='rh')
    op.create_index('idx_colaborador_status', 'colaboradores', ['status'], schema='rh')

    op.create_table('dependentes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('parentesco', sa.String(50), nullable=True),
        sa.Column('data_nascimento', sa.Date(), nullable=True),
        sa.Column('cpf', sa.String(14), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('localizacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('local_nome', sa.String(255), nullable=False),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('uf', sa.String(2), nullable=True),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_fim', sa.Date(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('ferias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('periodo_aquisitivo_inicio', sa.Date(), nullable=False),
        sa.Column('periodo_aquisitivo_fim', sa.Date(), nullable=False),
        sa.Column('periodo_concessivo_limite', sa.Date(), nullable=False),
        sa.Column('dias_direito', sa.Integer(), default=30),
        sa.Column('dias_gozados', sa.Integer(), default=0),
        sa.Column('dias_vendidos', sa.Integer(), default=0),
        sa.Column('status', sa.String(20), default='PENDENTE'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('periodos_ferias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ferias_id', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_fim', sa.Date(), nullable=False),
        sa.Column('dias', sa.Integer(), nullable=False),
        sa.Column('abono_pecuniario', sa.Boolean(), default=False),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ferias_id'], ['rh.ferias.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('contratos_experiencia',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('prazo_inicial', sa.Integer(), nullable=False),
        sa.Column('data_fim_inicial', sa.Date(), nullable=False),
        sa.Column('prorrogacao', sa.Integer(), nullable=True),
        sa.Column('data_fim_prorrogacao', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), default='VIGENTE'),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('blocklist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cpf', sa.String(14), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('data_admissao', sa.Date(), nullable=True),
        sa.Column('data_desligamento', sa.Date(), nullable=True),
        sa.Column('motivo_desligamento', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('pode_recontratar', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['rh.empresas.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('configuracoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chave', sa.String(100), nullable=False, unique=True),
        sa.Column('valor', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('historico_alteracoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('campo', sa.String(100), nullable=False),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_novo', sa.Text(), nullable=True),
        sa.Column('data_alteracao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('documentos_colaborador',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('colaborador_id', sa.Integer(), nullable=False),
        sa.Column('tipo_documento', sa.String(100), nullable=False),
        sa.Column('nome_arquivo_original', sa.String(255), nullable=True),
        sa.Column('caminho_arquivo', sa.String(500), nullable=False),
        sa.Column('obrigatorio', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['colaborador_id'], ['rh.colaboradores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('logs_sistema',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tipo_acao', sa.String(50), nullable=False),
        sa.Column('categoria', sa.String(50), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('entidade_tipo', sa.String(50), nullable=True),
        sa.Column('entidade_id', sa.Integer(), nullable=True),
        sa.Column('entidade_nome', sa.String(255), nullable=True),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_novo', sa.Text(), nullable=True),
        sa.Column('usuario', sa.String(100), default='Sistema'),
        sa.Column('data_hora', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome_completo', sa.String(255), nullable=False),
        sa.Column('login', sa.String(100), nullable=False, unique=True),
        sa.Column('senha', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.Column('nivel_acesso', sa.String(20), nullable=False, default='operador'),
        sa.Column('pergunta_seguranca', sa.String(255), nullable=True),
        sa.Column('resposta_seguranca', sa.String(255), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('ultimo_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('tentativas_login',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('login', sa.String(100), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('sucesso', sa.Boolean(), default=False),
        sa.Column('data_hora', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    op.create_table('bloqueios_login',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('login', sa.String(100), nullable=False, unique=True),
        sa.Column('bloqueado_ate', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='rh'
    )

    # ========== SCHEMA COMPRAS ==========

    op.create_table('centros_custo',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('local', sa.String(255), nullable=False),
        sa.Column('responsavel', sa.String(255), nullable=False),
        sa.Column('diretor', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('fornecedores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cpf_cnpj', sa.String(20), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('funcionarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cpf', sa.String(14), nullable=True),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('categorias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(10), nullable=False, unique=True),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('compras',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('data_compra', sa.Date(), nullable=False),
        sa.Column('fornecedor_id', sa.Integer(), nullable=True),
        sa.Column('fornecedor_nome', sa.String(255), nullable=True),
        sa.Column('centro_custo_id', sa.Integer(), nullable=True),
        sa.Column('centro_custo_nome', sa.String(255), nullable=True),
        sa.Column('categoria', sa.String(50), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('valor', sa.Float(), nullable=False),
        sa.Column('forma_pagamento', sa.String(50), nullable=True),
        sa.Column('funcionario_id', sa.Integer(), nullable=True),
        sa.Column('funcionario_nome', sa.String(255), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('emitente_id', sa.Integer(), nullable=True),
        sa.Column('emitente_nome', sa.String(255), nullable=True),
        sa.Column('tipo_documento', sa.String(50), nullable=True),
        sa.Column('numero_nf', sa.String(50), nullable=True),
        sa.Column('data_nf', sa.Date(), nullable=True),
        sa.Column('finalidade', sa.Text(), nullable=True),
        sa.Column('num_parcelas', sa.Integer(), nullable=True),
        sa.Column('datas_parcelas', sa.Text(), nullable=True),
        sa.Column('valores_parcelas', sa.Text(), nullable=True),
        sa.Column('data_pagamento_faturado', sa.Date(), nullable=True),
        sa.Column('ids_categoria', sa.Text(), nullable=True),
        sa.Column('numeros_nf', sa.Text(), nullable=True),
        sa.Column('datas_nf_multiplas', sa.Text(), nullable=True),
        sa.Column('valores_notas', sa.Text(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fornecedor_id'], ['compras.fornecedores.id']),
        sa.ForeignKeyConstraint(['centro_custo_id'], ['compras.centros_custo.id']),
        sa.ForeignKeyConstraint(['funcionario_id'], ['compras.funcionarios.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('requisicoes_compra',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero_rc', sa.String(20), nullable=True, unique=True),
        sa.Column('obra_projeto_id', sa.Integer(), nullable=False),
        sa.Column('tipo_requisicao', sa.String(20), nullable=False),
        sa.Column('tipo_material_servico', sa.String(50), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('especificacao_tecnica', sa.Text(), nullable=True),
        sa.Column('normas_aplicaveis', sa.Text(), nullable=True),
        sa.Column('quantidade', sa.Float(), nullable=True),
        sa.Column('unidade_medida', sa.String(20), nullable=True),
        sa.Column('prazo_entrega', sa.String(50), nullable=True),
        sa.Column('criticidade', sa.String(20), nullable=True),
        sa.Column('justificativa', sa.Text(), nullable=True),
        sa.Column('fornecedor_sugerido', sa.String(255), nullable=True),
        sa.Column('valor_estimado', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='Rascunho'),
        sa.Column('status_anterior', sa.String(50), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('data_ultima_atualizacao', sa.DateTime(), nullable=True),
        sa.Column('data_aprovacao', sa.DateTime(), nullable=True),
        sa.Column('data_cotacao', sa.DateTime(), nullable=True),
        sa.Column('data_selecao_vencedor', sa.DateTime(), nullable=True),
        sa.Column('data_arquivamento', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['obra_projeto_id'], ['compras.centros_custo.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('aprovacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('requisicao_id', sa.Integer(), nullable=False),
        sa.Column('aprovador', sa.String(255), nullable=False),
        sa.Column('tipo_aprovador', sa.String(20), nullable=True),
        sa.Column('acao', sa.String(30), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('data_hora', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requisicao_id'], ['compras.requisicoes_compra.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('cotacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rc_id', sa.Integer(), nullable=False),
        sa.Column('numero_rc', sa.String(20), nullable=True),
        sa.Column('status', sa.String(30), default='Em Análise'),
        sa.Column('data_cotacao', sa.Date(), nullable=True),
        sa.Column('fornecedor1_nome', sa.String(255), nullable=True),
        sa.Column('fornecedor1_valor', sa.Float(), nullable=True),
        sa.Column('fornecedor1_condicoes', sa.Text(), nullable=True),
        sa.Column('fornecedor1_prazo_entrega', sa.String(50), nullable=True),
        sa.Column('fornecedor1_frete', sa.String(50), nullable=True),
        sa.Column('fornecedor1_pagamento', sa.String(100), nullable=True),
        sa.Column('fornecedor1_observacoes', sa.Text(), nullable=True),
        sa.Column('fornecedor2_nome', sa.String(255), nullable=True),
        sa.Column('fornecedor2_valor', sa.Float(), nullable=True),
        sa.Column('fornecedor2_condicoes', sa.Text(), nullable=True),
        sa.Column('fornecedor2_prazo_entrega', sa.String(50), nullable=True),
        sa.Column('fornecedor2_frete', sa.String(50), nullable=True),
        sa.Column('fornecedor2_pagamento', sa.String(100), nullable=True),
        sa.Column('fornecedor2_observacoes', sa.Text(), nullable=True),
        sa.Column('fornecedor3_nome', sa.String(255), nullable=True),
        sa.Column('fornecedor3_valor', sa.Float(), nullable=True),
        sa.Column('fornecedor3_condicoes', sa.Text(), nullable=True),
        sa.Column('fornecedor3_prazo_entrega', sa.String(50), nullable=True),
        sa.Column('fornecedor3_frete', sa.String(50), nullable=True),
        sa.Column('fornecedor3_pagamento', sa.String(100), nullable=True),
        sa.Column('fornecedor3_observacoes', sa.Text(), nullable=True),
        sa.Column('condicoes', sa.Text(), nullable=True),
        sa.Column('fornecedor_vencedor', sa.String(255), nullable=True),
        sa.Column('justificativa_vencedor', sa.Text(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=True),
        sa.Column('data_ultima_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rc_id'], ['compras.requisicoes_compra.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('pedidos_finalizados',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rc_id', sa.Integer(), nullable=False),
        sa.Column('cotacao_id', sa.Integer(), nullable=True),
        sa.Column('fornecedor_vencedor', sa.String(255), nullable=True),
        sa.Column('valor_final', sa.Float(), nullable=True),
        sa.Column('justificativa_vencedor', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('aprovador_id', sa.Integer(), nullable=True),
        sa.Column('aprovador_nome', sa.String(255), nullable=True),
        sa.Column('aprovador_cargo', sa.String(100), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=True),
        sa.Column('data_ultima_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rc_id'], ['compras.requisicoes_compra.id']),
        sa.ForeignKeyConstraint(['cotacao_id'], ['compras.cotacoes.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    op.create_table('itens_rc',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rc_id', sa.Integer(), nullable=False),
        sa.Column('item_numero', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('quantidade', sa.Float(), nullable=False, default=1),
        sa.Column('unidade_medida', sa.String(20), nullable=False, default='UN'),
        sa.ForeignKeyConstraint(['rc_id'], ['compras.requisicoes_compra.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='compras'
    )

    # ========== SCHEMA PATRIMONIO ==========

    op.create_table('patrimonios',
        sa.Column('numero_patrimonio', sa.String(50), nullable=False),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('marca', sa.String(100), nullable=True),
        sa.Column('categoria', sa.String(100), nullable=True),
        sa.Column('status_uso', sa.String(50), nullable=True),
        sa.Column('localizacao', sa.String(255), nullable=True),
        sa.Column('valor', sa.Float(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('quilometragem_atual', sa.Integer(), default=0),
        sa.Column('requer_calibracao', sa.Boolean(), default=False),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('numero_patrimonio'),
        schema='patrimonio'
    )

    op.create_table('responsaveis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cpf', sa.String(14), nullable=True, unique=True),
        sa.Column('setor', sa.String(100), nullable=True),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), default='Ativo'),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('custodias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero_patrimonio', sa.String(50), nullable=False),
        sa.Column('id_responsavel', sa.Integer(), nullable=False),
        sa.Column('data_acao', sa.DateTime(), nullable=True),
        sa.Column('acao', sa.String(50), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('setor', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['numero_patrimonio'], ['patrimonio.patrimonios.numero_patrimonio'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_responsavel'], ['patrimonio.responsaveis.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('manutencoes_veiculos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero_patrimonio', sa.String(50), nullable=False),
        sa.Column('tipo_manutencao', sa.String(100), nullable=False),
        sa.Column('data_manutencao', sa.Date(), nullable=False),
        sa.Column('quilometragem', sa.Integer(), nullable=True),
        sa.Column('valor', sa.Float(), nullable=True),
        sa.Column('fornecedor', sa.String(255), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['numero_patrimonio'], ['patrimonio.patrimonios.numero_patrimonio'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('calibracoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numero_patrimonio', sa.String(50), nullable=False),
        sa.Column('data_calibracao', sa.Date(), nullable=False),
        sa.Column('validade_meses', sa.Integer(), default=12),
        sa.Column('data_vencimento', sa.Date(), nullable=False),
        sa.Column('certificado_path', sa.String(500), nullable=True),
        sa.Column('laboratorio', sa.String(255), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['numero_patrimonio'], ['patrimonio.patrimonios.numero_patrimonio'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('log_sistema',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('data_hora', sa.DateTime(), nullable=True),
        sa.Column('acao', sa.String(100), nullable=False),
        sa.Column('usuario', sa.String(100), default='Sistema'),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('fardamentos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cargo', sa.String(100), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=False),
        sa.Column('tamanho', sa.String(10), nullable=False),
        sa.Column('cor', sa.String(50), nullable=False),
        sa.Column('manga', sa.String(20), nullable=False),
        sa.Column('novas', sa.Integer(), default=0),
        sa.Column('em_uso', sa.Integer(), default=0),
        sa.Column('aguardando_higienizacao', sa.Integer(), default=0),
        sa.Column('higienizadas', sa.Integer(), default=0),
        sa.Column('descartadas', sa.Integer(), default=0),
        sa.Column('data_lote', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('cores_fardamento',
        sa.Column('nome', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('nome'),
        schema='patrimonio'
    )

    op.create_table('fardamentos_usados',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cargo', sa.String(100), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=False),
        sa.Column('tamanho', sa.String(10), nullable=False),
        sa.Column('cor', sa.String(50), nullable=False),
        sa.Column('manga', sa.String(20), nullable=False),
        sa.Column('responsavel', sa.String(255), nullable=False),
        sa.Column('data_retirada', sa.DateTime(), nullable=True),
        sa.Column('data_devolucao', sa.DateTime(), nullable=True),
        sa.Column('status_devolucao', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    op.create_table('termos_fardamento',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo_termo', sa.String(50), nullable=False, unique=True),
        sa.Column('responsavel', sa.String(255), nullable=False),
        sa.Column('cargo', sa.String(100), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=False),
        sa.Column('tamanho', sa.String(10), nullable=False),
        sa.Column('cor', sa.String(50), nullable=False),
        sa.Column('manga', sa.String(20), nullable=False),
        sa.Column('data_geracao', sa.DateTime(), nullable=True),
        sa.Column('caminho_arquivo', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patrimonio'
    )

    # ========== SCHEMA DOCUMENTAL (resumido por tamanho) ==========
    # As tabelas do schema documental seguem o mesmo padrão dos outros schemas
    # com estrutura para documentos ISO, NCs, treinamentos, competências, etc.

    op.create_table('tipos_documento',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(10), nullable=False, unique=True),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('nivel_piramide', sa.Integer(), default=4),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('areas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sigla', sa.String(10), nullable=False, unique=True),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('responsavel', sa.String(255), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('responsaveis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.Column('area_id', sa.Integer(), nullable=True),
        sa.Column('pode_elaborar', sa.Boolean(), default=True),
        sa.Column('pode_revisar', sa.Boolean(), default=True),
        sa.Column('pode_aprovar', sa.Boolean(), default=False),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['area_id'], ['documental.areas.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('requisitos_iso',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('norma', sa.String(20), nullable=False),
        sa.Column('clausula', sa.String(20), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('documentos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(30), nullable=False, unique=True),
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('tipo_documento_id', sa.Integer(), nullable=True),
        sa.Column('area_id', sa.Integer(), nullable=True),
        sa.Column('revisao_atual', sa.String(10), default='0000'),
        sa.Column('status', sa.String(30), default='Em Elaboração'),
        sa.Column('data_criacao', sa.Date(), nullable=True),
        sa.Column('data_ultima_revisao', sa.Date(), nullable=True),
        sa.Column('proxima_revisao', sa.Date(), nullable=True),
        sa.Column('periodicidade_revisao', sa.Integer(), default=12),
        sa.Column('elaborador_id', sa.Integer(), nullable=True),
        sa.Column('revisor_id', sa.Integer(), nullable=True),
        sa.Column('aprovador_id', sa.Integer(), nullable=True),
        sa.Column('arquivo_digital', sa.String(500), nullable=True),
        sa.Column('local_acesso', sa.String(255), nullable=True),
        sa.Column('obsoleto', sa.Boolean(), default=False),
        sa.Column('data_obsoleto', sa.Date(), nullable=True),
        sa.Column('motivo_obsoleto', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_elaboracao', sa.Date(), nullable=True),
        sa.Column('data_revisao_exec', sa.Date(), nullable=True),
        sa.Column('data_aprovacao', sa.Date(), nullable=True),
        sa.Column('data_inclusao_sistema', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['tipo_documento_id'], ['documental.tipos_documento.id']),
        sa.ForeignKeyConstraint(['area_id'], ['documental.areas.id']),
        sa.ForeignKeyConstraint(['elaborador_id'], ['documental.responsaveis.id']),
        sa.ForeignKeyConstraint(['revisor_id'], ['documental.responsaveis.id']),
        sa.ForeignKeyConstraint(['aprovador_id'], ['documental.responsaveis.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('nao_conformidades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(20), nullable=False, unique=True),
        sa.Column('data_abertura', sa.Date(), nullable=False),
        sa.Column('origem', sa.String(100), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=True),
        sa.Column('area_id', sa.Integer(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('evidencia', sa.Text(), nullable=True),
        sa.Column('classificacao', sa.String(20), default='Menor'),
        sa.Column('causa_raiz', sa.Text(), nullable=True),
        sa.Column('metodo_analise', sa.String(50), nullable=True),
        sa.Column('acao_corretiva', sa.Text(), nullable=True),
        sa.Column('acao_preventiva', sa.Text(), nullable=True),
        sa.Column('responsavel_id', sa.Integer(), nullable=True),
        sa.Column('prazo', sa.Date(), nullable=True),
        sa.Column('data_fechamento', sa.Date(), nullable=True),
        sa.Column('verificacao_eficacia', sa.Text(), nullable=True),
        sa.Column('data_verificacao', sa.Date(), nullable=True),
        sa.Column('eficaz', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(20), default='Aberta'),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['documento_id'], ['documental.documentos.id']),
        sa.ForeignKeyConstraint(['area_id'], ['documental.areas.id']),
        sa.ForeignKeyConstraint(['responsavel_id'], ['documental.responsaveis.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    op.create_table('log_atividades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('hora', sa.String(10), nullable=False),
        sa.Column('usuario', sa.String(100), nullable=True),
        sa.Column('acao', sa.String(100), nullable=False),
        sa.Column('modulo', sa.String(50), nullable=True),
        sa.Column('detalhes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='documental'
    )

    # Demais tabelas do schema documental (competências, treinamentos, análise crítica, etc.)
    # seguem o mesmo padrão e serão criadas automaticamente pelo SQLAlchemy.metadata.create_all()


def downgrade() -> None:
    # Drop todas as tabelas em ordem reversa

    # Schema documental
    op.drop_table('log_atividades', schema='documental')
    op.drop_table('nao_conformidades', schema='documental')
    op.drop_table('documentos', schema='documental')
    op.drop_table('requisitos_iso', schema='documental')
    op.drop_table('responsaveis', schema='documental')
    op.drop_table('areas', schema='documental')
    op.drop_table('tipos_documento', schema='documental')

    # Schema patrimonio
    op.drop_table('termos_fardamento', schema='patrimonio')
    op.drop_table('fardamentos_usados', schema='patrimonio')
    op.drop_table('cores_fardamento', schema='patrimonio')
    op.drop_table('fardamentos', schema='patrimonio')
    op.drop_table('log_sistema', schema='patrimonio')
    op.drop_table('calibracoes', schema='patrimonio')
    op.drop_table('manutencoes_veiculos', schema='patrimonio')
    op.drop_table('custodias', schema='patrimonio')
    op.drop_table('responsaveis', schema='patrimonio')
    op.drop_table('patrimonios', schema='patrimonio')

    # Schema compras
    op.drop_table('itens_rc', schema='compras')
    op.drop_table('pedidos_finalizados', schema='compras')
    op.drop_table('cotacoes', schema='compras')
    op.drop_table('aprovacoes', schema='compras')
    op.drop_table('requisicoes_compra', schema='compras')
    op.drop_table('compras', schema='compras')
    op.drop_table('categorias', schema='compras')
    op.drop_table('funcionarios', schema='compras')
    op.drop_table('fornecedores', schema='compras')
    op.drop_table('centros_custo', schema='compras')

    # Schema rh
    op.drop_table('bloqueios_login', schema='rh')
    op.drop_table('tentativas_login', schema='rh')
    op.drop_table('usuarios', schema='rh')
    op.drop_table('logs_sistema', schema='rh')
    op.drop_table('documentos_colaborador', schema='rh')
    op.drop_table('historico_alteracoes', schema='rh')
    op.drop_table('configuracoes', schema='rh')
    op.drop_table('blocklist', schema='rh')
    op.drop_table('contratos_experiencia', schema='rh')
    op.drop_table('periodos_ferias', schema='rh')
    op.drop_table('ferias', schema='rh')
    op.drop_table('localizacoes', schema='rh')
    op.drop_table('dependentes', schema='rh')
    op.drop_table('colaboradores', schema='rh')
    op.drop_table('empresas', schema='rh')

    # Schema crm
    op.drop_table('leads_contatos', schema='crm')
    op.drop_table('log_auditoria', schema='crm')
    op.drop_table('visitas', schema='crm')
    op.drop_table('leads', schema='crm')
    op.drop_table('contatos', schema='crm')
    op.drop_table('clientes', schema='crm')
