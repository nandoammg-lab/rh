"""
Models SQLAlchemy - Módulo CRM (Gerenciamento de Relacionamento com o Cliente)
Schema: crm
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class Cliente(Base):
    """Tabela de clientes"""
    __tablename__ = 'clientes'
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(20))
    cidade = Column(String(100))
    uf = Column(String(2))

    # Relacionamentos
    contatos = relationship('Contato', back_populates='cliente', cascade='all, delete-orphan')
    leads = relationship('Lead', back_populates='cliente')
    leads_contatos = relationship('LeadContato', back_populates='cliente', cascade='all, delete-orphan')


class Contato(Base):
    """Tabela de contatos dos clientes"""
    __tablename__ = 'contatos'
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('crm.clientes.id'))
    nome = Column(String(255), nullable=False)
    telefone = Column(String(20))
    email = Column(String(255))
    cargo = Column(String(100))

    # Relacionamentos
    cliente = relationship('Cliente', back_populates='contatos')


class Lead(Base):
    """Tabela de leads/oportunidades comerciais"""
    __tablename__ = 'leads'
    __table_args__ = (
        Index('idx_leads_codigo', 'codigo'),
        Index('idx_leads_status', 'status_lead'),
        {'schema': 'crm'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True)
    cliente_id = Column(Integer, ForeignKey('crm.clientes.id'))
    local = Column(String(255))
    uf_projeto = Column(String(2))
    convite = Column(String(255))
    contato = Column(String(255))
    telefone = Column(String(20))
    email = Column(String(255))
    data_entrada = Column(Date)
    caderno_encargos = Column(Text)
    contato_tecnico = Column(String(255))
    telefone_tecnico = Column(String(20))
    email_tecnico = Column(String(255))
    visita_agendada = Column(String(50))
    decisao_go = Column(String(10))
    data_go = Column(Date)
    data_qualificacao = Column(Date)
    data_proposta = Column(Date)
    responsavel_decisao = Column(String(255))
    observacoes = Column(Text)
    id_orcamento = Column(String(50))
    numero_pedido = Column(String(50))
    valor_bruto = Column(Float)
    margem_estimada = Column(Float)
    status_lead = Column(String(100))
    status_final = Column(String(50))
    motivo_perda = Column(Text)
    data_ultima_atualizacao = Column(Date)
    followup_proposta_status = Column(String(10))
    followup_proposta_dados = Column(Text)
    followup1_status = Column(String(10))
    followup1_dados = Column(Text)
    followup2_status = Column(String(10))
    followup2_dados = Column(Text)
    followup3_status = Column(String(10))
    followup3_dados = Column(Text)
    descricao_oportunidade = Column(Text)

    # Relacionamentos
    cliente = relationship('Cliente', back_populates='leads')


class Visita(Base):
    """Tabela de visitas comerciais"""
    __tablename__ = 'visitas'
    __table_args__ = (
        Index('idx_visitas_data', 'data_visita'),
        {'schema': 'crm'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    funcionario = Column(String(255))
    cliente = Column(String(255))
    local_visita = Column(String(255))
    uf_visita = Column(String(2))
    oportunidades = Column(Text)
    concorrentes = Column(Text)
    data_visita = Column(Date)


class LogAuditoria(Base):
    """Tabela de log de auditoria do CRM"""
    __tablename__ = 'log_auditoria'
    __table_args__ = (
        Index('idx_log_data', 'data_hora'),
        {'schema': 'crm'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String(100))
    acao = Column(String(50))
    tabela = Column(String(50))
    detalhes = Column(Text)


class LeadContato(Base):
    """Tabela de contatos comerciais por cliente (leads_contatos)"""
    __tablename__ = 'leads_contatos'
    __table_args__ = {'schema': 'crm'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('crm.clientes.id'), nullable=False)
    nome = Column(String(255), nullable=False)
    telefone = Column(String(20))
    email = Column(String(255))

    # Relacionamentos
    cliente = relationship('Cliente', back_populates='leads_contatos')
