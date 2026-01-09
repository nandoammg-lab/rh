"""
Models SQLAlchemy - Módulo Documental (Sistema de Gestão Documental ISO)
Schema: documental
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class TipoDocumento(Base):
    """Tabela de tipos de documento (Pirâmide Documental)"""
    __tablename__ = 'tipos_documento'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    nivel_piramide = Column(Integer, default=4)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    documentos = relationship('Documento', back_populates='tipo_documento')


class Area(Base):
    """Tabela de áreas/departamentos"""
    __tablename__ = 'areas'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    sigla = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    responsavel = Column(String(255))
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    documentos = relationship('Documento', back_populates='area')
    responsaveis = relationship('ResponsavelDoc', back_populates='area')
    funcoes = relationship('Funcao', back_populates='area')
    colaboradores = relationship('ColaboradorDoc', back_populates='area')
    nao_conformidades = relationship('NaoConformidade', back_populates='area')
    objetivos = relationship('ObjetivoMeta', back_populates='area')
    riscos = relationship('RiscoOportunidade', back_populates='area')
    treinamentos = relationship('Treinamento', back_populates='area')


class ResponsavelDoc(Base):
    """Tabela de responsáveis/aprovadores"""
    __tablename__ = 'responsaveis'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cargo = Column(String(100))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    pode_elaborar = Column(Boolean, default=True)
    pode_revisar = Column(Boolean, default=True)
    pode_aprovar = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    area = relationship('Area', back_populates='responsaveis')


class RequisitoISO(Base):
    """Tabela de requisitos ISO"""
    __tablename__ = 'requisitos_iso'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    norma = Column(String(20), nullable=False)
    clausula = Column(String(20), nullable=False)
    descricao = Column(Text, nullable=False)

    # Relacionamentos
    documentos = relationship('DocumentoRequisito', back_populates='requisito')


class Documento(Base):
    """Tabela de documentos"""
    __tablename__ = 'documentos'
    __table_args__ = (
        Index('idx_documento_codigo', 'codigo'),
        Index('idx_documento_status', 'status'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(30), unique=True, nullable=False)
    titulo = Column(String(255), nullable=False)
    tipo_documento_id = Column(Integer, ForeignKey('documental.tipos_documento.id'))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    revisao_atual = Column(String(10), default='0000')
    status = Column(String(30), default='Em Elaboração')
    data_criacao = Column(Date)
    data_ultima_revisao = Column(Date)
    proxima_revisao = Column(Date)
    periodicidade_revisao = Column(Integer, default=12)
    elaborador_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    revisor_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    aprovador_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    arquivo_digital = Column(String(500))
    local_acesso = Column(String(255))
    obsoleto = Column(Boolean, default=False)
    data_obsoleto = Column(Date)
    motivo_obsoleto = Column(Text)
    observacoes = Column(Text)
    data_elaboracao = Column(Date)
    data_revisao_exec = Column(Date)
    data_aprovacao = Column(Date)
    data_inclusao_sistema = Column(Date)

    # Relacionamentos
    tipo_documento = relationship('TipoDocumento', back_populates='documentos')
    area = relationship('Area', back_populates='documentos')
    revisoes = relationship('Revisao', back_populates='documento', cascade='all, delete-orphan')
    requisitos = relationship('DocumentoRequisito', back_populates='documento', cascade='all, delete-orphan')
    registros = relationship('Registro', back_populates='documento')
    distribuicoes = relationship('DistribuicaoCopia', back_populates='documento', cascade='all, delete-orphan')
    nao_conformidades = relationship('NaoConformidade', back_populates='documento')
    objetivos = relationship('ObjetivoDocumento', back_populates='documento')


class Revisao(Base):
    """Tabela de revisões (histórico)"""
    __tablename__ = 'revisoes'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'), nullable=False)
    revisao_numero = Column(String(10), nullable=False)
    data_revisao = Column(Date)
    motivo_revisao = Column(Text)
    elaborador_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    revisor_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    aprovador_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    data_elaboracao = Column(Date)
    data_revisao_exec = Column(Date)
    data_aprovacao = Column(Date)
    arquivo_versao = Column(String(500))
    status = Column(String(30), default='Em Elaboração')
    observacoes = Column(Text)

    # Relacionamentos
    documento = relationship('Documento', back_populates='revisoes')


class DocumentoRequisito(Base):
    """Tabela de vinculação Documento-Requisito ISO"""
    __tablename__ = 'documento_requisito'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'), nullable=False)
    requisito_id = Column(Integer, ForeignKey('documental.requisitos_iso.id'), nullable=False)

    # Relacionamentos
    documento = relationship('Documento', back_populates='requisitos')
    requisito = relationship('RequisitoISO', back_populates='documentos')


class CategoriaRegistro(Base):
    """Tabela de categorias de registros"""
    __tablename__ = 'categorias_registro'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(Text)
    tempo_retencao_meses = Column(Integer, default=72)
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    registros = relationship('Registro', back_populates='categoria')


class Registro(Base):
    """Tabela de registros"""
    __tablename__ = 'registros'
    __table_args__ = (
        Index('idx_registro_codigo', 'codigo'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    titulo = Column(String(255), nullable=False)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'))
    categoria_id = Column(Integer, ForeignKey('documental.categorias_registro.id'))
    data_registro = Column(Date)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    arquivo_escaneado = Column(String(500))
    tags = Column(Text)
    data_criacao = Column(Date)
    data_descarte = Column(Date)
    descartado = Column(Boolean, default=False)
    observacoes = Column(Text)

    # Relacionamentos
    documento = relationship('Documento', back_populates='registros')
    categoria = relationship('CategoriaRegistro', back_populates='registros')


class LocalDistribuicao(Base):
    """Tabela de locais de distribuição"""
    __tablename__ = 'locais_distribuicao'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(Text)
    responsavel = Column(String(255))
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    distribuicoes = relationship('DistribuicaoCopia', back_populates='local')


class DistribuicaoCopia(Base):
    """Tabela de distribuição de cópias controladas"""
    __tablename__ = 'distribuicao_copias'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'), nullable=False)
    revisao = Column(String(10), nullable=False)
    local_id = Column(Integer, ForeignKey('documental.locais_distribuicao.id'), nullable=False)
    data_distribuicao = Column(Date)
    responsavel_distribuicao = Column(String(255))
    data_recolhimento = Column(Date)
    responsavel_recolhimento = Column(String(255))
    status = Column(String(20), default='Ativa')
    observacoes = Column(Text)

    # Relacionamentos
    documento = relationship('Documento', back_populates='distribuicoes')
    local = relationship('LocalDistribuicao', back_populates='distribuicoes')


class NaoConformidade(Base):
    """Tabela de não-conformidades"""
    __tablename__ = 'nao_conformidades'
    __table_args__ = (
        Index('idx_nc_codigo', 'codigo'),
        Index('idx_nc_status', 'status'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    data_abertura = Column(Date, nullable=False)
    origem = Column(String(100), nullable=False)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    descricao = Column(Text, nullable=False)
    evidencia = Column(Text)
    classificacao = Column(String(20), default='Menor')
    causa_raiz = Column(Text)
    metodo_analise = Column(String(50))
    acao_corretiva = Column(Text)
    acao_preventiva = Column(Text)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    prazo = Column(Date)
    data_fechamento = Column(Date)
    verificacao_eficacia = Column(Text)
    data_verificacao = Column(Date)
    eficaz = Column(Boolean)
    status = Column(String(20), default='Aberta')
    observacoes = Column(Text)

    # Relacionamentos
    documento = relationship('Documento', back_populates='nao_conformidades')
    area = relationship('Area', back_populates='nao_conformidades')
    riscos = relationship('RiscoNC', back_populates='nao_conformidade')


class LogAtividades(Base):
    """Tabela de log de atividades"""
    __tablename__ = 'log_atividades'
    __table_args__ = (
        Index('idx_log_doc_data', 'data'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    hora = Column(String(10), nullable=False)
    usuario = Column(String(100))
    acao = Column(String(100), nullable=False)
    modulo = Column(String(50))
    detalhes = Column(Text)


# ========== MÓDULOS ISO ADICIONAIS ==========

class ObjetivoMeta(Base):
    """Tabela de objetivos e metas (ISO 6.2)"""
    __tablename__ = 'objetivos_metas'
    __table_args__ = (
        Index('idx_objetivo_codigo', 'codigo'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    tipo = Column(String(30), default='Qualidade')
    perspectiva = Column(String(50))
    meta_valor = Column(Float)
    meta_unidade = Column(String(30))
    valor_atual = Column(Float, default=0)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    status = Column(String(30), default='Em Andamento')
    observacoes = Column(Text)

    # Relacionamentos
    area = relationship('Area', back_populates='objetivos')
    acompanhamentos = relationship('ObjetivoAcompanhamento', back_populates='objetivo', cascade='all, delete-orphan')
    documentos = relationship('ObjetivoDocumento', back_populates='objetivo')


class ObjetivoAcompanhamento(Base):
    """Tabela de acompanhamento de objetivos"""
    __tablename__ = 'objetivos_acompanhamento'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    objetivo_id = Column(Integer, ForeignKey('documental.objetivos_metas.id'), nullable=False)
    data_medicao = Column(Date, nullable=False)
    valor_medido = Column(Float)
    observacoes = Column(Text)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))

    # Relacionamentos
    objetivo = relationship('ObjetivoMeta', back_populates='acompanhamentos')


class ObjetivoDocumento(Base):
    """Tabela de vinculação Objetivo-Documento"""
    __tablename__ = 'objetivo_documento'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    objetivo_id = Column(Integer, ForeignKey('documental.objetivos_metas.id'), nullable=False)
    documento_id = Column(Integer, ForeignKey('documental.documentos.id'), nullable=False)

    # Relacionamentos
    objetivo = relationship('ObjetivoMeta', back_populates='documentos')
    documento = relationship('Documento', back_populates='objetivos')


class RiscoOportunidade(Base):
    """Tabela de riscos e oportunidades (ISO 6.1)"""
    __tablename__ = 'riscos_oportunidades'
    __table_args__ = (
        Index('idx_risco_codigo', 'codigo'),
        Index('idx_risco_status', 'status'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    tipo = Column(String(20), nullable=False)  # Risco ou Oportunidade
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    fonte = Column(String(100))
    categoria = Column(String(50))
    probabilidade = Column(Integer, default=1)
    impacto = Column(Integer, default=1)
    nivel_risco = Column(Integer)
    tratamento = Column(String(50))
    acao_planejada = Column(Text)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    prazo = Column(Date)
    status = Column(String(30), default='Identificado')
    data_identificacao = Column(Date)
    data_atualizacao = Column(Date)
    eficacia = Column(String(50))
    observacoes = Column(Text)

    # Relacionamentos
    area = relationship('Area', back_populates='riscos')
    nao_conformidades = relationship('RiscoNC', back_populates='risco')


class RiscoNC(Base):
    """Tabela de vinculação Risco-NC"""
    __tablename__ = 'risco_nc'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    risco_id = Column(Integer, ForeignKey('documental.riscos_oportunidades.id'), nullable=False)
    nc_id = Column(Integer, ForeignKey('documental.nao_conformidades.id'), nullable=False)

    # Relacionamentos
    risco = relationship('RiscoOportunidade', back_populates='nao_conformidades')
    nao_conformidade = relationship('NaoConformidade', back_populates='riscos')


class Competencia(Base):
    """Tabela de competências (ISO 7.2)"""
    __tablename__ = 'competencias'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    tipo = Column(String(30), default='Técnica')
    nivel_requerido = Column(Integer, default=1)
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    funcoes = relationship('FuncaoCompetencia', back_populates='competencia')
    colaboradores = relationship('ColaboradorCompetencia', back_populates='competencia')
    treinamentos = relationship('TreinamentoCompetencia', back_populates='competencia')


class Funcao(Base):
    """Tabela de funções/cargos"""
    __tablename__ = 'funcoes'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    requisitos_minimos = Column(Text)
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    area = relationship('Area', back_populates='funcoes')
    competencias = relationship('FuncaoCompetencia', back_populates='funcao', cascade='all, delete-orphan')
    colaboradores = relationship('ColaboradorDoc', back_populates='funcao')


class FuncaoCompetencia(Base):
    """Tabela de matriz Função-Competência"""
    __tablename__ = 'funcao_competencia'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    funcao_id = Column(Integer, ForeignKey('documental.funcoes.id'), nullable=False)
    competencia_id = Column(Integer, ForeignKey('documental.competencias.id'), nullable=False)
    nivel_requerido = Column(Integer, default=1)
    obrigatorio = Column(Boolean, default=True)

    # Relacionamentos
    funcao = relationship('Funcao', back_populates='competencias')
    competencia = relationship('Competencia', back_populates='funcoes')


class ColaboradorDoc(Base):
    """Tabela de colaboradores (para competências)"""
    __tablename__ = 'colaboradores'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    matricula = Column(String(20))
    funcao_id = Column(Integer, ForeignKey('documental.funcoes.id'))
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    data_admissao = Column(Date)
    email = Column(String(255))
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True)
    observacoes = Column(Text)

    # Relacionamentos
    funcao = relationship('Funcao', back_populates='colaboradores')
    area = relationship('Area', back_populates='colaboradores')
    competencias = relationship('ColaboradorCompetencia', back_populates='colaborador', cascade='all, delete-orphan')
    treinamentos = relationship('TreinamentoParticipante', back_populates='colaborador')


class ColaboradorCompetencia(Base):
    """Tabela de qualificações do colaborador"""
    __tablename__ = 'colaborador_competencia'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    colaborador_id = Column(Integer, ForeignKey('documental.colaboradores.id'), nullable=False)
    competencia_id = Column(Integer, ForeignKey('documental.competencias.id'), nullable=False)
    nivel_atual = Column(Integer, default=0)
    data_avaliacao = Column(Date)
    evidencia = Column(Text)
    observacoes = Column(Text)

    # Relacionamentos
    colaborador = relationship('ColaboradorDoc', back_populates='competencias')
    competencia = relationship('Competencia', back_populates='colaboradores')


class Treinamento(Base):
    """Tabela de treinamentos (ISO 7.3)"""
    __tablename__ = 'treinamentos'
    __table_args__ = (
        Index('idx_treinamento_codigo', 'codigo'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    tipo = Column(String(30), default='Interno')
    area_id = Column(Integer, ForeignKey('documental.areas.id'))
    carga_horaria = Column(Float)
    instrutor = Column(String(255))
    instituicao = Column(String(255))
    data_realizacao = Column(Date)
    data_validade = Column(Date)
    local = Column(String(255))
    status = Column(String(30), default='Planejado')
    material = Column(Text)
    observacoes = Column(Text)

    # Relacionamentos
    area = relationship('Area', back_populates='treinamentos')
    competencias = relationship('TreinamentoCompetencia', back_populates='treinamento', cascade='all, delete-orphan')
    participantes = relationship('TreinamentoParticipante', back_populates='treinamento', cascade='all, delete-orphan')


class TreinamentoCompetencia(Base):
    """Tabela de competências por treinamento"""
    __tablename__ = 'treinamento_competencia'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    treinamento_id = Column(Integer, ForeignKey('documental.treinamentos.id'), nullable=False)
    competencia_id = Column(Integer, ForeignKey('documental.competencias.id'), nullable=False)

    # Relacionamentos
    treinamento = relationship('Treinamento', back_populates='competencias')
    competencia = relationship('Competencia', back_populates='treinamentos')


class TreinamentoParticipante(Base):
    """Tabela de participantes de treinamento"""
    __tablename__ = 'treinamento_participante'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    treinamento_id = Column(Integer, ForeignKey('documental.treinamentos.id'), nullable=False)
    colaborador_id = Column(Integer, ForeignKey('documental.colaboradores.id'), nullable=False)
    status = Column(String(30), default='Convocado')
    nota = Column(Float)
    aprovado = Column(Boolean)
    certificado = Column(String(500))
    observacoes = Column(Text)

    # Relacionamentos
    treinamento = relationship('Treinamento', back_populates='participantes')
    colaborador = relationship('ColaboradorDoc', back_populates='treinamentos')


class AnaliseCritica(Base):
    """Tabela de análise crítica pela direção (ISO 9.3)"""
    __tablename__ = 'analise_critica'
    __table_args__ = (
        Index('idx_analise_codigo', 'codigo'),
        {'schema': 'documental'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    data_reuniao = Column(Date, nullable=False)
    tipo = Column(String(30), default='Ordinária')
    participantes = Column(Text)
    pauta = Column(Text)
    resultados_anteriores = Column(Text)
    situacao_acoes = Column(Text)
    mudancas_contexto = Column(Text)
    desempenho_processos = Column(Text)
    conformidade_produtos = Column(Text)
    nao_conformidades = Column(Text)
    resultados_auditorias = Column(Text)
    satisfacao_cliente = Column(Text)
    fornecedores = Column(Text)
    recursos = Column(Text)
    riscos_oportunidades = Column(Text)
    melhoria_continua = Column(Text)
    decisoes = Column(Text)
    acoes_definidas = Column(Text)
    proxima_reuniao = Column(Date)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    status = Column(String(30), default='Realizada')
    observacoes = Column(Text)

    # Relacionamentos
    acoes = relationship('AnaliseCriticaAcao', back_populates='analise', cascade='all, delete-orphan')


class AnaliseCriticaAcao(Base):
    """Tabela de ações da análise crítica"""
    __tablename__ = 'analise_critica_acao'
    __table_args__ = {'schema': 'documental'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    analise_id = Column(Integer, ForeignKey('documental.analise_critica.id'), nullable=False)
    descricao = Column(Text, nullable=False)
    responsavel_id = Column(Integer, ForeignKey('documental.responsaveis.id'))
    prazo = Column(Date)
    status = Column(String(30), default='Pendente')
    resultado = Column(Text)

    # Relacionamentos
    analise = relationship('AnaliseCritica', back_populates='acoes')
