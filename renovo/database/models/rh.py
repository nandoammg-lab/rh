"""
Models SQLAlchemy - Módulo RH (Sistema de Gestão de Recursos Humanos)
Schema: rh
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class Empresa(Base):
    """Tabela de empresas contratantes"""
    __tablename__ = 'empresas'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=False)
    endereco = Column(String(255))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    cep = Column(String(10))
    cidade = Column(String(100))
    uf = Column(String(2))
    telefone = Column(String(20))
    email = Column(String(255))
    logo_path = Column(String(500))
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    colaboradores = relationship('Colaborador', back_populates='empresa')
    blocklist = relationship('Blocklist', back_populates='empresa')


class Colaborador(Base):
    """Tabela principal de colaboradores"""
    __tablename__ = 'colaboradores'
    __table_args__ = (
        Index('idx_colaborador_cpf', 'cpf'),
        Index('idx_colaborador_status', 'status'),
        {'schema': 'rh'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foto
    foto_path = Column(String(500))

    # Empresa Contratante
    empresa_id = Column(Integer, ForeignKey('rh.empresas.id'))

    # Dados Pessoais
    nome_completo = Column(String(255), nullable=False)
    endereco = Column(String(255))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    cep = Column(String(10))
    cidade = Column(String(100))
    uf_endereco = Column(String(2))
    telefone = Column(String(20))
    celular = Column(String(20))
    email = Column(String(255))
    data_nascimento = Column(Date)
    naturalidade = Column(String(100))
    uf_naturalidade = Column(String(2))
    sexo = Column(String(20))
    grau_instrucao = Column(String(100))
    curso_formacao = Column(String(255))
    data_conclusao = Column(Date)
    estado_civil = Column(String(50))
    data_casamento = Column(Date)
    nome_conjuge = Column(String(255))
    deficiencia = Column(String(255))
    nome_mae = Column(String(255))
    cpf_mae = Column(String(14))
    nome_pai = Column(String(255))
    cpf_pai = Column(String(14))

    # Documentos
    carteira_profissional = Column(String(50))
    serie_carteira = Column(String(20))
    uf_carteira = Column(String(2))
    data_emissao_carteira = Column(Date)
    rg = Column(String(20))
    data_emissao_rg = Column(Date)
    orgao_emissor_rg = Column(String(50))
    uf_rg = Column(String(2))
    cpf = Column(String(14), unique=True)
    titulo_eleitor = Column(String(20))
    zona_eleitor = Column(String(10))
    secao_eleitor = Column(String(10))
    habilitacao = Column(String(20))
    data_expedicao_cnh = Column(Date)
    tipo_cnh = Column(String(10))
    validade_cnh = Column(Date)
    conselho_regional = Column(String(100))
    sigla_conselho = Column(String(20))
    numero_conselho = Column(String(50))
    regiao_conselho = Column(String(50))
    pis = Column(String(20))
    data_cadastramento_pis = Column(Date)
    reservista = Column(String(50))

    # Exame Médico
    data_exame_medico = Column(Date)
    tipo_exames = Column(Text)
    nome_medico = Column(String(255))
    crm = Column(String(20))
    uf_crm = Column(String(2))

    # Dados Último Registro
    cnpj_ultimo_emprego = Column(String(20))
    empresa_ultimo_emprego = Column(String(255))
    data_admissao_ultimo = Column(Date)
    data_saida_ultimo = Column(Date)
    matricula_ultimo = Column(String(50))
    primeiro_registro = Column(String(10))
    data_ultima_contribuicao_sindical = Column(Date)

    # Dados da Empresa Atual
    data_admissao = Column(Date)
    funcao = Column(String(100))
    departamento = Column(String(100))
    salario = Column(Float)
    forma_pagamento = Column(String(50))
    prazo_experiencia = Column(Integer)
    prorrogacao = Column(Integer)
    dias_trabalho = Column(String(100))
    horario_trabalho = Column(String(50))
    intervalo = Column(String(50))
    dias_folga = Column(String(100))
    observacoes_contrato = Column(Text)
    tipo_contrato = Column(String(50))

    # Benefícios
    vale_transporte = Column(Boolean, default=False)
    vt_valor_diario = Column(Float)
    vt_percentual_desconto = Column(Float)
    vale_refeicao = Column(Boolean, default=False)
    vr_valor_diario = Column(Float)
    vr_percentual_desconto = Column(Float)
    vale_alimentacao = Column(Boolean, default=False)
    va_valor_diario = Column(Float)
    va_percentual_desconto = Column(Float)
    assistencia_medica = Column(Boolean, default=False)
    am_valor_desconto = Column(Float)
    assistencia_odontologica = Column(Boolean, default=False)
    ao_valor_desconto = Column(Float)
    seguro_vida = Column(Boolean, default=False)
    sv_valor_desconto = Column(Float)
    adiantamento = Column(Boolean, default=False)
    percentual_adiantamento = Column(Float)
    data_pagamento_adiantamento = Column(Integer)

    # Dados Bancários
    tipo_conta = Column(String(50))
    banco = Column(String(100))
    agencia = Column(String(20))
    conta = Column(String(30))
    observacoes_banco = Column(Text)

    # Observações Gerais
    observacoes_gerais = Column(Text)

    # Status
    status = Column(String(20), default='ATIVO')
    data_desligamento = Column(Date)
    motivo_desligamento = Column(Text)
    observacoes_desligamento = Column(Text)
    motivo_inativacao = Column(String(255))
    submotivo_inativacao = Column(String(255))
    data_inativacao = Column(Date)

    # Controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    empresa = relationship('Empresa', back_populates='colaboradores')
    dependentes = relationship('Dependente', back_populates='colaborador', cascade='all, delete-orphan')
    localizacoes = relationship('Localizacao', back_populates='colaborador', cascade='all, delete-orphan')
    ferias = relationship('Ferias', back_populates='colaborador', cascade='all, delete-orphan')
    contratos_experiencia = relationship('ContratoExperiencia', back_populates='colaborador', cascade='all, delete-orphan')
    historico_alteracoes = relationship('HistoricoAlteracao', back_populates='colaborador', cascade='all, delete-orphan')
    documentos = relationship('DocumentoColaborador', back_populates='colaborador', cascade='all, delete-orphan')


class Dependente(Base):
    """Tabela de dependentes dos colaboradores"""
    __tablename__ = 'dependentes'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    nome = Column(String(255), nullable=False)
    parentesco = Column(String(50))
    data_nascimento = Column(Date)
    cpf = Column(String(14))
    created_at = Column(DateTime, default=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='dependentes')


class Localizacao(Base):
    """Tabela de localizações (alocações de colaboradores)"""
    __tablename__ = 'localizacoes'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    local_nome = Column(String(255), nullable=False)
    cidade = Column(String(100))
    uf = Column(String(2))
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    observacoes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='localizacoes')


class Ferias(Base):
    """Tabela de férias"""
    __tablename__ = 'ferias'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    periodo_aquisitivo_inicio = Column(Date, nullable=False)
    periodo_aquisitivo_fim = Column(Date, nullable=False)
    periodo_concessivo_limite = Column(Date, nullable=False)
    dias_direito = Column(Integer, default=30)
    dias_gozados = Column(Integer, default=0)
    dias_vendidos = Column(Integer, default=0)
    status = Column(String(20), default='PENDENTE')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='ferias')
    periodos = relationship('PeriodoFerias', back_populates='ferias', cascade='all, delete-orphan')


class PeriodoFerias(Base):
    """Tabela de períodos de férias (fracionamento)"""
    __tablename__ = 'periodos_ferias'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    ferias_id = Column(Integer, ForeignKey('rh.ferias.id', ondelete='CASCADE'), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    dias = Column(Integer, nullable=False)
    abono_pecuniario = Column(Boolean, default=False)
    observacoes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # Relacionamentos
    ferias = relationship('Ferias', back_populates='periodos')


class ContratoExperiencia(Base):
    """Tabela de contratos de experiência"""
    __tablename__ = 'contratos_experiencia'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    data_inicio = Column(Date, nullable=False)
    prazo_inicial = Column(Integer, nullable=False)
    data_fim_inicial = Column(Date, nullable=False)
    prorrogacao = Column(Integer)
    data_fim_prorrogacao = Column(Date)
    status = Column(String(20), default='VIGENTE')
    observacoes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='contratos_experiencia')


class Blocklist(Base):
    """Tabela de blocklist (ex-funcionários)"""
    __tablename__ = 'blocklist'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(14), nullable=False)
    nome = Column(String(255), nullable=False)
    empresa_id = Column(Integer, ForeignKey('rh.empresas.id'))
    data_admissao = Column(Date)
    data_desligamento = Column(Date)
    motivo_desligamento = Column(Text)
    observacoes = Column(Text)
    pode_recontratar = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relacionamentos
    empresa = relationship('Empresa', back_populates='blocklist')


class Configuracao(Base):
    """Tabela de configurações do sistema"""
    __tablename__ = 'configuracoes'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HistoricoAlteracao(Base):
    """Tabela de histórico de alterações"""
    __tablename__ = 'historico_alteracoes'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    campo = Column(String(100), nullable=False)
    valor_anterior = Column(Text)
    valor_novo = Column(Text)
    data_alteracao = Column(DateTime, default=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='historico_alteracoes')


class DocumentoColaborador(Base):
    """Tabela de documentos do colaborador"""
    __tablename__ = 'documentos_colaborador'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('rh.colaboradores.id', ondelete='CASCADE'), nullable=False)
    tipo_documento = Column(String(100), nullable=False)
    nome_arquivo_original = Column(String(255))
    caminho_arquivo = Column(String(500), nullable=False)
    obrigatorio = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    colaborador = relationship('Colaborador', back_populates='documentos')


class LogSistema(Base):
    """Tabela de logs do sistema"""
    __tablename__ = 'logs_sistema'
    __table_args__ = (
        Index('idx_log_data_hora', 'data_hora'),
        {'schema': 'rh'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_acao = Column(String(50), nullable=False)
    categoria = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=False)
    entidade_tipo = Column(String(50))
    entidade_id = Column(Integer)
    entidade_nome = Column(String(255))
    valor_anterior = Column(Text)
    valor_novo = Column(Text)
    usuario = Column(String(100), default='Sistema')
    data_hora = Column(DateTime, default=datetime.now)


class Usuario(Base):
    """Tabela de usuários do sistema"""
    __tablename__ = 'usuarios'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_completo = Column(String(255), nullable=False)
    login = Column(String(100), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    email = Column(String(255))
    cargo = Column(String(100))
    nivel_acesso = Column(String(20), nullable=False, default='operador')
    pergunta_seguranca = Column(String(255))
    resposta_seguranca = Column(String(255))
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TentativaLogin(Base):
    """Tabela de tentativas de login"""
    __tablename__ = 'tentativas_login'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(100), nullable=False)
    ip_address = Column(String(50))
    sucesso = Column(Boolean, default=False)
    data_hora = Column(DateTime, default=datetime.now)


class BloqueioLogin(Base):
    """Tabela de bloqueios de login"""
    __tablename__ = 'bloqueios_login'
    __table_args__ = {'schema': 'rh'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(100), unique=True, nullable=False)
    bloqueado_ate = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
