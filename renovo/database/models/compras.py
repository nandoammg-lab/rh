"""
Models SQLAlchemy - Módulo Compras (Gestão de Compras)
Schema: compras
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class CentroCusto(Base):
    """Tabela de centros de custo (obras/projetos)"""
    __tablename__ = 'centros_custo'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    local = Column(String(255), nullable=False)
    responsavel = Column(String(255), nullable=False)
    diretor = Column(String(255), nullable=False)

    # Relacionamentos
    compras = relationship('Compra', back_populates='centro_custo')
    requisicoes = relationship('RequisicaoCompra', back_populates='obra_projeto')


class Fornecedor(Base):
    """Tabela de fornecedores"""
    __tablename__ = 'fornecedores'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cpf_cnpj = Column(String(20))
    cidade = Column(String(100))
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    compras = relationship('Compra', back_populates='fornecedor')


class Funcionario(Base):
    """Tabela de funcionários (solicitantes)"""
    __tablename__ = 'funcionarios'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14))
    cargo = Column(String(100))
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True)

    # Relacionamentos
    compras = relationship('Compra', back_populates='funcionario')


class Categoria(Base):
    """Tabela de categorias de compras"""
    __tablename__ = 'categorias'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), unique=True, nullable=False)
    descricao = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)


class Compra(Base):
    """Tabela de registro geral de compras"""
    __tablename__ = 'compras'
    __table_args__ = (
        Index('idx_compras_data', 'data_compra'),
        Index('idx_compras_fornecedor', 'fornecedor_id'),
        {'schema': 'compras'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_compra = Column(Date, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey('compras.fornecedores.id'))
    fornecedor_nome = Column(String(255))
    centro_custo_id = Column(Integer, ForeignKey('compras.centros_custo.id'))
    centro_custo_nome = Column(String(255))
    categoria = Column(String(50))
    descricao = Column(Text, nullable=False)
    valor = Column(Float, nullable=False)
    forma_pagamento = Column(String(50))
    funcionario_id = Column(Integer, ForeignKey('compras.funcionarios.id'))
    funcionario_nome = Column(String(255))
    observacoes = Column(Text)

    # Dados do documento
    emitente_id = Column(Integer)
    emitente_nome = Column(String(255))
    tipo_documento = Column(String(50))
    numero_nf = Column(String(50))
    data_nf = Column(Date)
    finalidade = Column(Text)

    # Parcelamento
    num_parcelas = Column(Integer)
    datas_parcelas = Column(Text)  # Separadas por ;
    valores_parcelas = Column(Text)  # Separadas por ;
    data_pagamento_faturado = Column(Date)

    # Múltiplas notas/categorias
    ids_categoria = Column(Text)
    numeros_nf = Column(Text)
    datas_nf_multiplas = Column(Text)
    valores_notas = Column(Text)

    # Controle
    data_criacao = Column(DateTime, nullable=False, default=datetime.now)
    data_atualizacao = Column(DateTime, onupdate=datetime.now)

    # Relacionamentos
    fornecedor = relationship('Fornecedor', back_populates='compras')
    centro_custo = relationship('CentroCusto', back_populates='compras')
    funcionario = relationship('Funcionario', back_populates='compras')


class RequisicaoCompra(Base):
    """Tabela de requisições de compra (RCs)"""
    __tablename__ = 'requisicoes_compra'
    __table_args__ = (
        Index('idx_rc_numero', 'numero_rc'),
        Index('idx_rc_status', 'status'),
        Index('idx_rc_obra', 'obra_projeto_id'),
        {'schema': 'compras'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_rc = Column(String(20), unique=True)
    obra_projeto_id = Column(Integer, ForeignKey('compras.centros_custo.id'), nullable=False)
    tipo_requisicao = Column(String(20), nullable=False)  # Simples, Técnica
    tipo_material_servico = Column(String(50))
    descricao = Column(Text, nullable=False)
    especificacao_tecnica = Column(Text)
    normas_aplicaveis = Column(Text)
    quantidade = Column(Float)
    unidade_medida = Column(String(20))
    prazo_entrega = Column(String(50))
    criticidade = Column(String(20))  # Baixa, Média, Alta, Crítica
    justificativa = Column(Text)
    fornecedor_sugerido = Column(String(255))
    valor_estimado = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default='Rascunho')
    status_anterior = Column(String(50))

    # Datas de controle
    data_criacao = Column(DateTime, nullable=False, default=datetime.now)
    data_ultima_atualizacao = Column(DateTime, onupdate=datetime.now)
    data_aprovacao = Column(DateTime)
    data_cotacao = Column(DateTime)
    data_selecao_vencedor = Column(DateTime)
    data_arquivamento = Column(DateTime)

    # Relacionamentos
    obra_projeto = relationship('CentroCusto', back_populates='requisicoes')
    aprovacoes = relationship('Aprovacao', back_populates='requisicao', cascade='all, delete-orphan')
    cotacoes = relationship('Cotacao', back_populates='requisicao', cascade='all, delete-orphan')
    itens = relationship('ItemRC', back_populates='requisicao', cascade='all, delete-orphan')
    pedido_finalizado = relationship('PedidoFinalizado', back_populates='requisicao', uselist=False)


class Aprovacao(Base):
    """Tabela de aprovações de requisições"""
    __tablename__ = 'aprovacoes'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    requisicao_id = Column(Integer, ForeignKey('compras.requisicoes_compra.id'), nullable=False)
    aprovador = Column(String(255), nullable=False)
    tipo_aprovador = Column(String(20))  # Gestor, Diretoria
    acao = Column(String(30), nullable=False)  # Aprovado, Reprovado, Ajustes Solicitados
    comentario = Column(Text)
    data_hora = Column(DateTime, nullable=False, default=datetime.now)

    # Relacionamentos
    requisicao = relationship('RequisicaoCompra', back_populates='aprovacoes')


class Cotacao(Base):
    """Tabela de cotações"""
    __tablename__ = 'cotacoes'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    rc_id = Column(Integer, ForeignKey('compras.requisicoes_compra.id'), nullable=False)
    numero_rc = Column(String(20))
    status = Column(String(30), default='Em Análise')
    data_cotacao = Column(Date)

    # Fornecedor 1
    fornecedor1_nome = Column(String(255))
    fornecedor1_valor = Column(Float)
    fornecedor1_condicoes = Column(Text)
    fornecedor1_prazo_entrega = Column(String(50))
    fornecedor1_frete = Column(String(50))
    fornecedor1_pagamento = Column(String(100))
    fornecedor1_observacoes = Column(Text)

    # Fornecedor 2
    fornecedor2_nome = Column(String(255))
    fornecedor2_valor = Column(Float)
    fornecedor2_condicoes = Column(Text)
    fornecedor2_prazo_entrega = Column(String(50))
    fornecedor2_frete = Column(String(50))
    fornecedor2_pagamento = Column(String(100))
    fornecedor2_observacoes = Column(Text)

    # Fornecedor 3
    fornecedor3_nome = Column(String(255))
    fornecedor3_valor = Column(Float)
    fornecedor3_condicoes = Column(Text)
    fornecedor3_prazo_entrega = Column(String(50))
    fornecedor3_frete = Column(String(50))
    fornecedor3_pagamento = Column(String(100))
    fornecedor3_observacoes = Column(Text)

    # Resultado
    condicoes = Column(Text)
    fornecedor_vencedor = Column(String(255))
    justificativa_vencedor = Column(Text)

    # Controle
    data_criacao = Column(DateTime, default=datetime.now)
    data_ultima_atualizacao = Column(DateTime, onupdate=datetime.now)

    # Relacionamentos
    requisicao = relationship('RequisicaoCompra', back_populates='cotacoes')
    pedido_finalizado = relationship('PedidoFinalizado', back_populates='cotacao', uselist=False)


class PedidoFinalizado(Base):
    """Tabela de pedidos finalizados"""
    __tablename__ = 'pedidos_finalizados'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    rc_id = Column(Integer, ForeignKey('compras.requisicoes_compra.id'), nullable=False)
    cotacao_id = Column(Integer, ForeignKey('compras.cotacoes.id'))
    fornecedor_vencedor = Column(String(255))
    valor_final = Column(Float)
    justificativa_vencedor = Column(Text)
    status = Column(String(30))

    # Aprovador
    aprovador_id = Column(Integer)
    aprovador_nome = Column(String(255))
    aprovador_cargo = Column(String(100))

    # Controle
    data_criacao = Column(DateTime, default=datetime.now)
    data_ultima_atualizacao = Column(DateTime, onupdate=datetime.now)

    # Relacionamentos
    requisicao = relationship('RequisicaoCompra', back_populates='pedido_finalizado')
    cotacao = relationship('Cotacao', back_populates='pedido_finalizado')


class ItemRC(Base):
    """Tabela de itens das requisições de compra"""
    __tablename__ = 'itens_rc'
    __table_args__ = {'schema': 'compras'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    rc_id = Column(Integer, ForeignKey('compras.requisicoes_compra.id'), nullable=False)
    item_numero = Column(Integer, nullable=False)
    descricao = Column(Text, nullable=False)
    quantidade = Column(Float, nullable=False, default=1)
    unidade_medida = Column(String(20), nullable=False, default='UN')

    # Relacionamentos
    requisicao = relationship('RequisicaoCompra', back_populates='itens')


class LogAuditoriaCompras(Base):
    """Tabela de log de auditoria do módulo de compras"""
    __tablename__ = 'log_auditoria'
    __table_args__ = (
        Index('idx_log_compras_data', 'data_hora'),
        {'schema': 'compras'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String(100))
    acao = Column(String(50))
    detalhes = Column(Text)
