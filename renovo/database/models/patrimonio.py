"""
Models SQLAlchemy - Módulo Patrimônio (Sistema de Gestão Patrimonial)
Schema: patrimonio
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class Patrimonio(Base):
    """Tabela de patrimônios (bens)"""
    __tablename__ = 'patrimonios'
    __table_args__ = (
        Index('idx_patrimonio_categoria', 'categoria'),
        Index('idx_patrimonio_status', 'status_uso'),
        {'schema': 'patrimonio'}
    )

    numero_patrimonio = Column(String(50), primary_key=True)
    descricao = Column(String(255), nullable=False)
    marca = Column(String(100))
    categoria = Column(String(100))
    status_uso = Column(String(50))
    localizacao = Column(String(255))
    valor = Column(Float)
    observacoes = Column(Text)
    quilometragem_atual = Column(Integer, default=0)
    requer_calibracao = Column(Boolean, default=False)
    data_cadastro = Column(DateTime, default=datetime.now)

    # Relacionamentos
    custodias = relationship('Custodia', back_populates='patrimonio', cascade='all, delete-orphan')
    manutencoes = relationship('ManutencaoVeiculo', back_populates='patrimonio', cascade='all, delete-orphan')
    calibracoes = relationship('Calibracao', back_populates='patrimonio', cascade='all, delete-orphan')


class Responsavel(Base):
    """Tabela de responsáveis pelos patrimônios"""
    __tablename__ = 'responsaveis'
    __table_args__ = {'schema': 'patrimonio'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True)
    setor = Column(String(100))
    cargo = Column(String(100))
    email = Column(String(255))
    telefone = Column(String(20))
    status = Column(String(20), default='Ativo')
    data_cadastro = Column(DateTime, default=datetime.now)

    # Relacionamentos
    custodias = relationship('Custodia', back_populates='responsavel')


class Custodia(Base):
    """Tabela de custódias (movimentações de patrimônio)"""
    __tablename__ = 'custodias'
    __table_args__ = (
        Index('idx_custodia_patrimonio', 'numero_patrimonio'),
        Index('idx_custodia_data', 'data_acao'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_patrimonio = Column(String(50), ForeignKey('patrimonio.patrimonios.numero_patrimonio', ondelete='CASCADE'), nullable=False)
    id_responsavel = Column(Integer, ForeignKey('patrimonio.responsaveis.id', ondelete='RESTRICT'), nullable=False)
    data_acao = Column(DateTime, default=datetime.now)
    acao = Column(String(50), nullable=False)
    motivo = Column(Text)
    setor = Column(String(100))

    # Relacionamentos
    patrimonio = relationship('Patrimonio', back_populates='custodias')
    responsavel = relationship('Responsavel', back_populates='custodias')


class ManutencaoVeiculo(Base):
    """Tabela de manutenções de veículos"""
    __tablename__ = 'manutencoes_veiculos'
    __table_args__ = (
        Index('idx_manutencao_patrimonio', 'numero_patrimonio'),
        Index('idx_manutencao_data', 'data_manutencao'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_patrimonio = Column(String(50), ForeignKey('patrimonio.patrimonios.numero_patrimonio', ondelete='CASCADE'), nullable=False)
    tipo_manutencao = Column(String(100), nullable=False)
    data_manutencao = Column(Date, nullable=False)
    quilometragem = Column(Integer)
    valor = Column(Float)
    fornecedor = Column(String(255))
    observacoes = Column(Text)
    data_cadastro = Column(DateTime, default=datetime.now)

    # Relacionamentos
    patrimonio = relationship('Patrimonio', back_populates='manutencoes')


class Calibracao(Base):
    """Tabela de calibrações de equipamentos"""
    __tablename__ = 'calibracoes'
    __table_args__ = (
        Index('idx_calibracao_patrimonio', 'numero_patrimonio'),
        Index('idx_calibracao_vencimento', 'data_vencimento'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_patrimonio = Column(String(50), ForeignKey('patrimonio.patrimonios.numero_patrimonio', ondelete='CASCADE'), nullable=False)
    data_calibracao = Column(Date, nullable=False)
    validade_meses = Column(Integer, default=12)
    data_vencimento = Column(Date, nullable=False)
    certificado_path = Column(String(500))
    laboratorio = Column(String(255))
    observacoes = Column(Text)
    data_cadastro = Column(DateTime, default=datetime.now)

    # Relacionamentos
    patrimonio = relationship('Patrimonio', back_populates='calibracoes')


class LogSistemaPatrimonio(Base):
    """Tabela de log do sistema de patrimônio"""
    __tablename__ = 'log_sistema'
    __table_args__ = (
        Index('idx_log_patrimonio_data', 'data_hora'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_hora = Column(DateTime, default=datetime.now)
    acao = Column(String(100), nullable=False)
    usuario = Column(String(100), default='Sistema')
    descricao = Column(Text)


# ========== FARDAMENTOS ==========

class Fardamento(Base):
    """Tabela de estoque de fardamentos"""
    __tablename__ = 'fardamentos'
    __table_args__ = (
        Index('idx_fardamento_cargo', 'cargo'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cargo = Column(String(100), nullable=False)
    tipo = Column(String(100), nullable=False)
    tamanho = Column(String(10), nullable=False)
    cor = Column(String(50), nullable=False)
    manga = Column(String(20), nullable=False)
    novas = Column(Integer, default=0)
    em_uso = Column(Integer, default=0)
    aguardando_higienizacao = Column(Integer, default=0)
    higienizadas = Column(Integer, default=0)
    descartadas = Column(Integer, default=0)
    data_lote = Column(DateTime, default=datetime.now)


class CorFardamento(Base):
    """Tabela de cores de fardamento disponíveis"""
    __tablename__ = 'cores_fardamento'
    __table_args__ = {'schema': 'patrimonio'}

    nome = Column(String(50), primary_key=True)


class FardamentoUsado(Base):
    """Tabela de fardamentos em uso"""
    __tablename__ = 'fardamentos_usados'
    __table_args__ = (
        Index('idx_fardamento_usado_responsavel', 'responsavel'),
        {'schema': 'patrimonio'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cargo = Column(String(100), nullable=False)
    tipo = Column(String(100), nullable=False)
    tamanho = Column(String(10), nullable=False)
    cor = Column(String(50), nullable=False)
    manga = Column(String(20), nullable=False)
    responsavel = Column(String(255), nullable=False)
    data_retirada = Column(DateTime, default=datetime.now)
    data_devolucao = Column(DateTime)
    status_devolucao = Column(String(50))


class TermoFardamento(Base):
    """Tabela de termos de entrega de fardamento"""
    __tablename__ = 'termos_fardamento'
    __table_args__ = {'schema': 'patrimonio'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_termo = Column(String(50), unique=True, nullable=False)
    responsavel = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=False)
    tipo = Column(String(100), nullable=False)
    tamanho = Column(String(10), nullable=False)
    cor = Column(String(50), nullable=False)
    manga = Column(String(20), nullable=False)
    data_geracao = Column(DateTime, default=datetime.now)
    caminho_arquivo = Column(String(500))
