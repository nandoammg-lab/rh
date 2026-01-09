"""
Módulo de Conexão com Banco de Dados MySQL/AWS RDS
Renovo ERP - Sistema Unificado

Este módulo gerencia a conexão com o banco de dados MySQL hospedado na AWS RDS,
utilizando SQLAlchemy como ORM e suportando múltiplos schemas por módulo.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

# Carregar variáveis de ambiente
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Base declarativa para todos os models
Base = declarative_base()

# Schemas disponíveis (um por módulo)
SCHEMAS = ['crm', 'rh', 'compras', 'patrimonio', 'documental']

# Configuração da engine (singleton)
_engine = None
_session_factory = None


def get_connection_url() -> str:
    """
    Monta a URL de conexão MySQL a partir das variáveis de ambiente.

    Returns:
        str: URL de conexão no formato SQLAlchemy
    """
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = os.getenv('MYSQL_PORT', '3306')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'rh')

    # Construir URL base
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    # Adicionar parâmetros de charset
    url += "?charset=utf8mb4"

    return url


def get_ssl_args() -> dict:
    """
    Retorna argumentos SSL para conexão segura com AWS RDS.

    Returns:
        dict: Argumentos de conexão SSL
    """
    ssl_required = os.getenv('MYSQL_SSL_REQUIRED', 'false').lower() == 'true'

    if not ssl_required:
        return {}

    ssl_ca = os.getenv('MYSQL_SSL_CA')

    connect_args = {
        'ssl': {
            'ssl_mode': 'VERIFY_IDENTITY'
        }
    }

    if ssl_ca:
        ssl_ca_path = Path(__file__).parent.parent / ssl_ca
        if ssl_ca_path.exists():
            connect_args['ssl']['ca'] = str(ssl_ca_path)

    return connect_args


def get_engine():
    """
    Retorna a engine SQLAlchemy (singleton).
    Cria uma nova engine se não existir.

    Returns:
        Engine: Engine SQLAlchemy configurada
    """
    global _engine

    if _engine is None:
        pool_size = int(os.getenv('MYSQL_POOL_SIZE', '5'))
        max_overflow = int(os.getenv('MYSQL_MAX_OVERFLOW', '10'))
        pool_timeout = int(os.getenv('MYSQL_POOL_TIMEOUT', '30'))

        _engine = create_engine(
            get_connection_url(),
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verifica conexão antes de usar
            echo=os.getenv('ENVIRONMENT', 'development') == 'development',
            connect_args=get_ssl_args()
        )

        # Event listener para definir charset em cada conexão
        @event.listens_for(_engine, 'connect')
        def set_charset(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()

    return _engine


def get_session_factory():
    """
    Retorna a factory de sessões (singleton).

    Returns:
        sessionmaker: Factory configurada para criar sessões
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

    return _session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager para obter uma sessão do banco de dados.
    Gerencia commit/rollback automaticamente.

    Yields:
        Session: Sessão SQLAlchemy

    Example:
        with get_session() as session:
            result = session.query(User).all()
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_schemas():
    """
    Cria os schemas do banco de dados se não existirem.
    """
    engine = get_engine()

    with engine.connect() as conn:
        for schema in SCHEMAS:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()


def init_database(create_tables: bool = True):
    """
    Inicializa o banco de dados, criando schemas e tabelas.

    Args:
        create_tables: Se True, cria as tabelas definidas nos models
    """
    # Criar schemas
    create_schemas()

    if create_tables:
        # Importar todos os models para registrá-los na Base
        from database.models import crm, rh, compras, patrimonio, documental

        # Criar todas as tabelas
        Base.metadata.create_all(bind=get_engine())


def test_connection() -> bool:
    """
    Testa a conexão com o banco de dados.

    Returns:
        bool: True se a conexão foi bem-sucedida
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return False


# Funções de compatibilidade para migração gradual dos módulos existentes
def get_legacy_connection(schema: str):
    """
    Retorna uma conexão no estilo antigo (para compatibilidade durante migração).

    Args:
        schema: Nome do schema/módulo (crm, rh, compras, patrimonio, documental)

    Returns:
        Connection: Conexão SQLAlchemy com schema definido
    """
    engine = get_engine()
    conn = engine.connect()
    conn.execute(text(f"USE `{schema}`"))
    return conn
