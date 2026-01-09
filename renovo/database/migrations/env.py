"""
Alembic Environment Configuration - Renovo ERP
Suporte a múltiplos schemas (crm, rh, compras, patrimonio, documental)
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool, text
from alembic import context

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar configurações e models
from database.connection import get_connection_url, SCHEMAS, Base

# Importar todos os models para registrar na metadata
from database.models import crm, rh, compras, patrimonio, documental

# Configuração do Alembic
config = context.config

# Configurar logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata dos models para autogenerate
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Filtrar objetos para incluir apenas os schemas relevantes.
    """
    if type_ == "table":
        if hasattr(object, 'schema') and object.schema:
            return object.schema in SCHEMAS
    return True


def run_migrations_offline() -> None:
    """
    Executar migrations em modo 'offline'.
    Gera SQL sem conectar ao banco.
    """
    url = get_connection_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        include_schemas=True,
        version_table_schema='rh',  # Schema para tabela de versão
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executar migrations em modo 'online'.
    Conecta ao banco e aplica alterações.
    """
    # Configurar URL da conexão
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_connection_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Criar schemas se não existirem
        for schema in SCHEMAS:
            try:
                connection.execute(
                    text(f"CREATE DATABASE IF NOT EXISTS `{schema}` "
                         f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                )
            except Exception:
                pass
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            include_schemas=True,
            version_table_schema='rh',  # Schema para tabela de versão alembic
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
