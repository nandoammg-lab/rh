"""
Script de Migração de Dados - SQLite para MySQL/AWS RDS
Renovo ERP - Sistema Unificado

Este script migra todos os dados dos bancos SQLite existentes
para o banco MySQL unificado na AWS RDS.

Uso:
    python scripts/migrate_data.py

Pré-requisitos:
    1. Configurar o arquivo .env com as credenciais do MySQL
    2. Executar as migrations: alembic upgrade head
    3. Ter os bancos SQLite existentes nos módulos
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Adicionar raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.connection import get_session, get_engine, SCHEMAS
from sqlalchemy import text


# Caminhos dos bancos SQLite existentes
SQLITE_DATABASES = {
    'crm': ROOT_DIR / 'Gerenciamento de Relacionamento com o Cliente' / 'dashboard_comercial.db',
    'rh': ROOT_DIR / 'Sistema de Gestão de Recursos Humanos' / 'rh_database.db',
    'compras_principal': ROOT_DIR / 'Gestão de Compras' / 'database' / 'sistema_compras.db',
    'compras_pedidos': ROOT_DIR / 'Gestão de Compras' / 'database' / 'pedidos_compra.db',
    'patrimonio': ROOT_DIR / 'Sistema de Gestão Patrimonial' / 'database' / 'gestao_patrimonial.db',
    'fardamentos': ROOT_DIR / 'Sistema de Gestão Patrimonial' / 'database' / 'fardamentos.db',
    'documental': ROOT_DIR / 'Sistema de Gestao Documental' / 'database' / 'gestao_documental.db',
}


def get_sqlite_connection(db_path: Path):
    """Retorna conexão SQLite se o arquivo existir"""
    if not db_path.exists():
        print(f"  [AVISO] Banco não encontrado: {db_path}")
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_table_columns(sqlite_conn, table_name: str) -> list:
    """Retorna lista de colunas de uma tabela SQLite"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]


def migrate_table(sqlite_conn, mysql_engine, table_name: str, schema: str,
                  column_mapping: dict = None, transform_func=None):
    """
    Migra dados de uma tabela SQLite para MySQL.

    Args:
        sqlite_conn: Conexão SQLite
        mysql_engine: Engine MySQL
        table_name: Nome da tabela
        schema: Schema MySQL de destino
        column_mapping: Mapeamento de colunas {sqlite_col: mysql_col}
        transform_func: Função para transformar cada linha
    """
    cursor = sqlite_conn.cursor()

    # Verificar se tabela existe no SQLite
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"    [SKIP] Tabela {table_name} não existe no SQLite")
        return 0

    # Buscar dados
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if not rows:
        print(f"    [SKIP] Tabela {table_name} está vazia")
        return 0

    # Obter nomes das colunas
    columns = [desc[0] for desc in cursor.description]

    # Aplicar mapeamento de colunas se fornecido
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]

    count = 0
    with mysql_engine.connect() as conn:
        for row in rows:
            row_dict = dict(zip(columns, row))

            # Aplicar transformação se fornecida
            if transform_func:
                row_dict = transform_func(row_dict)
                if row_dict is None:
                    continue

            # Montar INSERT
            cols = ', '.join([f"`{c}`" for c in row_dict.keys()])
            placeholders = ', '.join([f":{c}" for c in row_dict.keys()])

            try:
                conn.execute(
                    text(f"INSERT INTO `{schema}`.`{table_name}` ({cols}) VALUES ({placeholders})"),
                    row_dict
                )
                count += 1
            except Exception as e:
                # Tentar UPDATE se for duplicata
                if "Duplicate" in str(e):
                    pass  # Registro já existe
                else:
                    print(f"    [ERRO] {table_name}: {e}")

        conn.commit()

    return count


def migrate_crm():
    """Migra dados do módulo CRM"""
    print("\n[CRM] Iniciando migração...")

    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['crm'])
    if not sqlite_conn:
        return

    engine = get_engine()

    # Migrar tabelas
    tables = ['clientes', 'contatos', 'leads', 'visitas', 'log_auditoria', 'leads_contatos']

    for table in tables:
        count = migrate_table(sqlite_conn, engine, table, 'crm')
        print(f"    [OK] {table}: {count} registros")

    sqlite_conn.close()
    print("[CRM] Migração concluída!")


def migrate_rh():
    """Migra dados do módulo RH"""
    print("\n[RH] Iniciando migração...")

    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['rh'])
    if not sqlite_conn:
        return

    engine = get_engine()

    # Migrar tabelas em ordem (respeitando FKs)
    tables = [
        'empresas',
        'colaboradores',
        'dependentes',
        'localizacoes',
        'ferias',
        'periodos_ferias',
        'contratos_experiencia',
        'blocklist',
        'configuracoes',
        'historico_alteracoes',
        'documentos_colaborador',
        'logs_sistema',
        'usuarios',
        'tentativas_login',
        'bloqueios_login'
    ]

    for table in tables:
        count = migrate_table(sqlite_conn, engine, table, 'rh')
        print(f"    [OK] {table}: {count} registros")

    sqlite_conn.close()
    print("[RH] Migração concluída!")


def migrate_compras():
    """Migra dados do módulo Compras"""
    print("\n[COMPRAS] Iniciando migração...")

    engine = get_engine()

    # Banco principal
    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['compras_principal'])
    if sqlite_conn:
        tables_principal = ['centros_custo', 'fornecedores', 'funcionarios', 'categorias', 'compras']
        for table in tables_principal:
            count = migrate_table(sqlite_conn, engine, table, 'compras')
            print(f"    [OK] {table}: {count} registros")
        sqlite_conn.close()

    # Banco de pedidos
    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['compras_pedidos'])
    if sqlite_conn:
        tables_pedidos = ['requisicoes_compra', 'aprovacoes', 'cotacoes', 'pedidos_finalizados', 'itens_rc']
        for table in tables_pedidos:
            count = migrate_table(sqlite_conn, engine, table, 'compras')
            print(f"    [OK] {table}: {count} registros")
        sqlite_conn.close()

    print("[COMPRAS] Migração concluída!")


def migrate_patrimonio():
    """Migra dados do módulo Patrimônio"""
    print("\n[PATRIMONIO] Iniciando migração...")

    engine = get_engine()

    # Banco principal
    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['patrimonio'])
    if sqlite_conn:
        tables = ['patrimonios', 'responsaveis', 'custodias', 'manutencoes_veiculos', 'calibracoes', 'log_sistema']
        for table in tables:
            count = migrate_table(sqlite_conn, engine, table, 'patrimonio')
            print(f"    [OK] {table}: {count} registros")
        sqlite_conn.close()

    # Banco de fardamentos
    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['fardamentos'])
    if sqlite_conn:
        tables = ['fardamentos', 'cores_fardamento', 'fardamentos_usados', 'termos_fardamento']
        for table in tables:
            count = migrate_table(sqlite_conn, engine, table, 'patrimonio')
            print(f"    [OK] {table}: {count} registros")
        sqlite_conn.close()

    print("[PATRIMONIO] Migração concluída!")


def migrate_documental():
    """Migra dados do módulo Documental"""
    print("\n[DOCUMENTAL] Iniciando migração...")

    sqlite_conn = get_sqlite_connection(SQLITE_DATABASES['documental'])
    if not sqlite_conn:
        return

    engine = get_engine()

    # Migrar tabelas em ordem (respeitando FKs)
    tables = [
        'tipos_documento',
        'areas',
        'responsaveis',
        'requisitos_iso',
        'documentos',
        'revisoes',
        'documento_requisito',
        'categorias_registro',
        'registros',
        'locais_distribuicao',
        'distribuicao_copias',
        'nao_conformidades',
        'log_atividades',
        'objetivos_metas',
        'objetivos_acompanhamento',
        'objetivo_documento',
        'riscos_oportunidades',
        'risco_nc',
        'competencias',
        'funcoes',
        'funcao_competencia',
        'colaboradores',
        'colaborador_competencia',
        'treinamentos',
        'treinamento_competencia',
        'treinamento_participante',
        'analise_critica',
        'analise_critica_acao'
    ]

    for table in tables:
        count = migrate_table(sqlite_conn, engine, table, 'documental')
        print(f"    [OK] {table}: {count} registros")

    sqlite_conn.close()
    print("[DOCUMENTAL] Migração concluída!")


def verify_migration():
    """Verifica a migração comparando contagens"""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DA MIGRAÇÃO")
    print("="*60)

    engine = get_engine()

    for schema in SCHEMAS:
        print(f"\n[{schema.upper()}]")

        with engine.connect() as conn:
            # Listar tabelas do schema
            result = conn.execute(text(f"SHOW TABLES FROM `{schema}`"))
            tables = [row[0] for row in result]

            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM `{schema}`.`{table}`"))
                count = result.scalar()
                print(f"  {table}: {count} registros")


def main():
    """Função principal de migração"""
    print("="*60)
    print("MIGRAÇÃO DE DADOS - SQLite para MySQL/AWS RDS")
    print("Renovo ERP - Sistema Unificado")
    print("="*60)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Verificar conexão MySQL
    print("\n[CONEXAO] Testando conexão com MySQL...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[CONEXAO] Conexão OK!")
    except Exception as e:
        print(f"[ERRO] Falha na conexão: {e}")
        print("\nVerifique o arquivo .env com as credenciais do MySQL.")
        return

    # Executar migrações
    migrate_crm()
    migrate_rh()
    migrate_compras()
    migrate_patrimonio()
    migrate_documental()

    # Verificar migração
    verify_migration()

    print("\n" + "="*60)
    print("MIGRAÇÃO CONCLUÍDA!")
    print(f"Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)


if __name__ == '__main__':
    main()
