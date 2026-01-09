"""
Módulo de Banco de Dados - Sistema de Gestão de RH
RENOVO Montagens Industriais
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import json


def get_base_path():
    """
    Retorna o caminho base do executável ou script.
    Necessário para PyInstaller --onefile funcionar corretamente.
    """
    if getattr(sys, 'frozen', False):
        # Executando como executável PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Executando como script Python - volta um nível (de utilities para raiz)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATABASE_PATH = os.path.join(get_base_path(), "rh_database.db")
BACKUP_DIR = os.path.join(get_base_path(), "backups")

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inicializa o banco de dados com todas as tabelas necessárias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Empresas Contratantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razao_social TEXT NOT NULL,
            cnpj TEXT UNIQUE NOT NULL,
            endereco TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            cidade TEXT,
            uf TEXT,
            telefone TEXT,
            email TEXT,
            logo_path TEXT,
            ativa INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela Principal de Colaboradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Foto
            foto_path TEXT,
            
            -- Empresa Contratante
            empresa_id INTEGER,
            
            -- Dados Pessoais
            nome_completo TEXT NOT NULL,
            endereco TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            cidade TEXT,
            uf_endereco TEXT,
            telefone TEXT,
            celular TEXT,
            email TEXT,
            data_nascimento DATE,
            naturalidade TEXT,
            uf_naturalidade TEXT,
            sexo TEXT,
            grau_instrucao TEXT,
            curso_formacao TEXT,
            data_conclusao DATE,
            estado_civil TEXT,
            data_casamento DATE,
            nome_conjuge TEXT,
            deficiencia TEXT,
            nome_mae TEXT,
            cpf_mae TEXT,
            nome_pai TEXT,
            cpf_pai TEXT,
            
            -- Documentos
            carteira_profissional TEXT,
            serie_carteira TEXT,
            uf_carteira TEXT,
            data_emissao_carteira DATE,
            rg TEXT,
            data_emissao_rg DATE,
            orgao_emissor_rg TEXT,
            uf_rg TEXT,
            cpf TEXT UNIQUE,
            titulo_eleitor TEXT,
            zona_eleitor TEXT,
            secao_eleitor TEXT,
            habilitacao TEXT,
            data_expedicao_cnh DATE,
            tipo_cnh TEXT,
            validade_cnh DATE,
            conselho_regional TEXT,
            sigla_conselho TEXT,
            numero_conselho TEXT,
            regiao_conselho TEXT,
            pis TEXT,
            data_cadastramento_pis DATE,
            reservista TEXT,
            
            -- Exame Médico
            data_exame_medico DATE,
            tipo_exames TEXT,
            nome_medico TEXT,
            crm TEXT,
            uf_crm TEXT,
            
            -- Dados Último Registro
            cnpj_ultimo_emprego TEXT,
            empresa_ultimo_emprego TEXT,
            data_admissao_ultimo DATE,
            data_saida_ultimo DATE,
            matricula_ultimo TEXT,
            primeiro_registro TEXT,
            data_ultima_contribuicao_sindical DATE,
            
            -- Dados da Empresa Atual
            data_admissao DATE,
            funcao TEXT,
            departamento TEXT,
            salario REAL,
            forma_pagamento TEXT,
            prazo_experiencia INTEGER,
            prorrogacao INTEGER,
            dias_trabalho TEXT,
            horario_trabalho TEXT,
            intervalo TEXT,
            dias_folga TEXT,
            observacoes_contrato TEXT,
            tipo_contrato TEXT,
            
            -- Benefícios
            vale_transporte INTEGER DEFAULT 0,
            vt_valor_diario REAL,
            vt_percentual_desconto REAL,
            vale_refeicao INTEGER DEFAULT 0,
            vr_valor_diario REAL,
            vr_percentual_desconto REAL,
            vale_alimentacao INTEGER DEFAULT 0,
            va_valor_diario REAL,
            va_percentual_desconto REAL,
            assistencia_medica INTEGER DEFAULT 0,
            am_valor_desconto REAL,
            assistencia_odontologica INTEGER DEFAULT 0,
            ao_valor_desconto REAL,
            seguro_vida INTEGER DEFAULT 0,
            sv_valor_desconto REAL,
            adiantamento INTEGER DEFAULT 0,
            percentual_adiantamento REAL,
            data_pagamento_adiantamento INTEGER,
            
            -- Dados Bancários
            tipo_conta TEXT,
            banco TEXT,
            agencia TEXT,
            conta TEXT,
            observacoes_banco TEXT,
            
            -- Observações Gerais
            observacoes_gerais TEXT,
            
            -- Status
            status TEXT DEFAULT 'ATIVO',
            data_desligamento DATE,
            motivo_desligamento TEXT,
            observacoes_desligamento TEXT,
            motivo_inativacao TEXT,
            submotivo_inativacao TEXT,
            data_inativacao DATE,
            
            -- Controle
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    ''')
    
    # Tabela de Dependentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dependentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            parentesco TEXT,
            data_nascimento DATE,
            cpf TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Localizações (onde o colaborador está alocado)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS localizacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            local_nome TEXT NOT NULL,
            cidade TEXT,
            uf TEXT,
            data_inicio DATE NOT NULL,
            data_fim DATE,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Férias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            periodo_aquisitivo_inicio DATE NOT NULL,
            periodo_aquisitivo_fim DATE NOT NULL,
            periodo_concessivo_limite DATE NOT NULL,
            dias_direito INTEGER DEFAULT 30,
            dias_gozados INTEGER DEFAULT 0,
            dias_vendidos INTEGER DEFAULT 0,
            status TEXT DEFAULT 'PENDENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de Períodos de Férias (fracionamento)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS periodos_ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ferias_id INTEGER NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE NOT NULL,
            dias INTEGER NOT NULL,
            abono_pecuniario INTEGER DEFAULT 0,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ferias_id) REFERENCES ferias(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de Histórico de Contratos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos_experiencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            data_inicio DATE NOT NULL,
            prazo_inicial INTEGER NOT NULL,
            data_fim_inicial DATE NOT NULL,
            prorrogacao INTEGER,
            data_fim_prorrogacao DATE,
            status TEXT DEFAULT 'VIGENTE',
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela Block-list (Ex-funcionários)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT NOT NULL,
            nome TEXT NOT NULL,
            empresa_id INTEGER,
            data_admissao DATE,
            data_desligamento DATE,
            motivo_desligamento TEXT,
            observacoes TEXT,
            pode_recontratar INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    ''')
    
    # Tabela de Configurações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Histórico de Alterações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_alteracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            campo TEXT NOT NULL,
            valor_anterior TEXT,
            valor_novo TEXT,
            data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Documentos do Colaborador
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos_colaborador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            tipo_documento TEXT NOT NULL,
            nome_arquivo_original TEXT,
            caminho_arquivo TEXT NOT NULL,
            obrigatorio INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Logs do Sistema (histórico centralizado)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_acao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            entidade_tipo TEXT,
            entidade_id INTEGER,
            entidade_nome TEXT,
            valor_anterior TEXT,
            valor_novo TEXT,
            usuario TEXT DEFAULT 'Sistema',
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Usuários do Sistema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            email TEXT,
            cargo TEXT,
            nivel_acesso TEXT NOT NULL DEFAULT 'operador',
            pergunta_seguranca TEXT,
            resposta_seguranca TEXT,
            ativo INTEGER DEFAULT 1,
            ultimo_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Tentativas de Login (para bloqueio após 10 tentativas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tentativas_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL,
            ip_address TEXT,
            sucesso INTEGER DEFAULT 0,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Bloqueios de Login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bloqueios_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            bloqueado_ate TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Migração: adicionar colunas de inativação se não existirem
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(colaboradores)")
        colunas = [col[1] for col in cursor.fetchall()]

        if 'motivo_inativacao' not in colunas:
            cursor.execute('ALTER TABLE colaboradores ADD COLUMN motivo_inativacao TEXT')
        if 'submotivo_inativacao' not in colunas:
            cursor.execute('ALTER TABLE colaboradores ADD COLUMN submotivo_inativacao TEXT')
        if 'data_inativacao' not in colunas:
            cursor.execute('ALTER TABLE colaboradores ADD COLUMN data_inativacao DATE')

        conn.commit()
    except:
        pass

    # Migração: normalizar CPFs para 11 dígitos
    try:
        cursor = conn.cursor()
        # Verificar se a migração já foi feita checando a tabela de configurações
        cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'migracao_cpf_11_digitos'")
        resultado = cursor.fetchone()

        if not resultado:
            conn.close()
            # Executar migração
            migrar_cpfs_para_11_digitos()
            # Marcar como executada
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('migracao_cpf_11_digitos', '1')")
            conn.commit()
        else:
            conn.close()
    except Exception:
        try:
            conn.close()
        except:
            pass

    # Migração: adicionar coluna nao_necessario na tabela documentos_colaborador
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(documentos_colaborador)")
        colunas = [col[1] for col in cursor.fetchall()]

        if 'nao_necessario' not in colunas:
            cursor.execute('ALTER TABLE documentos_colaborador ADD COLUMN nao_necessario INTEGER DEFAULT 0')
            conn.commit()
        conn.close()
    except:
        pass

    # Migração: adicionar coluna senha_resetada na tabela usuarios
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = [col[1] for col in cursor.fetchall()]

        if 'senha_resetada' not in colunas:
            cursor.execute('ALTER TABLE usuarios ADD COLUMN senha_resetada INTEGER DEFAULT 0')
            conn.commit()
        conn.close()
    except:
        pass

    # Criar índices para melhorar performance de buscas
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Índices para tabela colaboradores
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_colaboradores_cpf ON colaboradores(cpf)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_colaboradores_status ON colaboradores(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_colaboradores_empresa ON colaboradores(empresa_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_colaboradores_nome ON colaboradores(nome_completo)')

        # Índices para tabela blocklist
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocklist_cpf ON blocklist(cpf)')

        # Índices para tabela ferias
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ferias_colaborador ON ferias(colaborador_id)')

        # Índices para tabela dependentes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dependentes_colaborador ON dependentes(colaborador_id)')

        # Índices para tabela documentos_colaborador
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documentos_colaborador ON documentos_colaborador(colaborador_id)')

        # Índices para tabela contratos_experiencia
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contratos_colaborador ON contratos_experiencia(colaborador_id)')

        conn.commit()
        conn.close()
    except:
        pass

    # Criar diretório de backups se não existir
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def backup_database():
    """Realiza backup do banco de dados."""
    if not os.path.exists(DATABASE_PATH):
        return None

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"rh_backup_{timestamp}.db")
    shutil.copy2(DATABASE_PATH, backup_path)

    # Manter apenas os últimos 10 backups
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')])
    while len(backups) > 10:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))

    return backup_path


def validar_banco_dados(caminho_arquivo: str) -> bool:
    """
    Valida se um arquivo é um banco de dados SQLite válido do sistema.
    Verifica se contém as tabelas essenciais do sistema.
    """
    if not os.path.exists(caminho_arquivo):
        return False

    try:
        # Tentar conectar ao banco de dados
        conn = sqlite3.connect(caminho_arquivo)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verificar se as tabelas essenciais existem
        tabelas_essenciais = [
            'colaboradores',
            'empresas',
            'dependentes',
            'ferias',
            'blocklist'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas_existentes = [row['name'] for row in cursor.fetchall()]

        conn.close()

        # Verificar se todas as tabelas essenciais existem
        for tabela in tabelas_essenciais:
            if tabela not in tabelas_existentes:
                return False

        return True

    except Exception:
        return False


# =============================================================================
# CRUD Empresas
# =============================================================================

def criar_empresa(dados: dict) -> int:
    """Cria uma nova empresa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO empresas (razao_social, cnpj, endereco, numero, complemento,
                             bairro, cep, cidade, uf, telefone, email, logo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados.get('razao_social'),
        dados.get('cnpj'),
        dados.get('endereco'),
        dados.get('numero'),
        dados.get('complemento'),
        dados.get('bairro'),
        dados.get('cep'),
        dados.get('cidade'),
        dados.get('uf'),
        dados.get('telefone'),
        dados.get('email'),
        dados.get('logo_path')
    ))

    empresa_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Registrar log
    nome = dados.get('razao_social', 'Empresa')
    registrar_log(
        tipo_acao='CRIAR',
        categoria='EMPRESA',
        descricao=f'Nova empresa cadastrada: {nome}',
        entidade_tipo='empresa',
        entidade_id=empresa_id,
        entidade_nome=nome
    )

    return empresa_id

def listar_empresas(apenas_ativas: bool = True) -> List[Dict]:
    """Lista todas as empresas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if apenas_ativas:
        cursor.execute('SELECT * FROM empresas WHERE ativa = 1 ORDER BY razao_social')
    else:
        cursor.execute('SELECT * FROM empresas ORDER BY razao_social')
    
    empresas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return empresas

def obter_empresa(empresa_id: int) -> Optional[Dict]:
    """Obtém uma empresa pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM empresas WHERE id = ?', (empresa_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_empresa(empresa_id: int, dados: dict) -> bool:
    """Atualiza os dados de uma empresa."""
    conn = get_connection()
    cursor = conn.cursor()
    
    campos = []
    valores = []
    for key, value in dados.items():
        if key != 'id':
            campos.append(f"{key} = ?")
            valores.append(value)
    
    valores.append(empresa_id)
    
    cursor.execute(f'''
        UPDATE empresas SET {', '.join(campos)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', valores)
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def contar_colaboradores_empresa(empresa_id: int) -> int:
    """Conta quantos colaboradores estão vinculados a uma empresa."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM colaboradores WHERE empresa_id = ?', (empresa_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0


def excluir_empresa(empresa_id: int, excluir_colaboradores: bool = False) -> bool:
    """
    Exclui uma empresa do banco de dados.
    Se excluir_colaboradores=True, também exclui todos os colaboradores vinculados.
    Se excluir_colaboradores=False e houver colaboradores, retorna False.
    """
    # Obter dados da empresa para log
    empresa = obter_empresa(empresa_id)
    nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'

    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se há colaboradores vinculados
    cursor.execute('SELECT COUNT(*) FROM colaboradores WHERE empresa_id = ?', (empresa_id,))
    qtd_colaboradores = cursor.fetchone()[0]

    if qtd_colaboradores > 0 and not excluir_colaboradores:
        conn.close()
        return False

    try:
        if excluir_colaboradores and qtd_colaboradores > 0:
            # Obter IDs dos colaboradores para excluir registros relacionados
            cursor.execute('SELECT id FROM colaboradores WHERE empresa_id = ?', (empresa_id,))
            colaboradores_ids = [row[0] for row in cursor.fetchall()]

            for colab_id in colaboradores_ids:
                # Excluir dependentes
                cursor.execute('DELETE FROM dependentes WHERE colaborador_id = ?', (colab_id,))
                # Excluir contratos de experiência
                cursor.execute('DELETE FROM contratos_experiencia WHERE colaborador_id = ?', (colab_id,))
                # Excluir períodos de férias
                cursor.execute('DELETE FROM periodos_ferias WHERE colaborador_id = ?', (colab_id,))

            # Excluir colaboradores
            cursor.execute('DELETE FROM colaboradores WHERE empresa_id = ?', (empresa_id,))

        # Excluir registros da blocklist vinculados à empresa
        cursor.execute('DELETE FROM blocklist WHERE empresa_id = ?', (empresa_id,))

        # Excluir a empresa
        cursor.execute('DELETE FROM empresas WHERE id = ?', (empresa_id,))

        conn.commit()
        conn.close()

        # Registrar log
        descricao = f'Empresa excluída: {nome_empresa}'
        if excluir_colaboradores and qtd_colaboradores > 0:
            descricao += f' (incluindo {qtd_colaboradores} colaborador(es))'
        registrar_log(
            tipo_acao='EXCLUIR',
            categoria='EMPRESA',
            descricao=descricao,
            entidade_tipo='empresa',
            entidade_id=empresa_id,
            entidade_nome=nome_empresa
        )

        # Backup automático
        backup_database()

        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


# =============================================================================
# CRUD Colaboradores
# =============================================================================

def criar_colaborador(dados: dict) -> int:
    """Cria um novo colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    # Construir query dinamicamente
    campos = list(dados.keys())
    placeholders = ', '.join(['?' for _ in campos])
    campos_str = ', '.join(campos)
    valores = [dados[c] for c in campos]

    cursor.execute(f'''
        INSERT INTO colaboradores ({campos_str})
        VALUES ({placeholders})
    ''', valores)

    colaborador_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Registrar log
    nome = dados.get('nome_completo', 'Colaborador')
    registrar_log(
        tipo_acao='CRIAR',
        categoria='COLABORADOR',
        descricao=f'Novo colaborador cadastrado: {nome}',
        entidade_tipo='colaborador',
        entidade_id=colaborador_id,
        entidade_nome=nome
    )

    # Backup automático
    backup_database()

    return colaborador_id

def listar_colaboradores(filtro: str = None, status: str = 'ATIVO', empresa_id: int = None,
                         localizacao: str = None, limite: int = None, offset: int = None) -> List[Dict]:
    """Lista colaboradores com filtros opcionais e suporte a paginação."""
    conn = get_connection()
    cursor = conn.cursor()

    if localizacao:
        # Se filtrar por localização, fazer JOIN com a tabela de localizações
        query = '''
            SELECT c.*, e.razao_social as empresa_nome
            FROM colaboradores c
            LEFT JOIN empresas e ON c.empresa_id = e.id
            JOIN localizacoes l ON c.id = l.colaborador_id AND l.data_fim IS NULL
            WHERE 1=1
        '''
    else:
        query = 'SELECT c.*, e.razao_social as empresa_nome FROM colaboradores c LEFT JOIN empresas e ON c.empresa_id = e.id WHERE 1=1'
    params = []

    if status:
        query += ' AND c.status = ?'
        params.append(status)

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    if localizacao:
        query += ' AND l.local_nome = ?'
        params.append(localizacao)

    if filtro:
        query += ' AND (c.nome_completo LIKE ? OR c.cpf LIKE ?)'
        params.extend([f'%{filtro}%', f'%{filtro}%'])

    query += ' ORDER BY c.nome_completo'

    # Adicionar paginação
    if limite is not None:
        query += ' LIMIT ?'
        params.append(limite)
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)

    cursor.execute(query, params)
    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return colaboradores


def contar_colaboradores(filtro: str = None, status: str = 'ATIVO', empresa_id: int = None,
                         localizacao: str = None) -> int:
    """Conta o total de colaboradores com filtros opcionais."""
    conn = get_connection()
    cursor = conn.cursor()

    if localizacao:
        # Se filtrar por localização, fazer JOIN com a tabela de localizações
        query = '''
            SELECT COUNT(*) FROM colaboradores c
            JOIN localizacoes l ON c.id = l.colaborador_id AND l.data_fim IS NULL
            WHERE 1=1
        '''
    else:
        query = 'SELECT COUNT(*) FROM colaboradores c WHERE 1=1'
    params = []

    if status:
        query += ' AND c.status = ?'
        params.append(status)

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    if localizacao:
        query += ' AND l.local_nome = ?'
        params.append(localizacao)

    if filtro:
        query += ' AND (c.nome_completo LIKE ? OR c.cpf LIKE ?)'
        params.extend([f'%{filtro}%', f'%{filtro}%'])

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()
    return total

def obter_colaborador(colaborador_id: int) -> Optional[Dict]:
    """Obtém um colaborador pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, e.razao_social as empresa_nome, e.cnpj as empresa_cnpj
        FROM colaboradores c 
        LEFT JOIN empresas e ON c.empresa_id = e.id 
        WHERE c.id = ?
    ''', (colaborador_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_colaborador(colaborador_id: int, dados: dict) -> bool:
    """Atualiza os dados de um colaborador."""
    # Obter dados atuais para log
    colaborador_atual = obter_colaborador(colaborador_id)
    nome_colaborador = colaborador_atual.get('nome_completo', 'Colaborador') if colaborador_atual else 'Colaborador'

    conn = get_connection()
    cursor = conn.cursor()

    campos = []
    valores = []
    for key, value in dados.items():
        if key != 'id':
            campos.append(f"{key} = ?")
            valores.append(value)

    valores.append(colaborador_id)

    cursor.execute(f'''
        UPDATE colaboradores SET {', '.join(campos)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', valores)

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    # Registrar log para campos alterados
    if affected > 0 and colaborador_atual:
        campos_alterados = []
        for key, value in dados.items():
            if key != 'id':
                valor_anterior = colaborador_atual.get(key)
                if str(valor_anterior) != str(value):
                    campos_alterados.append(key)

        if campos_alterados:
            # Log específico para mudança de status
            if 'status' in dados:
                tipo_acao = 'DESATIVAR' if dados['status'] == 'INATIVO' else 'REATIVAR'
                registrar_log(
                    tipo_acao=tipo_acao,
                    categoria='COLABORADOR',
                    descricao=f'Status do colaborador alterado para {dados["status"]}',
                    entidade_tipo='colaborador',
                    entidade_id=colaborador_id,
                    entidade_nome=nome_colaborador,
                    valor_anterior=colaborador_atual.get('status'),
                    valor_novo=dados['status']
                )
            else:
                # Log genérico para outras alterações
                descricao = f'Dados do colaborador atualizados: {", ".join(campos_alterados[:5])}'
                if len(campos_alterados) > 5:
                    descricao += f' e mais {len(campos_alterados) - 5} campo(s)'
                registrar_log(
                    tipo_acao='EDITAR',
                    categoria='COLABORADOR',
                    descricao=descricao,
                    entidade_tipo='colaborador',
                    entidade_id=colaborador_id,
                    entidade_nome=nome_colaborador
                )

    # Backup automático
    backup_database()

    return affected > 0

def excluir_colaborador(colaborador_id: int) -> bool:
    """Exclui um colaborador (soft delete - muda status para INATIVO)."""
    return atualizar_colaborador(colaborador_id, {'status': 'INATIVO'})

def excluir_colaborador_permanente(colaborador_id: int) -> bool:
    """Exclui permanentemente um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM colaboradores WHERE id = ?', (colaborador_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def desligar_colaborador(colaborador_id: int, data_desligamento: str, motivo: str, observacoes: str = None) -> bool:
    """Desliga um colaborador e adiciona à blocklist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obter dados do colaborador
    colaborador = obter_colaborador(colaborador_id)
    if not colaborador:
        conn.close()
        return False
    
    # Atualizar status do colaborador
    cursor.execute('''
        UPDATE colaboradores 
        SET status = 'DESLIGADO', 
            data_desligamento = ?,
            motivo_desligamento = ?,
            observacoes_desligamento = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (data_desligamento, motivo, observacoes, colaborador_id))
    
    # Adicionar à blocklist
    cursor.execute('''
        INSERT INTO blocklist (cpf, nome, empresa_id, data_admissao, data_desligamento, 
                               motivo_desligamento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        colaborador.get('cpf'),
        colaborador.get('nome_completo'),
        colaborador.get('empresa_id'),
        colaborador.get('data_admissao'),
        data_desligamento,
        motivo,
        observacoes
    ))
    
    conn.commit()
    conn.close()
    
    backup_database()
    return True


# =============================================================================
# CRUD Dependentes
# =============================================================================

def adicionar_dependente(colaborador_id: int, dados: dict) -> int:
    """Adiciona um dependente a um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO dependentes (colaborador_id, nome, parentesco, data_nascimento, cpf)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        colaborador_id,
        dados.get('nome'),
        dados.get('parentesco'),
        dados.get('data_nascimento'),
        dados.get('cpf')
    ))
    
    dependente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dependente_id

def listar_dependentes(colaborador_id: int) -> List[Dict]:
    """Lista os dependentes de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dependentes WHERE colaborador_id = ? ORDER BY nome', (colaborador_id,))
    dependentes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dependentes

def excluir_dependente(dependente_id: int) -> bool:
    """Exclui um dependente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM dependentes WHERE id = ?', (dependente_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# =============================================================================
# Funções de Localizações
# =============================================================================

def atribuir_localizacao(colaborador_id: int, local_nome: str, cidade: str, uf: str,
                         data_inicio: str, observacoes: str = None) -> int:
    """
    Atribui uma nova localização ao colaborador.
    Encerra automaticamente a localização anterior (se houver).
    Não permite mais de uma alteração de localização no mesmo dia.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se já existe uma localização iniciada no mesmo dia
    cursor.execute('''
        SELECT id FROM localizacoes
        WHERE colaborador_id = ? AND data_inicio = ?
    ''', (colaborador_id, data_inicio))

    if cursor.fetchone():
        conn.close()
        raise ValueError("Já existe uma localização registrada para esta data. Não é permitido mais de uma alteração de localização no mesmo dia.")

    # Encerrar localização atual (se houver)
    cursor.execute('''
        UPDATE localizacoes
        SET data_fim = ?, updated_at = CURRENT_TIMESTAMP
        WHERE colaborador_id = ? AND data_fim IS NULL
    ''', (data_inicio, colaborador_id))

    # Inserir nova localização
    cursor.execute('''
        INSERT INTO localizacoes (colaborador_id, local_nome, cidade, uf, data_inicio, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (colaborador_id, local_nome, cidade, uf, data_inicio, observacoes))

    localizacao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return localizacao_id


def obter_localizacao_atual(colaborador_id: int) -> Optional[Dict]:
    """Obtém a localização atual do colaborador (data_fim IS NULL)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM localizacoes
        WHERE colaborador_id = ? AND data_fim IS NULL
        ORDER BY data_inicio DESC LIMIT 1
    ''', (colaborador_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def listar_localizacoes_colaborador(colaborador_id: int) -> List[Dict]:
    """Lista todas as localizações (histórico) de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM localizacoes
        WHERE colaborador_id = ?
        ORDER BY data_inicio DESC
    ''', (colaborador_id,))
    localizacoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return localizacoes


def encerrar_localizacao(localizacao_id: int, data_fim: str) -> bool:
    """Encerra uma localização específica."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE localizacoes
        SET data_fim = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (data_fim, localizacao_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def listar_locais_cadastrados() -> List[str]:
    """Lista todos os locais já cadastrados (para autocomplete)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT local_nome FROM localizacoes
        ORDER BY local_nome
    ''')
    locais = [row['local_nome'] for row in cursor.fetchall()]
    conn.close()
    return locais


def listar_colaboradores_por_localizacao(local_nome: str = None, cidade: str = None,
                                          uf: str = None) -> List[Dict]:
    """Lista colaboradores filtrados por localização atual."""
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT c.*, l.local_nome, l.cidade as loc_cidade, l.uf as loc_uf, l.data_inicio as loc_data_inicio,
               e.razao_social as empresa_nome
        FROM colaboradores c
        JOIN localizacoes l ON c.id = l.colaborador_id AND l.data_fim IS NULL
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO'
    '''
    params = []

    if local_nome:
        query += ' AND l.local_nome LIKE ?'
        params.append(f'%{local_nome}%')
    if cidade:
        query += ' AND l.cidade LIKE ?'
        params.append(f'%{cidade}%')
    if uf:
        query += ' AND l.uf = ?'
        params.append(uf)

    query += ' ORDER BY l.local_nome, c.nome_completo'

    cursor.execute(query, params)
    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return colaboradores


def contar_colaboradores_por_local() -> List[Dict]:
    """Conta quantos colaboradores estão em cada localização."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.local_nome, l.cidade, l.uf, COUNT(*) as qtd_colaboradores
        FROM localizacoes l
        JOIN colaboradores c ON l.colaborador_id = c.id
        WHERE l.data_fim IS NULL AND c.status = 'ATIVO'
        GROUP BY l.local_nome, l.cidade, l.uf
        ORDER BY qtd_colaboradores DESC
    ''')
    resultado = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultado


# =============================================================================
# Validações de CPF
# =============================================================================

def verificar_cpf_existente(cpf: str, colaborador_id: int = None) -> Dict:
    """
    Verifica se um CPF já existe no sistema.
    Retorna o colaborador encontrado ou None.
    Se colaborador_id for informado, ignora esse ID na busca (para edição).
    """
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    if not cpf_limpo:
        return None

    # Normalizar para 11 dígitos para garantir comparação correta
    cpf_normalizado = cpf_limpo.zfill(11) if len(cpf_limpo) < 11 else cpf_limpo[:11]

    conn = get_connection()
    cursor = conn.cursor()

    if colaborador_id:
        cursor.execute('''
            SELECT id, nome_completo, cpf, status FROM colaboradores
            WHERE cpf = ? AND id != ?
        ''', (cpf_normalizado, colaborador_id))
    else:
        cursor.execute('''
            SELECT id, nome_completo, cpf, status FROM colaboradores
            WHERE cpf = ?
        ''', (cpf_normalizado,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


# =============================================================================
# Block-list
# =============================================================================

def verificar_blocklist(cpf: str) -> List[Dict]:
    """Verifica se um CPF está na blocklist."""
    # Limpar e normalizar CPF para 11 dígitos
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    if cpf_limpo:
        cpf_limpo = cpf_limpo.zfill(11) if len(cpf_limpo) < 11 else cpf_limpo[:11]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.*, e.razao_social as empresa_nome
        FROM blocklist b
        LEFT JOIN empresas e ON b.empresa_id = e.id
        WHERE b.cpf = ?
        ORDER BY b.data_desligamento DESC
    ''', (cpf_limpo,))
    registros = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return registros

def listar_blocklist() -> List[Dict]:
    """Lista todos os registros da blocklist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.*, e.razao_social as empresa_nome
        FROM blocklist b
        LEFT JOIN empresas e ON b.empresa_id = e.id
        ORDER BY b.data_desligamento DESC
    ''')
    registros = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return registros


def listar_blocklist_agrupado() -> List[Dict]:
    """
    Lista os registros da blocklist agrupados por CPF.
    Cada colaborador aparece apenas uma vez, com um histórico de todas as entradas.

    Retorna uma lista de dicionários no formato:
    {
        'cpf': '12345678901',
        'nome': 'Nome do Colaborador',
        'total_entradas': 2,
        'historico': [
            {
                'id': 1,
                'empresa_nome': 'Empresa X',
                'data_admissao': '2023-01-01',
                'data_desligamento': '2023-06-01',
                'motivo_desligamento': 'Pedido de demissão',
                'observacoes': 'Observação...',
                'entrada_numero': 1
            },
            ...
        ],
        'ultima_entrada': {...}  # Referência ao registro mais recente
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar todos os registros ordenados por CPF e data de desligamento
    cursor.execute('''
        SELECT b.*, e.razao_social as empresa_nome
        FROM blocklist b
        LEFT JOIN empresas e ON b.empresa_id = e.id
        ORDER BY b.cpf, b.data_desligamento ASC
    ''')
    registros = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Agrupar por CPF
    agrupado = {}
    for reg in registros:
        cpf = reg.get('cpf', '')
        if not cpf:
            continue

        if cpf not in agrupado:
            agrupado[cpf] = {
                'cpf': cpf,
                'nome': reg.get('nome', ''),
                'historico': [],
                'total_entradas': 0
            }

        # Adicionar ao histórico com número da entrada
        agrupado[cpf]['total_entradas'] += 1
        entrada = {
            'id': reg.get('id'),
            'empresa_id': reg.get('empresa_id'),
            'empresa_nome': reg.get('empresa_nome', 'Não informada'),
            'data_admissao': reg.get('data_admissao'),
            'data_desligamento': reg.get('data_desligamento'),
            'motivo_desligamento': reg.get('motivo_desligamento'),
            'observacoes': reg.get('observacoes'),
            'pode_recontratar': reg.get('pode_recontratar'),
            'created_at': reg.get('created_at'),
            'entrada_numero': agrupado[cpf]['total_entradas']
        }
        agrupado[cpf]['historico'].append(entrada)
        # Atualizar nome para o mais recente (caso tenha mudado)
        agrupado[cpf]['nome'] = reg.get('nome', agrupado[cpf]['nome'])

    # Converter para lista e adicionar referência à última entrada
    resultado = []
    for cpf, dados in agrupado.items():
        # A última entrada é a mais recente (última do histórico ordenado por data)
        if dados['historico']:
            dados['ultima_entrada'] = dados['historico'][-1]
        resultado.append(dados)

    # Ordenar por data de desligamento mais recente (última entrada)
    resultado.sort(
        key=lambda x: x.get('ultima_entrada', {}).get('data_desligamento', '') or '',
        reverse=True
    )

    return resultado

def adicionar_blocklist(dados: dict) -> int:
    """Adiciona um registro manualmente à blocklist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO blocklist (cpf, nome, empresa_id, data_admissao, data_desligamento,
                               motivo_desligamento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados.get('cpf'),
        dados.get('nome'),
        dados.get('empresa_id'),
        dados.get('data_admissao'),
        dados.get('data_desligamento'),
        dados.get('motivo_desligamento'),
        dados.get('observacoes'),
    ))

    registro_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Registrar log
    nome = dados.get('nome', 'Colaborador')
    motivo = dados.get('motivo_desligamento', 'Não informado')
    registrar_log(
        tipo_acao='CRIAR',
        categoria='BLOCKLIST',
        descricao=f'Colaborador adicionado à Block-List: {nome} - Motivo: {motivo}',
        entidade_tipo='blocklist',
        entidade_id=registro_id,
        entidade_nome=nome
    )

    return registro_id


def atualizar_blocklist(registro_id: int, observacoes: str) -> bool:
    """Atualiza a justificativa de um registro na blocklist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE blocklist SET observacoes = ? WHERE id = ?
    ''', (observacoes, registro_id))

    conn.commit()
    conn.close()
    return True


def remover_blocklist(registro_id: int) -> bool:
    """Remove um registro da blocklist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Obter dados antes de excluir
    cursor.execute('SELECT nome, cpf FROM blocklist WHERE id = ?', (registro_id,))
    registro = cursor.fetchone()

    cursor.execute('DELETE FROM blocklist WHERE id = ?', (registro_id,))

    conn.commit()
    conn.close()

    # Registrar log
    if registro:
        registrar_log(
            tipo_acao='EXCLUIR',
            categoria='BLOCKLIST',
            descricao=f'Registro removido da Block-List: {registro["nome"]}',
            entidade_tipo='blocklist',
            entidade_id=registro_id,
            entidade_nome=registro['nome']
        )

    return True


# =============================================================================
# Contratos de Experiência
# =============================================================================

def criar_contrato_experiencia(colaborador_id: int, data_inicio: str, prazo_inicial: int,
                                prorrogacao: int = None) -> int:
    """
    Cria um contrato de experiência.
    - Verifica se já existe um contrato vigente para o colaborador
    - Valida que o total não exceda 90 dias (CLT)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se já existe contrato vigente para este colaborador
    cursor.execute('''
        SELECT id FROM contratos_experiencia
        WHERE colaborador_id = ? AND status = 'VIGENTE'
    ''', (colaborador_id,))

    contrato_existente = cursor.fetchone()
    if contrato_existente:
        # Já existe contrato vigente, não criar duplicado
        conn.close()
        return contrato_existente['id']

    # Validar limite de 90 dias (CLT)
    total_dias = prazo_inicial + (prorrogacao or 0)
    if total_dias > 90:
        conn.close()
        raise ValueError(f"O contrato de experiência não pode exceder 90 dias. Total solicitado: {total_dias} dias")

    # Calcular datas
    # O dia de início conta como dia 1, então o fim é início + prazo - 1
    from datetime import datetime, timedelta
    inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
    fim_inicial = inicio + timedelta(days=prazo_inicial - 1)
    fim_prorrogacao = None

    if prorrogacao:
        # A prorrogação começa no dia seguinte ao fim do período inicial
        fim_prorrogacao = fim_inicial + timedelta(days=prorrogacao)

    cursor.execute('''
        INSERT INTO contratos_experiencia (colaborador_id, data_inicio, prazo_inicial,
                                           data_fim_inicial, prorrogacao, data_fim_prorrogacao)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        colaborador_id,
        data_inicio,
        prazo_inicial,
        fim_inicial.strftime('%Y-%m-%d'),
        prorrogacao,
        fim_prorrogacao.strftime('%Y-%m-%d') if fim_prorrogacao else None
    ))

    contrato_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return contrato_id

def listar_contratos_vencendo(dias_antecedencia: int = 5) -> List[Dict]:
    """Lista contratos de experiência próximos do vencimento."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ce.*, c.nome_completo, c.funcao, e.razao_social as empresa_nome
        FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE ce.status = 'VIGENTE'
        AND (
            (ce.prorrogacao IS NULL AND date(ce.data_fim_inicial) <= date('now', '+' || ? || ' days'))
            OR (ce.prorrogacao IS NOT NULL AND date(ce.data_fim_prorrogacao) <= date('now', '+' || ? || ' days'))
        )
        ORDER BY COALESCE(ce.data_fim_prorrogacao, ce.data_fim_inicial)
    ''', (dias_antecedencia, dias_antecedencia))

    contratos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return contratos


def listar_todos_contratos_experiencia() -> List[Dict]:
    """Lista todos os contratos de experiência vigentes com informações detalhadas."""
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar contratos da tabela contratos_experiencia
    # Se tem prorrogação, a data final é sempre data_fim_prorrogacao
    # O período atual é determinado se já passou do período inicial ou não
    cursor.execute('''
        SELECT ce.id, ce.colaborador_id, ce.data_inicio, ce.prazo_inicial, ce.data_fim_inicial,
               ce.prorrogacao, ce.data_fim_prorrogacao, ce.status,
               c.nome_completo, c.funcao, c.status as colaborador_status,
               e.razao_social as empresa_nome,
               CASE
                   WHEN ce.prorrogacao IS NOT NULL AND date('now', 'localtime') > date(ce.data_fim_inicial) THEN 2
                   ELSE 1
               END as periodo_atual,
               CASE
                   WHEN ce.prorrogacao IS NOT NULL THEN ce.data_fim_prorrogacao
                   ELSE ce.data_fim_inicial
               END as proxima_data_vencimento,
               CAST(julianday(
                   CASE
                       WHEN ce.prorrogacao IS NOT NULL THEN ce.data_fim_prorrogacao
                       ELSE ce.data_fim_inicial
                   END
               ) - julianday(date('now', 'localtime')) AS INTEGER) as dias_restantes
        FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE ce.status = 'VIGENTE'
        AND c.status = 'ATIVO'
    ''')

    contratos = [dict(row) for row in cursor.fetchall()]

    # Buscar colaboradores com tipo_contrato = 'Contrato de Experiência' que NÃO têm registro na tabela
    cursor.execute('''
        SELECT c.id as colaborador_id, c.nome_completo, c.funcao, c.status as colaborador_status,
               c.data_admissao as data_inicio, c.prazo_experiencia as prazo_inicial,
               c.prorrogacao, e.razao_social as empresa_nome
        FROM colaboradores c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        LEFT JOIN contratos_experiencia ce ON c.id = ce.colaborador_id AND ce.status = 'VIGENTE'
        WHERE c.tipo_contrato = 'Contrato de Experiência'
        AND c.status = 'ATIVO'
        AND ce.id IS NULL
        AND c.data_admissao IS NOT NULL
        AND c.prazo_experiencia IS NOT NULL
    ''')

    colaboradores_sem_contrato = cursor.fetchall()
    conn.close()

    # Para colaboradores sem registro na tabela, calcular as datas
    for colab in colaboradores_sem_contrato:
        colab = dict(colab)
        try:
            inicio = datetime.strptime(colab['data_inicio'], '%Y-%m-%d')
            prazo = colab['prazo_inicial']
            prorrogacao = colab.get('prorrogacao')

            # A data_fim_inicial é calculada como: data_inicio + prazo_inicial - 1
            # Porque o dia de início conta como dia 1 do contrato
            fim_inicial = inicio + timedelta(days=prazo - 1)
            fim_prorrogacao = None
            if prorrogacao:
                # A prorrogação começa no dia seguinte ao fim do período inicial
                fim_prorrogacao = fim_inicial + timedelta(days=prorrogacao)

            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Determinar período atual e próxima data de vencimento
            # Se tem prorrogação, a data final é sempre a data_fim_prorrogacao
            if prorrogacao:
                # Com prorrogação: a data final é sempre a prorrogação
                proxima_data = fim_prorrogacao
                # Período atual depende se já passou do período inicial
                if hoje > fim_inicial:
                    periodo_atual = 2
                else:
                    periodo_atual = 1
            else:
                # Sem prorrogação: apenas o período inicial
                periodo_atual = 1
                proxima_data = fim_inicial

            dias_restantes = (proxima_data - hoje).days

            colab['data_fim_inicial'] = fim_inicial.strftime('%Y-%m-%d')
            colab['data_fim_prorrogacao'] = fim_prorrogacao.strftime('%Y-%m-%d') if fim_prorrogacao else None
            colab['periodo_atual'] = periodo_atual
            colab['proxima_data_vencimento'] = proxima_data.strftime('%Y-%m-%d')
            colab['dias_restantes'] = dias_restantes
            colab['status'] = 'VIGENTE'
            colab['id'] = None  # Não tem ID de contrato

            contratos.append(colab)
        except Exception:
            pass  # Ignorar registros com dados inválidos

    # Ordenar por dias restantes
    contratos.sort(key=lambda x: x.get('dias_restantes', 9999))

    return contratos

def obter_contrato_colaborador(colaborador_id: int) -> Optional[Dict]:
    """Obtém o contrato de experiência vigente de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM contratos_experiencia 
        WHERE colaborador_id = ? AND status = 'VIGENTE'
        ORDER BY created_at DESC LIMIT 1
    ''', (colaborador_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_contrato(contrato_id: int, dados: dict) -> bool:
    """Atualiza um contrato de experiência."""
    conn = get_connection()
    cursor = conn.cursor()
    
    campos = []
    valores = []
    for key, value in dados.items():
        if key != 'id':
            campos.append(f"{key} = ?")
            valores.append(value)
    
    valores.append(contrato_id)
    
    cursor.execute(f'''
        UPDATE contratos_experiencia SET {', '.join(campos)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', valores)
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def resetar_prorrogacoes_contratos():
    """Remove todas as prorrogações dos contratos (para correção de dados)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Resetar contratos_experiencia
    cursor.execute('''
        UPDATE contratos_experiencia
        SET prorrogacao = NULL, data_fim_prorrogacao = NULL, updated_at = CURRENT_TIMESTAMP
    ''')

    # Resetar colaboradores
    cursor.execute('''
        UPDATE colaboradores
        SET prorrogacao = NULL
        WHERE tipo_contrato = 'Contrato de Experiência'
    ''')

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected


def converter_contratos_vencidos_para_clt() -> List[Dict]:
    """
    Verifica contratos de experiência vencidos e converte automaticamente para CLT.

    Um contrato é considerado vencido quando:
    - Se tem prorrogação: a data_fim_prorrogacao já passou
    - Se não tem prorrogação: a data_fim_inicial já passou

    Retorna lista de colaboradores convertidos para log/notificação.
    """
    conn = get_connection()
    cursor = conn.cursor()

    convertidos = []
    hoje = date.today().strftime('%Y-%m-%d')

    # Buscar contratos vigentes que já venceram
    cursor.execute('''
        SELECT ce.id as contrato_id, ce.colaborador_id, ce.data_fim_inicial,
               ce.prorrogacao, ce.data_fim_prorrogacao,
               c.nome_completo, c.tipo_contrato
        FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        WHERE ce.status = 'VIGENTE'
        AND c.status = 'ATIVO'
        AND c.tipo_contrato = 'Contrato de Experiência'
        AND (
            (ce.prorrogacao IS NOT NULL AND date(ce.data_fim_prorrogacao) < date(?))
            OR (ce.prorrogacao IS NULL AND date(ce.data_fim_inicial) < date(?))
        )
    ''', (hoje, hoje))

    contratos_vencidos = cursor.fetchall()

    for contrato in contratos_vencidos:
        contrato = dict(contrato)
        colaborador_id = contrato['colaborador_id']
        contrato_id = contrato['contrato_id']

        # Atualizar o tipo de contrato do colaborador para CLT
        cursor.execute('''
            UPDATE colaboradores
            SET tipo_contrato = 'CLT',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (colaborador_id,))

        # Encerrar o contrato de experiência
        cursor.execute('''
            UPDATE contratos_experiencia
            SET status = 'EFETIVADO',
                observacoes = COALESCE(observacoes || ' | ', '') || 'Convertido automaticamente para CLT em ' || ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (hoje, contrato_id))

        convertidos.append({
            'colaborador_id': colaborador_id,
            'nome': contrato['nome_completo'],
            'data_conversao': hoje
        })

    # Também verificar colaboradores com tipo_contrato = 'Contrato de Experiência'
    # que NÃO têm registro na tabela contratos_experiencia mas têm dados de experiência
    cursor.execute('''
        SELECT c.id as colaborador_id, c.nome_completo, c.data_admissao,
               c.prazo_experiencia, c.prorrogacao
        FROM colaboradores c
        LEFT JOIN contratos_experiencia ce ON c.id = ce.colaborador_id AND ce.status = 'VIGENTE'
        WHERE c.tipo_contrato = 'Contrato de Experiência'
        AND c.status = 'ATIVO'
        AND ce.id IS NULL
        AND c.data_admissao IS NOT NULL
        AND c.prazo_experiencia IS NOT NULL
    ''')

    colaboradores_sem_contrato = cursor.fetchall()

    for colab in colaboradores_sem_contrato:
        colab = dict(colab)
        try:
            inicio = datetime.strptime(colab['data_admissao'], '%Y-%m-%d')
            prazo = colab['prazo_experiencia']
            prorrogacao = colab.get('prorrogacao')

            # Calcular data fim
            fim_inicial = inicio + timedelta(days=prazo - 1)

            if prorrogacao:
                data_fim = fim_inicial + timedelta(days=prorrogacao)
            else:
                data_fim = fim_inicial

            hoje_dt = datetime.strptime(hoje, '%Y-%m-%d')

            # Se venceu, converter para CLT
            if data_fim < hoje_dt:
                cursor.execute('''
                    UPDATE colaboradores
                    SET tipo_contrato = 'CLT',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (colab['colaborador_id'],))

                convertidos.append({
                    'colaborador_id': colab['colaborador_id'],
                    'nome': colab['nome_completo'],
                    'data_conversao': hoje
                })
        except Exception:
            pass  # Ignorar registros com dados inválidos

    conn.commit()
    conn.close()

    return convertidos


# =============================================================================
# Gestão de Férias
# =============================================================================

def criar_periodo_ferias(colaborador_id: int, data_admissao: str) -> int:
    """Cria um período aquisitivo de férias baseado na data de admissão."""
    conn = get_connection()
    cursor = conn.cursor()
    
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    admissao = datetime.strptime(data_admissao, '%Y-%m-%d')

    # Período aquisitivo: 12 meses a partir da admissão
    periodo_inicio = admissao
    periodo_fim = admissao + relativedelta(years=1) - timedelta(days=1)

    # Período concessivo: 11 meses após o fim do período aquisitivo
    concessivo_limite = periodo_fim + relativedelta(months=11)
    
    cursor.execute('''
        INSERT INTO ferias (colaborador_id, periodo_aquisitivo_inicio, periodo_aquisitivo_fim,
                           periodo_concessivo_limite, dias_direito)
        VALUES (?, ?, ?, ?, 30)
    ''', (
        colaborador_id,
        periodo_inicio.strftime('%Y-%m-%d'),
        periodo_fim.strftime('%Y-%m-%d'),
        concessivo_limite.strftime('%Y-%m-%d')
    ))
    
    ferias_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ferias_id

def listar_ferias_vencendo(meses_antecedencia: int = 6) -> List[Dict]:
    """Lista férias com período concessivo próximo do vencimento (em meses)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT f.*, c.nome_completo, c.funcao, e.razao_social as empresa_nome
        FROM ferias f
        JOIN colaboradores c ON f.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE f.status = 'PENDENTE'
        AND c.status = 'ATIVO'
        AND date(f.periodo_concessivo_limite) <= date('now', '+' || ? || ' months')
        ORDER BY f.periodo_concessivo_limite
    ''', (meses_antecedencia,))

    ferias = [dict(row) for row in cursor.fetchall()]

    # Buscar últimas férias gozadas para cada colaborador
    for f in ferias:
        cursor.execute('''
            SELECT pf.data_inicio, pf.data_fim, pf.dias
            FROM periodos_ferias pf
            JOIN ferias fer ON pf.ferias_id = fer.id
            WHERE fer.colaborador_id = ?
            ORDER BY pf.data_fim DESC
            LIMIT 1
        ''', (f['colaborador_id'],))

        ultima = cursor.fetchone()
        if ultima:
            f['ultimas_ferias_inicio'] = ultima[0]
            f['ultimas_ferias_fim'] = ultima[1]
            f['ultimas_ferias_dias'] = ultima[2]
        else:
            f['ultimas_ferias_inicio'] = None
            f['ultimas_ferias_fim'] = None
            f['ultimas_ferias_dias'] = None

    conn.close()
    return ferias


def listar_ferias_vencendo_dias(dias_antecedencia: int = 90) -> List[Dict]:
    """Lista férias com período concessivo próximo do vencimento (em dias)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT f.*, c.nome_completo, c.funcao, e.razao_social as empresa_nome,
               CAST(julianday(f.periodo_concessivo_limite) - julianday(date('now', 'localtime')) AS INTEGER) as dias_restantes
        FROM ferias f
        JOIN colaboradores c ON f.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE f.status = 'PENDENTE'
        AND c.status = 'ATIVO'
        AND date(f.periodo_concessivo_limite) <= date('now', '+' || ? || ' days')
        ORDER BY f.periodo_concessivo_limite
    ''', (dias_antecedencia,))

    ferias = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ferias

def listar_ferias_colaborador(colaborador_id: int) -> List[Dict]:
    """Lista todos os períodos de férias de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ferias WHERE colaborador_id = ? ORDER BY periodo_aquisitivo_inicio DESC
    ''', (colaborador_id,))
    ferias = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ferias

def registrar_gozo_ferias(ferias_id: int, data_inicio: str, data_fim: str,
                          dias: int, abono_pecuniario: bool = False, observacoes: str = None) -> int:
    """Registra um período de gozo de férias."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO periodos_ferias (ferias_id, data_inicio, data_fim, dias, abono_pecuniario, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ferias_id, data_inicio, data_fim, dias, 1 if abono_pecuniario else 0, observacoes))

    periodo_id = cursor.lastrowid

    # Atualizar dias gozados/vendidos
    if abono_pecuniario:
        cursor.execute('''
            UPDATE ferias SET dias_vendidos = dias_vendidos + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (dias, ferias_id))
    else:
        cursor.execute('''
            UPDATE ferias SET dias_gozados = dias_gozados + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (dias, ferias_id))

    # Verificar se completou as férias
    cursor.execute('''
        SELECT COALESCE(dias_direito, 30) as dias_direito, COALESCE(dias_gozados, 0) as dias_gozados,
               COALESCE(dias_vendidos, 0) as dias_vendidos, colaborador_id, periodo_aquisitivo_fim
        FROM ferias WHERE id = ?
    ''', (ferias_id,))
    row = cursor.fetchone()
    if row:
        total_usado = row['dias_gozados'] + row['dias_vendidos']
        dias_direito = row['dias_direito'] if row['dias_direito'] else 30
        if total_usado >= dias_direito:
            cursor.execute('''
                UPDATE ferias SET status = 'CONCLUIDO', updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (ferias_id,))

            # Criar próximo período aquisitivo automaticamente baseado na data de RETORNO das férias
            from dateutil.relativedelta import relativedelta

            # Buscar a data de fim do último período de gozo (data de retorno = data_fim + 1)
            cursor.execute('''
                SELECT data_fim FROM periodos_ferias
                WHERE ferias_id = ?
                ORDER BY data_fim DESC LIMIT 1
            ''', (ferias_id,))
            ultimo_gozo = cursor.fetchone()

            if ultimo_gozo:
                # Data de retorno = dia seguinte ao fim das férias
                data_retorno = datetime.strptime(ultimo_gozo['data_fim'], '%Y-%m-%d') + timedelta(days=1)
            else:
                # Fallback: usar fim do período aquisitivo atual + 1
                data_retorno = datetime.strptime(row['periodo_aquisitivo_fim'], '%Y-%m-%d') + timedelta(days=1)

            # Novo período aquisitivo: da data de retorno até 1 ano depois
            # Ex: retorno 03/02/2024 -> aquisitivo 03/02/2024 a 02/02/2025
            proximo_inicio = data_retorno
            proximo_fim = proximo_inicio + relativedelta(years=1) - timedelta(days=1)
            # Período concessivo: começa no dia seguinte ao fim do aquisitivo e dura 11 meses
            # Ex: concessivo 03/02/2025 a 02/01/2026
            concessivo_limite = proximo_fim + relativedelta(months=11)

            # Verificar se já existe um período que engloba essa data
            cursor.execute('''
                SELECT id FROM ferias
                WHERE colaborador_id = ?
                AND status = 'PENDENTE'
                AND periodo_aquisitivo_inicio >= ?
            ''', (row['colaborador_id'], proximo_inicio.strftime('%Y-%m-%d')))

            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO ferias (colaborador_id, periodo_aquisitivo_inicio, periodo_aquisitivo_fim,
                                       periodo_concessivo_limite, dias_direito)
                    VALUES (?, ?, ?, ?, 30)
                ''', (
                    row['colaborador_id'],
                    proximo_inicio.strftime('%Y-%m-%d'),
                    proximo_fim.strftime('%Y-%m-%d'),
                    concessivo_limite.strftime('%Y-%m-%d')
                ))

    conn.commit()
    conn.close()
    return periodo_id


def listar_periodos_ferias_gozados(ferias_id: int) -> List[Dict]:
    """Lista os períodos de férias já gozados de um período aquisitivo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM periodos_ferias WHERE ferias_id = ? ORDER BY data_inicio
    ''', (ferias_id,))
    periodos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return periodos


def sincronizar_ferias_colaborador(colaborador_id: int):
    """
    Sincroniza os períodos de férias de um colaborador, garantindo que:
    1. Períodos sem gozo registrado voltem para PENDENTE
    2. Períodos com todos os dias gozados estejam como CONCLUIDO
    3. Remove períodos futuros órfãos (criados automaticamente mas sem o período anterior concluído)
    """
    from dateutil.relativedelta import relativedelta

    conn = get_connection()
    cursor = conn.cursor()

    # Buscar todos os períodos de férias do colaborador
    cursor.execute('''
        SELECT f.id, f.periodo_aquisitivo_inicio, f.periodo_aquisitivo_fim, f.status,
               f.dias_direito, f.dias_gozados, f.dias_vendidos
        FROM ferias f
        WHERE f.colaborador_id = ?
        ORDER BY f.periodo_aquisitivo_inicio ASC
    ''', (colaborador_id,))
    ferias_list = cursor.fetchall()

    for f in ferias_list:
        ferias_id = f['id']
        dias_direito = f['dias_direito'] or 30
        status_atual = f['status']

        # Contar dias realmente gozados/vendidos nos períodos registrados
        cursor.execute('''
            SELECT COALESCE(SUM(CASE WHEN abono_pecuniario = 0 THEN dias ELSE 0 END), 0) as dias_gozados,
                   COALESCE(SUM(CASE WHEN abono_pecuniario = 1 THEN dias ELSE 0 END), 0) as dias_vendidos
            FROM periodos_ferias
            WHERE ferias_id = ?
        ''', (ferias_id,))
        resultado = cursor.fetchone()
        dias_gozados_real = resultado['dias_gozados']
        dias_vendidos_real = resultado['dias_vendidos']
        total_usado = dias_gozados_real + dias_vendidos_real

        # Atualizar dias gozados/vendidos se estiverem diferentes
        if f['dias_gozados'] != dias_gozados_real or f['dias_vendidos'] != dias_vendidos_real:
            cursor.execute('''
                UPDATE ferias SET dias_gozados = ?, dias_vendidos = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (dias_gozados_real, dias_vendidos_real, ferias_id))

        # Determinar status correto
        if total_usado >= dias_direito:
            novo_status = 'CONCLUIDO'
        else:
            novo_status = 'PENDENTE'

        # Atualizar status se necessário
        if status_atual != novo_status:
            cursor.execute('''
                UPDATE ferias SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (novo_status, ferias_id))

    # Remover períodos futuros órfãos (PENDENTE sem período anterior CONCLUIDO)
    cursor.execute('''
        SELECT f.id, f.periodo_aquisitivo_inicio
        FROM ferias f
        WHERE f.colaborador_id = ? AND f.status = 'PENDENTE'
        ORDER BY f.periodo_aquisitivo_inicio ASC
    ''', (colaborador_id,))
    pendentes = cursor.fetchall()

    # Verificar se há mais de um período pendente (o que indicaria inconsistência)
    if len(pendentes) > 1:
        # Manter apenas o mais antigo, deletar os outros
        for p in pendentes[1:]:
            # Verificar se tem períodos de gozo
            cursor.execute('SELECT COUNT(*) as cnt FROM periodos_ferias WHERE ferias_id = ?', (p['id'],))
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute('DELETE FROM ferias WHERE id = ?', (p['id'],))

    conn.commit()
    conn.close()


def obter_ferias_pendente(colaborador_id: int) -> Optional[Dict]:
    """Obtém o período de férias pendente mais antigo do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ferias
        WHERE colaborador_id = ? AND status = 'PENDENTE'
        ORDER BY periodo_aquisitivo_inicio ASC LIMIT 1
    ''', (colaborador_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def listar_colaboradores_em_ferias() -> List[Dict]:
    """
    Lista todos os colaboradores que estão de férias hoje.
    Um colaborador está de férias se a data atual está dentro de um período
    registrado na tabela periodos_ferias e não é abono pecuniário.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT c.id, c.nome_completo, c.funcao, c.foto_path,
               e.razao_social as empresa_nome,
               pf.data_inicio, pf.data_fim, pf.dias
        FROM periodos_ferias pf
        JOIN ferias f ON pf.ferias_id = f.id
        JOIN colaboradores c ON f.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE date('now', 'localtime') BETWEEN date(pf.data_inicio) AND date(pf.data_fim)
        AND pf.abono_pecuniario = 0
        AND c.status = 'ATIVO'
        ORDER BY c.nome_completo
    ''')

    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return colaboradores


def atualizar_ferias_por_admissao(colaborador_id: int, nova_data_admissao: str):
    """
    Atualiza os períodos de férias quando a data de admissão é alterada.
    - Períodos ANTERIORES à nova data de admissão: são SEMPRE deletados (dados inconsistentes)
    - Períodos posteriores sem gozo: são deletados e recriados
    - Ao final, cria um novo período baseado na nova data de admissão
    """
    conn = get_connection()
    cursor = conn.cursor()

    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    # Converter nova data de admissão para comparação
    nova_admissao = datetime.strptime(nova_data_admissao, '%Y-%m-%d')

    # Buscar todos os períodos de férias do colaborador
    cursor.execute('''
        SELECT f.id, f.periodo_aquisitivo_inicio, f.dias_gozados, f.dias_vendidos, f.status
        FROM ferias f
        WHERE f.colaborador_id = ?
    ''', (colaborador_id,))

    ferias_existentes = cursor.fetchall()

    # Se não há férias, criar o primeiro período
    if not ferias_existentes:
        conn.close()
        criar_periodo_ferias(colaborador_id, nova_data_admissao)
        return

    ids_para_deletar = []

    for f in ferias_existentes:
        ferias_id = f['id']
        periodo_inicio_str = f['periodo_aquisitivo_inicio']

        # Converter data do período para comparação
        try:
            periodo_inicio = datetime.strptime(periodo_inicio_str, '%Y-%m-%d')
        except:
            periodo_inicio = None

        # REGRA 1: Se o período aquisitivo começa ANTES da nova data de admissão,
        # é um dado inconsistente e deve ser deletado (independente de ter gozo ou não)
        if periodo_inicio and periodo_inicio < nova_admissao:
            ids_para_deletar.append(ferias_id)
            # Deletar também os períodos de gozo associados
            cursor.execute('DELETE FROM periodos_ferias WHERE ferias_id = ?', (ferias_id,))
            continue

        # REGRA 2: Para períodos posteriores à admissão, verificar se tem gozo
        # Verificar se tem períodos de gozo na tabela periodos_ferias
        cursor.execute('''
            SELECT COUNT(*) as total FROM periodos_ferias WHERE ferias_id = ?
        ''', (ferias_id,))
        resultado = cursor.fetchone()
        tem_periodo_gozo = resultado['total'] > 0 if resultado else False

        # Verificar se tem dias gozados ou vendidos marcados
        tem_dias_usados = f['dias_gozados'] > 0 or f['dias_vendidos'] > 0

        # Se não tem nenhum uso, marcar para deletar
        if not tem_periodo_gozo and not tem_dias_usados:
            ids_para_deletar.append(ferias_id)

    # Deletar os períodos marcados
    if ids_para_deletar:
        placeholders = ','.join(['?' for _ in ids_para_deletar])
        cursor.execute(f'DELETE FROM ferias WHERE id IN ({placeholders})', ids_para_deletar)

    conn.commit()
    conn.close()

    # Criar novo período baseado na nova data de admissão
    criar_periodo_ferias(colaborador_id, nova_data_admissao)


# =============================================================================
# Banco de Talentos (Todos os colaboradores)
# =============================================================================

def listar_banco_talentos(filtro: str = None, empresa_id: int = None) -> List[Dict]:
    """
    Lista TODOS os colaboradores que já passaram pelo sistema,
    independente de status (ativo, inativo, blocklist, etc).
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT c.*, e.razao_social as empresa_nome,
               CASE
                   WHEN c.status = 'ATIVO' THEN 'Ativo'
                   WHEN c.status = 'INATIVO' AND EXISTS (
                       SELECT 1 FROM blocklist b WHERE b.cpf = c.cpf
                   ) THEN 'Block-List'
                   WHEN c.status = 'INATIVO' THEN 'Inativo'
                   ELSE c.status
               END as status_detalhado,
               (SELECT 1 FROM blocklist b WHERE b.cpf = c.cpf LIMIT 1) as na_blocklist
        FROM colaboradores c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE 1=1
    '''
    params = []

    if filtro:
        query += ' AND (c.nome_completo LIKE ? OR c.cpf LIKE ?)'
        params.extend([f'%{filtro}%', f'%{filtro}%'])

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    query += ' ORDER BY c.nome_completo'

    cursor.execute(query, params)
    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return colaboradores


def obter_estatisticas_banco_talentos() -> Dict:
    """Retorna estatísticas do banco de talentos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Total de colaboradores
    cursor.execute('SELECT COUNT(*) FROM colaboradores')
    total = cursor.fetchone()[0]

    # Ativos
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO'")
    ativos = cursor.fetchone()[0]

    # Inativos (não na blocklist)
    cursor.execute('''
        SELECT COUNT(*) FROM colaboradores c
        WHERE c.status = 'INATIVO'
        AND NOT EXISTS (SELECT 1 FROM blocklist b WHERE b.cpf = c.cpf)
    ''')
    inativos = cursor.fetchone()[0]

    # Na blocklist (contar CPFs únicos, não registros)
    cursor.execute('SELECT COUNT(DISTINCT cpf) FROM blocklist')
    blocklist = cursor.fetchone()[0]

    conn.close()

    return {
        'total': total,
        'ativos': ativos,
        'inativos': inativos,
        'blocklist': blocklist,
    }


# =============================================================================
# Aniversariantes
# =============================================================================

def listar_aniversariantes_mes(mes: int = None) -> List[Dict]:
    """Lista os aniversariantes do mês."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if mes is None:
        mes = datetime.now().month
    
    cursor.execute('''
        SELECT c.id, c.nome_completo, c.data_nascimento, c.funcao, c.departamento,
               e.razao_social as empresa_nome
        FROM colaboradores c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO'
        AND strftime('%m', c.data_nascimento) = ?
        ORDER BY strftime('%d', c.data_nascimento)
    ''', (f'{mes:02d}',))
    
    aniversariantes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return aniversariantes


# =============================================================================
# Exportação
# =============================================================================

def exportar_colaboradores_dict(status: str = None, empresa_id: int = None) -> List[Dict]:
    """Exporta colaboradores como lista de dicionários."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT c.*, e.razao_social as empresa_nome, e.cnpj as empresa_cnpj
        FROM colaboradores c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE 1=1
    '''
    params = []
    
    if status:
        query += ' AND c.status = ?'
        params.append(status)
    
    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)
    
    query += ' ORDER BY c.nome_completo'
    
    cursor.execute(query, params)
    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return colaboradores


# =============================================================================
# Histórico de Alterações
# =============================================================================

# Mapeamento de nomes de campos para nomes legíveis
CAMPOS_LEGIVEIS = {
    'nome_completo': 'Nome Completo',
    'endereco': 'Endereço',
    'numero': 'Número',
    'complemento': 'Complemento',
    'bairro': 'Bairro',
    'cep': 'CEP',
    'cidade': 'Cidade',
    'uf_endereco': 'UF Endereço',
    'telefone': 'Telefone',
    'celular': 'Celular',
    'email': 'E-mail',
    'data_nascimento': 'Data de Nascimento',
    'naturalidade': 'Naturalidade',
    'uf_naturalidade': 'UF Naturalidade',
    'sexo': 'Sexo',
    'grau_instrucao': 'Grau de Instrução',
    'estado_civil': 'Estado Civil',
    'deficiencia': 'Deficiência',
    'nome_mae': 'Nome da Mãe',
    'cpf_mae': 'CPF da Mãe',
    'nome_pai': 'Nome do Pai',
    'cpf_pai': 'CPF do Pai',
    'cpf': 'CPF',
    'rg': 'RG',
    'orgao_emissor_rg': 'Órgão Emissor RG',
    'uf_rg': 'UF RG',
    'carteira_profissional': 'CTPS',
    'serie_carteira': 'Série CTPS',
    'uf_carteira': 'UF CTPS',
    'pis': 'PIS',
    'titulo_eleitor': 'Título de Eleitor',
    'zona_eleitor': 'Zona Eleitoral',
    'secao_eleitor': 'Seção Eleitoral',
    'habilitacao': 'CNH',
    'tipo_cnh': 'Tipo CNH',
    'validade_cnh': 'Validade CNH',
    'reservista': 'Reservista',
    'data_admissao': 'Data de Admissão',
    'funcao': 'Função',
    'departamento': 'Departamento',
    'salario': 'Salário',
    'forma_pagamento': 'Forma de Pagamento',
    'tipo_contrato': 'Tipo de Contrato',
    'prazo_experiencia': 'Prazo de Experiência',
    'prorrogacao': 'Prorrogação',
    'horario_trabalho': 'Horário de Trabalho',
    'dias_trabalho': 'Dias de Trabalho',
    'intervalo': 'Intervalo',
    'vale_transporte': 'Vale Transporte',
    'vale_alimentacao': 'Vale Alimentação',
    'vale_refeicao': 'Vale Refeição',
    'assistencia_medica': 'Assistência Médica',
    'assistencia_odontologica': 'Assistência Odontológica',
    'seguro_vida': 'Seguro de Vida',
    'tipo_conta': 'Tipo de Conta',
    'banco': 'Banco',
    'agencia': 'Agência',
    'conta': 'Conta',
    'observacoes_gerais': 'Observações Gerais',
    'status': 'Status',
    'empresa_id': 'Empresa',
    'foto_path': 'Foto',
    'motivo_inativacao': 'Motivo da Inativação',
    'submotivo_inativacao': 'Submotivo da Inativação',
    'data_inativacao': 'Data da Inativação',
}


def registrar_alteracao(colaborador_id: int, campo: str, valor_anterior: str, valor_novo: str):
    """Registra uma alteração no histórico do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO historico_alteracoes (colaborador_id, campo, valor_anterior, valor_novo)
        VALUES (?, ?, ?, ?)
    ''', (colaborador_id, campo, str(valor_anterior) if valor_anterior is not None else None,
          str(valor_novo) if valor_novo is not None else None))

    conn.commit()
    conn.close()


def registrar_alteracoes_colaborador(colaborador_id: int, dados_novos: dict, dados_antigos: dict):
    """Compara dados novos e antigos e registra todas as alterações."""
    conn = get_connection()
    cursor = conn.cursor()

    for campo, valor_novo in dados_novos.items():
        if campo in ['id', 'created_at', 'updated_at']:
            continue

        valor_anterior = dados_antigos.get(campo)

        # Converter para string para comparação
        str_anterior = str(valor_anterior) if valor_anterior is not None else ''
        str_novo = str(valor_novo) if valor_novo is not None else ''

        # Só registra se houver mudança real
        if str_anterior != str_novo:
            cursor.execute('''
                INSERT INTO historico_alteracoes (colaborador_id, campo, valor_anterior, valor_novo)
                VALUES (?, ?, ?, ?)
            ''', (colaborador_id, campo, str_anterior if str_anterior else None, str_novo if str_novo else None))

    conn.commit()
    conn.close()


def listar_historico_colaborador(colaborador_id: int) -> List[Dict]:
    """Lista todo o histórico de alterações de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM historico_alteracoes
        WHERE colaborador_id = ?
        ORDER BY data_alteracao DESC
    ''', (colaborador_id,))

    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historico


def obter_nome_campo_legivel(campo: str) -> str:
    """Retorna o nome legível de um campo."""
    return CAMPOS_LEGIVEIS.get(campo, campo.replace('_', ' ').title())


def normalizar_cpf(cpf: str) -> str:
    """
    Normaliza um CPF para ter exatamente 11 dígitos.
    - Se tiver menos de 11 dígitos, adiciona zeros à esquerda.
    - Se tiver mais de 11 dígitos, corta para os primeiros 11.
    - Retorna apenas números.
    """
    if not cpf:
        return None

    # Remove caracteres não numéricos
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))

    if not cpf_limpo:
        return None

    # Normalizar para 11 dígitos
    if len(cpf_limpo) < 11:
        # Adiciona zeros à esquerda
        cpf_limpo = cpf_limpo.zfill(11)
    elif len(cpf_limpo) > 11:
        # Corta para os primeiros 11 dígitos
        cpf_limpo = cpf_limpo[:11]

    return cpf_limpo


def migrar_cpfs_para_11_digitos():
    """
    Migra todos os CPFs existentes no banco para ter exatamente 11 dígitos.
    Aplica a normalização em:
    - colaboradores.cpf
    - colaboradores.cpf_mae
    - colaboradores.cpf_pai
    - blocklist.cpf
    - dependentes.cpf
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Migrar CPFs da tabela colaboradores
    cursor.execute('SELECT id, cpf, cpf_mae, cpf_pai FROM colaboradores WHERE cpf IS NOT NULL OR cpf_mae IS NOT NULL OR cpf_pai IS NOT NULL')
    colaboradores = cursor.fetchall()

    for colab in colaboradores:
        updates = {}

        # CPF principal
        if colab['cpf']:
            cpf_normalizado = normalizar_cpf(colab['cpf'])
            if cpf_normalizado and cpf_normalizado != colab['cpf']:
                updates['cpf'] = cpf_normalizado

        # CPF da mãe
        if colab['cpf_mae']:
            cpf_mae_normalizado = normalizar_cpf(colab['cpf_mae'])
            if cpf_mae_normalizado and cpf_mae_normalizado != colab['cpf_mae']:
                updates['cpf_mae'] = cpf_mae_normalizado

        # CPF do pai
        if colab['cpf_pai']:
            cpf_pai_normalizado = normalizar_cpf(colab['cpf_pai'])
            if cpf_pai_normalizado and cpf_pai_normalizado != colab['cpf_pai']:
                updates['cpf_pai'] = cpf_pai_normalizado

        # Aplicar updates se houver mudanças
        if updates:
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [colab['id']]
            cursor.execute(f'UPDATE colaboradores SET {set_clause} WHERE id = ?', values)

    # Migrar CPFs da tabela blocklist
    cursor.execute('SELECT id, cpf FROM blocklist WHERE cpf IS NOT NULL')
    blocklist_registros = cursor.fetchall()

    for registro in blocklist_registros:
        if registro['cpf']:
            cpf_normalizado = normalizar_cpf(registro['cpf'])
            if cpf_normalizado and cpf_normalizado != registro['cpf']:
                cursor.execute('UPDATE blocklist SET cpf = ? WHERE id = ?', (cpf_normalizado, registro['id']))

    # Migrar CPFs da tabela dependentes
    cursor.execute('SELECT id, cpf FROM dependentes WHERE cpf IS NOT NULL')
    dependentes = cursor.fetchall()

    for dep in dependentes:
        if dep['cpf']:
            cpf_normalizado = normalizar_cpf(dep['cpf'])
            if cpf_normalizado and cpf_normalizado != dep['cpf']:
                cursor.execute('UPDATE dependentes SET cpf = ? WHERE id = ?', (cpf_normalizado, dep['id']))

    conn.commit()
    conn.close()


def finalizar_contrato_experiencia(colaborador_id: int):
    """Finaliza o contrato de experiência de um colaborador (usado quando muda para CLT)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE contratos_experiencia
        SET status = 'FINALIZADO', updated_at = CURRENT_TIMESTAMP
        WHERE colaborador_id = ? AND status = 'VIGENTE'
    ''', (colaborador_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# =============================================================================
# CRUD Documentos do Colaborador
# =============================================================================

# Lista de documentos obrigatórios para todos os colaboradores
DOCUMENTOS_OBRIGATORIOS = [
    "COMPROVANTE DE VACINAÇÃO",
    "ATESTADO DE SAÚDE OCUPACIONAL (ASO)",
    "COMPROVANTE DE RESIDÊNCIA",
    "CÓPIA DO RG",
    "CÓPIA DO CPF",
    "CÓPIA DA CTPS",
    "CÓPIA DO TÍTULO DE ELEITOR",
    "CÓPIA DO COMPROVANTE DE ESCOLARIDADE",
    "CERTIDÃO DE NASCIMENTO/CASAMENTO",
    "CERTIFICADO DE RESERVISTA",
    "CÓPIA DO PIS/PASEP",
    "COMPROVANTE DE CONTA BANCÁRIA",
    "CÓPIA DA CNH",
]

# Diretório base para documentos
DOCUMENTOS_DIR = "documentos_colaborador"


def obter_diretorio_documentos():
    """Retorna o diretório base para documentos, criando se não existir."""
    if not os.path.exists(DOCUMENTOS_DIR):
        os.makedirs(DOCUMENTOS_DIR)
    return DOCUMENTOS_DIR


def listar_tipos_documentos() -> List[str]:
    """Retorna a lista de tipos de documentos (obrigatórios + personalizados do banco)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar tipos personalizados que não estão na lista obrigatória
    cursor.execute('''
        SELECT DISTINCT tipo_documento FROM documentos_colaborador
        WHERE tipo_documento NOT IN ({})
    '''.format(','.join(['?' for _ in DOCUMENTOS_OBRIGATORIOS])), DOCUMENTOS_OBRIGATORIOS)

    tipos_personalizados = [row['tipo_documento'] for row in cursor.fetchall()]
    conn.close()

    # Combinar obrigatórios + personalizados
    return DOCUMENTOS_OBRIGATORIOS + sorted(tipos_personalizados)


def listar_documentos_colaborador(colaborador_id: int) -> List[Dict]:
    """Lista todos os documentos de um colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM documentos_colaborador
        WHERE colaborador_id = ?
        ORDER BY tipo_documento
    ''', (colaborador_id,))

    documentos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documentos


def obter_documento(colaborador_id: int, tipo_documento: str) -> Optional[Dict]:
    """Obtém um documento específico de um colaborador pelo tipo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM documentos_colaborador
        WHERE colaborador_id = ? AND tipo_documento = ?
    ''', (colaborador_id, tipo_documento))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def salvar_documento(colaborador_id: int, tipo_documento: str, caminho_origem: str, cpf: str) -> str:
    """
    Salva um documento para um colaborador.
    - Cria pasta com nome do tipo de documento
    - Copia o arquivo renomeando para o CPF do colaborador
    - Registra no banco de dados

    Retorna o caminho do arquivo salvo.
    """
    # Obter extensão do arquivo original
    _, extensao = os.path.splitext(caminho_origem)

    # Limpar CPF
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    if len(cpf_limpo) < 11:
        cpf_limpo = cpf_limpo.zfill(11)

    # Criar diretório do tipo de documento
    diretorio_tipo = os.path.join(obter_diretorio_documentos(), tipo_documento)
    if not os.path.exists(diretorio_tipo):
        os.makedirs(diretorio_tipo)

    # Nome do arquivo destino: CPF + extensão original
    nome_arquivo_destino = f"{cpf_limpo}{extensao}"
    caminho_destino = os.path.join(diretorio_tipo, nome_arquivo_destino)

    # Copiar arquivo
    shutil.copy2(caminho_origem, caminho_destino)

    # Obter nome original do arquivo
    nome_original = os.path.basename(caminho_origem)

    # Verificar se já existe registro no banco
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM documentos_colaborador
        WHERE colaborador_id = ? AND tipo_documento = ?
    ''', (colaborador_id, tipo_documento))

    registro_existente = cursor.fetchone()

    obrigatorio = 1 if tipo_documento in DOCUMENTOS_OBRIGATORIOS else 0

    if registro_existente:
        # Atualizar registro existente
        cursor.execute('''
            UPDATE documentos_colaborador
            SET nome_arquivo_original = ?, caminho_arquivo = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (nome_original, caminho_destino, registro_existente['id']))
    else:
        # Inserir novo registro
        cursor.execute('''
            INSERT INTO documentos_colaborador
            (colaborador_id, tipo_documento, nome_arquivo_original, caminho_arquivo, obrigatorio)
            VALUES (?, ?, ?, ?, ?)
        ''', (colaborador_id, tipo_documento, nome_original, caminho_destino, obrigatorio))

    conn.commit()
    conn.close()

    # Obter nome do colaborador para log
    colaborador = obter_colaborador(colaborador_id)
    nome_colaborador = colaborador.get('nome_completo', 'Colaborador') if colaborador else 'Colaborador'

    # Registrar log
    registrar_log(
        tipo_acao='ANEXAR',
        categoria='DOCUMENTO',
        descricao=f'Documento "{tipo_documento}" anexado',
        entidade_tipo='colaborador',
        entidade_id=colaborador_id,
        entidade_nome=nome_colaborador,
        valor_novo=nome_original
    )

    return caminho_destino


def excluir_documento(documento_id: int) -> bool:
    """Exclui um documento do colaborador (banco e arquivo físico)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Obter dados do documento antes de excluir
    cursor.execute('''
        SELECT dc.*, c.nome_completo
        FROM documentos_colaborador dc
        LEFT JOIN colaboradores c ON dc.colaborador_id = c.id
        WHERE dc.id = ?
    ''', (documento_id,))
    doc = cursor.fetchone()

    if doc and doc['caminho_arquivo'] and os.path.exists(doc['caminho_arquivo']):
        try:
            os.remove(doc['caminho_arquivo'])
        except Exception:
            pass  # Se não conseguir excluir o arquivo, continua com a exclusão do registro

    cursor.execute('DELETE FROM documentos_colaborador WHERE id = ?', (documento_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    # Registrar log
    if affected > 0 and doc:
        registrar_log(
            tipo_acao='EXCLUIR',
            categoria='DOCUMENTO',
            descricao=f'Documento "{doc["tipo_documento"]}" excluído',
            entidade_tipo='colaborador',
            entidade_id=doc['colaborador_id'],
            entidade_nome=doc['nome_completo'] or 'Colaborador'
        )

    return affected > 0


def marcar_documento_nao_necessario(colaborador_id: int, tipo_documento: str) -> bool:
    """
    Marca um documento obrigatório como 'Não Necessário' para um colaborador.
    Cria um registro sem arquivo, apenas marcando como não necessário.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se já existe registro
    cursor.execute('''
        SELECT id FROM documentos_colaborador
        WHERE colaborador_id = ? AND tipo_documento = ?
    ''', (colaborador_id, tipo_documento))

    registro_existente = cursor.fetchone()

    if registro_existente:
        # Atualizar registro existente
        cursor.execute('''
            UPDATE documentos_colaborador
            SET nao_necessario = 1, caminho_arquivo = 'NAO_NECESSARIO', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (registro_existente['id'],))
    else:
        # Inserir novo registro marcado como não necessário
        obrigatorio = 1 if tipo_documento in DOCUMENTOS_OBRIGATORIOS else 0
        cursor.execute('''
            INSERT INTO documentos_colaborador
            (colaborador_id, tipo_documento, nome_arquivo_original, caminho_arquivo, obrigatorio, nao_necessario)
            VALUES (?, ?, 'Não Necessário', 'NAO_NECESSARIO', ?, 1)
        ''', (colaborador_id, tipo_documento, obrigatorio))

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def desmarcar_documento_nao_necessario(colaborador_id: int, tipo_documento: str) -> bool:
    """
    Remove a marcação de 'Não Necessário' de um documento, excluindo o registro.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM documentos_colaborador
        WHERE colaborador_id = ? AND tipo_documento = ? AND nao_necessario = 1
    ''', (colaborador_id, tipo_documento))

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def obter_documentos_obrigatorios_dependentes(colaborador_id: int) -> List[str]:
    """
    Retorna a lista de documentos obrigatórios relacionados aos dependentes do colaborador.
    - Para TODOS os dependentes: CPF do dependente
    - Para dependentes FILHOS: Certidão de nascimento, Cartão de vacina, Declaração escolar
    """
    dependentes = listar_dependentes(colaborador_id)
    documentos_dependentes = []

    # Parentescos considerados como "filho"
    parentescos_filho = ['filho', 'filha', 'filho(a)', 'enteado', 'enteada', 'menor sob guarda']

    for dep in dependentes:
        nome_dep = dep.get('nome', 'Dependente')
        parentesco = (dep.get('parentesco') or '').lower().strip()

        # CPF é obrigatório para TODOS os dependentes
        documentos_dependentes.append(f"CPF - {nome_dep}")

        # Documentos específicos para filhos
        if any(p in parentesco for p in parentescos_filho):
            documentos_dependentes.append(f"CERTIDÃO DE NASCIMENTO - {nome_dep}")
            documentos_dependentes.append(f"CARTÃO DE VACINA - {nome_dep}")
            documentos_dependentes.append(f"DECLARAÇÃO DE FREQUÊNCIA ESCOLAR - {nome_dep}")

    return documentos_dependentes


def obter_todos_documentos_obrigatorios(colaborador_id: int) -> List[str]:
    """
    Retorna a lista completa de documentos obrigatórios para um colaborador,
    incluindo os documentos base e os documentos de dependentes.
    """
    # Documentos base obrigatórios
    todos = list(DOCUMENTOS_OBRIGATORIOS)

    # Adicionar documentos de dependentes
    docs_dependentes = obter_documentos_obrigatorios_dependentes(colaborador_id)
    todos.extend(docs_dependentes)

    return todos


def obter_status_documentos_colaborador(colaborador_id: int) -> Dict:
    """
    Retorna o status dos documentos de um colaborador.
    Verifica quais documentos obrigatórios estão presentes e quais faltam.
    Inclui documentos de dependentes.
    """
    documentos_existentes = listar_documentos_colaborador(colaborador_id)
    tipos_existentes = {doc['tipo_documento'] for doc in documentos_existentes}

    # Obter lista completa de obrigatórios (base + dependentes)
    todos_obrigatorios = obter_todos_documentos_obrigatorios(colaborador_id)

    obrigatorios_completos = []
    obrigatorios_faltando = []

    for tipo in todos_obrigatorios:
        if tipo in tipos_existentes:
            obrigatorios_completos.append(tipo)
        else:
            obrigatorios_faltando.append(tipo)

    # Documentos extras (não obrigatórios)
    extras = [doc for doc in documentos_existentes if doc['tipo_documento'] not in todos_obrigatorios]

    return {
        'total_obrigatorios': len(todos_obrigatorios),
        'completos': len(obrigatorios_completos),
        'faltando': len(obrigatorios_faltando),
        'lista_completos': obrigatorios_completos,
        'lista_faltando': obrigatorios_faltando,
        'extras': extras,
        'percentual': round((len(obrigatorios_completos) / len(todos_obrigatorios)) * 100, 1) if todos_obrigatorios else 100,
        'documentos_obrigatorios': todos_obrigatorios  # Nova chave com lista completa
    }


# =============================================================================
# Funções para Exportação Excel
# =============================================================================

def listar_todos_dependentes_com_colaborador(empresa_id: int = None) -> List[Dict]:
    """Lista todos os dependentes com informações do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT d.*, c.nome_completo as colaborador_nome, c.cpf as colaborador_cpf
        FROM dependentes d
        JOIN colaboradores c ON d.colaborador_id = c.id
        WHERE c.status = 'ATIVO'
    '''
    params = []

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    query += ' ORDER BY c.nome_completo, d.nome'

    cursor.execute(query, params)
    dependentes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dependentes


def listar_todos_contratos_com_colaborador(empresa_id: int = None) -> List[Dict]:
    """Lista todos os contratos de experiência com informações do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT ce.*, c.nome_completo, c.cpf, c.funcao, e.razao_social as empresa_nome
        FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO'
    '''
    params = []

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    query += ' ORDER BY ce.data_fim_prorrogacao DESC, ce.data_fim_inicial DESC'

    cursor.execute(query, params)
    contratos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return contratos


def listar_todas_ferias_com_colaborador(empresa_id: int = None) -> List[Dict]:
    """Lista todos os períodos de férias com informações do colaborador."""
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT f.*, c.nome_completo, c.cpf, e.razao_social as empresa_nome
        FROM ferias f
        JOIN colaboradores c ON f.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO'
    '''
    params = []

    if empresa_id:
        query += ' AND c.empresa_id = ?'
        params.append(empresa_id)

    query += ' ORDER BY f.periodo_concessivo_limite'

    cursor.execute(query, params)
    ferias = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ferias


def listar_blocklist_completa() -> List[Dict]:
    """Lista toda a blocklist com nome da empresa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.*, e.razao_social as empresa_nome
        FROM blocklist b
        LEFT JOIN empresas e ON b.empresa_id = e.id
        ORDER BY b.data_desligamento DESC
    ''')

    blocklist = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return blocklist


def listar_documentos_pendentes_todos(empresa_id: int = None) -> List[Dict]:
    """Lista todos os documentos pendentes de todos os colaboradores ativos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar colaboradores ativos
    query = 'SELECT id, nome_completo, cpf FROM colaboradores WHERE status = ?'
    params = ['ATIVO']

    if empresa_id:
        query += ' AND empresa_id = ?'
        params.append(empresa_id)

    cursor.execute(query, params)
    colaboradores = [dict(row) for row in cursor.fetchall()]
    conn.close()

    documentos_pendentes = []

    for colab in colaboradores:
        status = obter_status_documentos_colaborador(colab['id'])
        for doc in status.get('lista_faltando', []):
            documentos_pendentes.append({
                'colaborador_nome': colab['nome_completo'],
                'colaborador_cpf': colab['cpf'],
                'documento': doc,
                'obrigatorio': True
            })

    return documentos_pendentes


def sincronizar_fotos_colaboradores():
    """
    Sincroniza as fotos dos colaboradores baseado nos arquivos da pasta fotos_colaboradores.
    Verifica se existe um arquivo com o CPF do colaborador e atualiza o foto_path no banco.
    Usa caminhos RELATIVOS para funcionar em qualquer computador.
    """
    # Usar caminho relativo - pasta fotos_colaboradores na raiz do programa
    fotos_dir = "fotos_colaboradores"

    # Se a pasta não existe, criar ela
    if not os.path.exists(fotos_dir):
        os.makedirs(fotos_dir)
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    # Buscar todos os colaboradores com CPF
    cursor.execute('SELECT id, cpf, foto_path FROM colaboradores WHERE cpf IS NOT NULL')
    colaboradores = cursor.fetchall()

    extensoes = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    atualizados = 0

    for colab in colaboradores:
        colab_id = colab['id']
        cpf = colab['cpf']
        foto_path_atual = colab['foto_path']

        if not cpf:
            continue

        # Normalizar CPF
        cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
        if len(cpf_limpo) < 11:
            cpf_limpo = cpf_limpo.zfill(11)

        # Procurar arquivo de foto com qualquer extensão (caminho relativo)
        foto_encontrada = None
        for ext in extensoes:
            # Caminho relativo: fotos_colaboradores/CPF.ext
            caminho_relativo = f"{fotos_dir}/{cpf_limpo}{ext}"
            if os.path.exists(caminho_relativo):
                foto_encontrada = caminho_relativo
                break

        # Se encontrou foto
        if foto_encontrada:
            # Verificar se o path atual é diferente (ou é um path absoluto antigo)
            # Converter para comparar corretamente
            path_esperado = foto_encontrada.replace("\\", "/")
            path_atual = (foto_path_atual or "").replace("\\", "/")

            # Se o path atual contém caminho absoluto ou é diferente, atualizar
            if path_atual != path_esperado:
                cursor.execute('UPDATE colaboradores SET foto_path = ? WHERE id = ?',
                             (foto_encontrada, colab_id))
                atualizados += 1
        else:
            # Se não encontrou foto, limpar o foto_path
            if foto_path_atual:
                cursor.execute('UPDATE colaboradores SET foto_path = NULL WHERE id = ?',
                             (colab_id,))
                atualizados += 1

    if atualizados > 0:
        conn.commit()

    conn.close()
    return atualizados


# =============================================================================
# Sistema de Logs
# =============================================================================

def registrar_log(
    tipo_acao: str,
    categoria: str,
    descricao: str,
    entidade_tipo: str = None,
    entidade_id: int = None,
    entidade_nome: str = None,
    valor_anterior: str = None,
    valor_novo: str = None,
    usuario: str = None
) -> int:
    """
    Registra uma ação no log do sistema.

    Parâmetros:
    - tipo_acao: CRIAR, EDITAR, EXCLUIR, ANEXAR, DESATIVAR, REATIVAR, etc.
    - categoria: COLABORADOR, EMPRESA, DOCUMENTO, FERIAS, CONTRATO, BLOCKLIST, BACKUP, etc.
    - descricao: Descrição legível da ação
    - entidade_tipo: Tipo da entidade afetada (colaborador, empresa, documento, etc.)
    - entidade_id: ID da entidade afetada
    - entidade_nome: Nome/identificação da entidade
    - valor_anterior: Valor antes da alteração (para edições)
    - valor_novo: Valor após a alteração (para edições)
    - usuario: Nome do usuário que realizou a ação (se None, usa o usuário logado)

    Retorna o ID do log criado.
    """
    # Se não foi especificado usuário, usa o usuário logado
    if usuario is None:
        usuario = get_nome_usuario_logado()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO logs_sistema
        (tipo_acao, categoria, descricao, entidade_tipo, entidade_id, entidade_nome,
         valor_anterior, valor_novo, usuario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tipo_acao, categoria, descricao, entidade_tipo, entidade_id, entidade_nome,
          valor_anterior, valor_novo, usuario))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def listar_logs(
    limite: int = 100,
    offset: int = 0,
    categoria: str = None,
    tipo_acao: str = None,
    entidade_tipo: str = None,
    entidade_id: int = None,
    data_inicio: str = None,
    data_fim: str = None,
    pesquisa: str = None
) -> List[Dict]:
    """
    Lista os logs do sistema com filtros opcionais.

    Parâmetros:
    - limite: Quantidade máxima de registros
    - offset: Offset para paginação
    - categoria: Filtrar por categoria
    - tipo_acao: Filtrar por tipo de ação
    - entidade_tipo: Filtrar por tipo de entidade
    - entidade_id: Filtrar por ID de entidade específica
    - data_inicio: Data inicial (formato YYYY-MM-DD)
    - data_fim: Data final (formato YYYY-MM-DD)
    - pesquisa: Texto para buscar na descrição ou nome da entidade

    Retorna lista de logs ordenados do mais recente para o mais antigo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM logs_sistema WHERE 1=1'
    params = []

    if categoria:
        query += ' AND categoria = ?'
        params.append(categoria)

    if tipo_acao:
        query += ' AND tipo_acao = ?'
        params.append(tipo_acao)

    if entidade_tipo:
        query += ' AND entidade_tipo = ?'
        params.append(entidade_tipo)

    if entidade_id:
        query += ' AND entidade_id = ?'
        params.append(entidade_id)

    if data_inicio:
        query += ' AND DATE(data_hora) >= ?'
        params.append(data_inicio)

    if data_fim:
        query += ' AND DATE(data_hora) <= ?'
        params.append(data_fim)

    if pesquisa:
        query += ' AND (descricao LIKE ? OR entidade_nome LIKE ?)'
        params.append(f'%{pesquisa}%')
        params.append(f'%{pesquisa}%')

    query += ' ORDER BY data_hora DESC LIMIT ? OFFSET ?'
    params.extend([limite, offset])

    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return logs


def contar_logs(
    categoria: str = None,
    tipo_acao: str = None,
    entidade_tipo: str = None,
    entidade_id: int = None,
    data_inicio: str = None,
    data_fim: str = None,
    pesquisa: str = None
) -> int:
    """Conta o total de logs com os filtros aplicados."""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT COUNT(*) FROM logs_sistema WHERE 1=1'
    params = []

    if categoria:
        query += ' AND categoria = ?'
        params.append(categoria)

    if tipo_acao:
        query += ' AND tipo_acao = ?'
        params.append(tipo_acao)

    if entidade_tipo:
        query += ' AND entidade_tipo = ?'
        params.append(entidade_tipo)

    if entidade_id:
        query += ' AND entidade_id = ?'
        params.append(entidade_id)

    if data_inicio:
        query += ' AND DATE(data_hora) >= ?'
        params.append(data_inicio)

    if data_fim:
        query += ' AND DATE(data_hora) <= ?'
        params.append(data_fim)

    if pesquisa:
        query += ' AND (descricao LIKE ? OR entidade_nome LIKE ?)'
        params.append(f'%{pesquisa}%')
        params.append(f'%{pesquisa}%')

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()

    return total


def obter_categorias_log() -> List[str]:
    """Retorna lista de categorias únicas registradas nos logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT categoria FROM logs_sistema ORDER BY categoria')
    categorias = [row['categoria'] for row in cursor.fetchall()]
    conn.close()

    return categorias


def obter_tipos_acao_log() -> List[str]:
    """Retorna lista de tipos de ação únicos registrados nos logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT tipo_acao FROM logs_sistema ORDER BY tipo_acao')
    tipos = [row['tipo_acao'] for row in cursor.fetchall()]
    conn.close()

    return tipos


def obter_estatisticas_log() -> Dict:
    """Retorna estatísticas gerais dos logs."""
    conn = get_connection()
    cursor = conn.cursor()

    # Total de logs
    cursor.execute('SELECT COUNT(*) FROM logs_sistema')
    total = cursor.fetchone()[0]

    # Logs de hoje
    cursor.execute("SELECT COUNT(*) FROM logs_sistema WHERE DATE(data_hora) = DATE('now', 'localtime')")
    hoje = cursor.fetchone()[0]

    # Logs desta semana
    cursor.execute("SELECT COUNT(*) FROM logs_sistema WHERE DATE(data_hora) >= DATE('now', 'localtime', '-7 days')")
    semana = cursor.fetchone()[0]

    # Logs deste mês
    cursor.execute("SELECT COUNT(*) FROM logs_sistema WHERE strftime('%Y-%m', data_hora) = strftime('%Y-%m', 'now', 'localtime')")
    mes = cursor.fetchone()[0]

    # Por categoria
    cursor.execute('''
        SELECT categoria, COUNT(*) as total
        FROM logs_sistema
        GROUP BY categoria
        ORDER BY total DESC
    ''')
    por_categoria = {row['categoria']: row['total'] for row in cursor.fetchall()}

    # Por tipo de ação
    cursor.execute('''
        SELECT tipo_acao, COUNT(*) as total
        FROM logs_sistema
        GROUP BY tipo_acao
        ORDER BY total DESC
    ''')
    por_tipo_acao = {row['tipo_acao']: row['total'] for row in cursor.fetchall()}

    conn.close()

    return {
        'total': total,
        'hoje': hoje,
        'semana': semana,
        'mes': mes,
        'por_categoria': por_categoria,
        'por_tipo_acao': por_tipo_acao
    }


def limpar_logs_antigos(dias: int = 365) -> int:
    """
    Remove logs mais antigos que o número de dias especificado.
    Por padrão, mantém logs do último ano.

    Retorna a quantidade de logs removidos.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM logs_sistema
        WHERE DATE(data_hora) < DATE('now', 'localtime', ?)
    ''', (f'-{dias} days',))

    removidos = cursor.rowcount
    conn.commit()
    conn.close()

    return removidos


# =============================================================================
# CRUD Usuários do Sistema
# =============================================================================

def hash_senha(senha: str) -> str:
    """Gera hash da senha usando SHA256."""
    import hashlib
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_usuario_admin_padrao():
    """Cria o usuário admin padrão se não existir."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se já existe algum usuário admin
    cursor.execute("SELECT id FROM usuarios WHERE login = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO usuarios (nome_completo, login, senha, nivel_acesso, ativo)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Administrador', 'admin', hash_senha('admin'), 'administrador', 1))
        conn.commit()

    conn.close()


def criar_usuario(dados: dict, usuario_logado: str = 'Sistema') -> int:
    """Cria um novo usuário no sistema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Hash da senha
    senha_hash = hash_senha(dados.get('senha', ''))

    # Hash da resposta de segurança (se fornecida)
    resposta_hash = None
    if dados.get('resposta_seguranca'):
        resposta_hash = hash_senha(dados.get('resposta_seguranca').lower().strip())

    cursor.execute('''
        INSERT INTO usuarios (nome_completo, login, senha, email, cargo, nivel_acesso,
                             pergunta_seguranca, resposta_seguranca, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados.get('nome_completo'),
        dados.get('login'),
        senha_hash,
        dados.get('email'),
        dados.get('cargo'),
        dados.get('nivel_acesso', 'operador'),
        dados.get('pergunta_seguranca'),
        resposta_hash,
        1
    ))

    usuario_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Registrar log
    registrar_log(
        tipo_acao='CRIAR',
        categoria='USUARIO',
        descricao=f'Novo usuário criado: {dados.get("login")}',
        entidade_tipo='usuario',
        entidade_id=usuario_id,
        entidade_nome=dados.get('nome_completo'),
        usuario=usuario_logado
    )

    return usuario_id


def listar_usuarios() -> List[Dict]:
    """Lista todos os usuários do sistema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, nome_completo, login, email, cargo, nivel_acesso, ativo,
               ultimo_login, created_at
        FROM usuarios
        ORDER BY nome_completo
    ''')

    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usuarios


def obter_usuario(usuario_id: int) -> Optional[Dict]:
    """Obtém um usuário pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, nome_completo, login, email, cargo, nivel_acesso, ativo,
               pergunta_seguranca, ultimo_login, created_at
        FROM usuarios WHERE id = ?
    ''', (usuario_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def obter_usuario_por_login(login: str) -> Optional[Dict]:
    """Obtém um usuário pelo login."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, nome_completo, login, senha, email, cargo, nivel_acesso, ativo,
               pergunta_seguranca, resposta_seguranca, ultimo_login
        FROM usuarios WHERE login = ?
    ''', (login,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def atualizar_usuario(usuario_id: int, dados: dict, usuario_logado: str = 'Sistema') -> bool:
    """Atualiza os dados de um usuário."""
    conn = get_connection()
    cursor = conn.cursor()

    campos = []
    valores = []

    for key, value in dados.items():
        if key not in ['id', 'senha', 'resposta_seguranca']:
            campos.append(f"{key} = ?")
            valores.append(value)

    # Se houver nova senha, fazer hash
    if 'senha' in dados and dados['senha']:
        campos.append("senha = ?")
        valores.append(hash_senha(dados['senha']))

    # Se houver nova resposta de segurança, fazer hash
    if 'resposta_seguranca' in dados and dados['resposta_seguranca']:
        campos.append("resposta_seguranca = ?")
        valores.append(hash_senha(dados['resposta_seguranca'].lower().strip()))

    valores.append(usuario_id)

    cursor.execute(f'''
        UPDATE usuarios SET {', '.join(campos)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', valores)

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected > 0:
        usuario = obter_usuario(usuario_id)
        registrar_log(
            tipo_acao='EDITAR',
            categoria='USUARIO',
            descricao=f'Usuário atualizado: {usuario.get("login") if usuario else ""}',
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            entidade_nome=usuario.get('nome_completo') if usuario else '',
            usuario=usuario_logado
        )

    return affected > 0


def desativar_usuario(usuario_id: int, usuario_logado: str = 'Sistema') -> bool:
    """Desativa um usuário (não exclui)."""
    usuario = obter_usuario(usuario_id)
    if not usuario:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE usuarios SET ativo = 0, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (usuario_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected > 0:
        registrar_log(
            tipo_acao='DESATIVAR',
            categoria='USUARIO',
            descricao=f'Usuário desativado: {usuario.get("login")}',
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            entidade_nome=usuario.get('nome_completo'),
            usuario=usuario_logado
        )

    return affected > 0


def reativar_usuario(usuario_id: int, usuario_logado: str = 'Sistema') -> bool:
    """Reativa um usuário desativado."""
    usuario = obter_usuario(usuario_id)
    if not usuario:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE usuarios SET ativo = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (usuario_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected > 0:
        registrar_log(
            tipo_acao='REATIVAR',
            categoria='USUARIO',
            descricao=f'Usuário reativado: {usuario.get("login")}',
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            entidade_nome=usuario.get('nome_completo'),
            usuario=usuario_logado
        )

    return affected > 0


def alterar_senha_usuario(usuario_id: int, nova_senha: str, usuario_logado: str = 'Sistema') -> bool:
    """Altera a senha de um usuário."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE usuarios SET senha = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (hash_senha(nova_senha), usuario_id))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected > 0:
        usuario = obter_usuario(usuario_id)
        registrar_log(
            tipo_acao='EDITAR',
            categoria='USUARIO',
            descricao=f'Senha alterada para o usuário: {usuario.get("login") if usuario else ""}',
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            entidade_nome=usuario.get('nome_completo') if usuario else '',
            usuario=usuario_logado
        )

    return affected > 0


def resetar_senha_admin(usuario_id: int, nova_senha: str, usuario_logado: str = 'Sistema') -> bool:
    """Admin reseta a senha de um usuário e marca como senha resetada."""
    resultado = alterar_senha_usuario(usuario_id, nova_senha, usuario_logado)

    if resultado:
        # Marcar que a senha foi resetada e precisa ser alterada
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE usuarios SET senha_resetada = 1 WHERE id = ?', (usuario_id,))
        conn.commit()
        conn.close()

    return resultado


def verificar_senha_resetada(usuario_id: int) -> bool:
    """Verifica se o usuário precisa alterar a senha (após reset)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT senha_resetada FROM usuarios WHERE id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado and resultado['senha_resetada'] == 1


def limpar_senha_resetada(usuario_id: int) -> bool:
    """Limpa o flag de senha resetada após o usuário alterar a senha."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET senha_resetada = 0 WHERE id = ?', (usuario_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# =============================================================================
# Sistema de Autenticação e Bloqueio
# =============================================================================

def verificar_login_bloqueado(login: str) -> Optional[datetime]:
    """
    Verifica se o login está bloqueado.
    Retorna a data/hora até quando está bloqueado, ou None se não estiver.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT bloqueado_ate FROM bloqueios_login
        WHERE login = ? AND bloqueado_ate > datetime('now', 'localtime')
    ''', (login,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return datetime.strptime(row['bloqueado_ate'], '%Y-%m-%d %H:%M:%S')
    return None


def registrar_tentativa_login(login: str, sucesso: bool) -> int:
    """
    Registra uma tentativa de login.
    Retorna o número de tentativas falhas recentes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Registrar tentativa
    cursor.execute('''
        INSERT INTO tentativas_login (login, sucesso)
        VALUES (?, ?)
    ''', (login, 1 if sucesso else 0))

    if sucesso:
        # Se login bem sucedido, limpar tentativas anteriores e bloqueios
        cursor.execute('DELETE FROM tentativas_login WHERE login = ? AND sucesso = 0', (login,))
        cursor.execute('DELETE FROM bloqueios_login WHERE login = ?', (login,))

        # Atualizar último login do usuário
        cursor.execute('''
            UPDATE usuarios SET ultimo_login = datetime('now', 'localtime')
            WHERE login = ?
        ''', (login,))

    conn.commit()

    # Contar tentativas falhas na última hora
    cursor.execute('''
        SELECT COUNT(*) FROM tentativas_login
        WHERE login = ? AND sucesso = 0
        AND data_hora > datetime('now', 'localtime', '-1 hour')
    ''', (login,))

    falhas = cursor.fetchone()[0]
    conn.close()

    return falhas


def bloquear_login(login: str, horas: int = 1) -> bool:
    """Bloqueia um login por determinado número de horas."""
    conn = get_connection()
    cursor = conn.cursor()

    bloqueado_ate = datetime.now() + timedelta(hours=horas)

    cursor.execute('''
        INSERT OR REPLACE INTO bloqueios_login (login, bloqueado_ate)
        VALUES (?, ?)
    ''', (login, bloqueado_ate.strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()

    registrar_log(
        tipo_acao='BLOQUEAR',
        categoria='USUARIO',
        descricao=f'Login bloqueado por {horas} hora(s): {login}',
        entidade_tipo='usuario',
        entidade_nome=login
    )

    return True


def autenticar_usuario(login: str, senha: str) -> Dict:
    """
    Autentica um usuário.
    Retorna um dicionário com:
    - sucesso: bool
    - usuario: dict ou None
    - mensagem: str
    - bloqueado_ate: datetime ou None
    """
    # Verificar se está bloqueado
    bloqueado_ate = verificar_login_bloqueado(login)
    if bloqueado_ate:
        return {
            'sucesso': False,
            'usuario': None,
            'mensagem': f'Login bloqueado até {bloqueado_ate.strftime("%H:%M")}',
            'bloqueado_ate': bloqueado_ate
        }

    # Buscar usuário
    usuario = obter_usuario_por_login(login)

    if not usuario:
        falhas = registrar_tentativa_login(login, False)
        if falhas >= 10:
            bloquear_login(login, 1)
            return {
                'sucesso': False,
                'usuario': None,
                'mensagem': 'Login bloqueado por 1 hora devido a múltiplas tentativas falhas',
                'bloqueado_ate': datetime.now() + timedelta(hours=1)
            }
        return {
            'sucesso': False,
            'usuario': None,
            'mensagem': f'Usuário ou senha inválidos ({10 - falhas} tentativas restantes)',
            'bloqueado_ate': None
        }

    # Verificar se está ativo
    if not usuario.get('ativo'):
        return {
            'sucesso': False,
            'usuario': None,
            'mensagem': 'Usuário desativado. Contate o administrador.',
            'bloqueado_ate': None
        }

    # Verificar senha
    if usuario.get('senha') != hash_senha(senha):
        falhas = registrar_tentativa_login(login, False)
        if falhas >= 10:
            bloquear_login(login, 1)
            return {
                'sucesso': False,
                'usuario': None,
                'mensagem': 'Login bloqueado por 1 hora devido a múltiplas tentativas falhas',
                'bloqueado_ate': datetime.now() + timedelta(hours=1)
            }
        return {
            'sucesso': False,
            'usuario': None,
            'mensagem': f'Usuário ou senha inválidos ({10 - falhas} tentativas restantes)',
            'bloqueado_ate': None
        }

    # Login bem sucedido
    registrar_tentativa_login(login, True)

    # Remover senha do retorno
    usuario_retorno = {k: v for k, v in usuario.items() if k not in ['senha', 'resposta_seguranca']}

    registrar_log(
        tipo_acao='LOGIN',
        categoria='USUARIO',
        descricao=f'Login realizado: {login}',
        entidade_tipo='usuario',
        entidade_id=usuario.get('id'),
        entidade_nome=usuario.get('nome_completo'),
        usuario=usuario.get('nome_completo')
    )

    return {
        'sucesso': True,
        'usuario': usuario_retorno,
        'mensagem': 'Login realizado com sucesso',
        'bloqueado_ate': None
    }


def verificar_resposta_seguranca(login: str, resposta: str) -> bool:
    """Verifica se a resposta de segurança está correta."""
    usuario = obter_usuario_por_login(login)
    if not usuario:
        return False

    resposta_hash = hash_senha(resposta.lower().strip())
    return usuario.get('resposta_seguranca') == resposta_hash


def obter_pergunta_seguranca(login: str) -> Optional[str]:
    """Obtém a pergunta de segurança de um usuário."""
    usuario = obter_usuario_por_login(login)
    if usuario:
        return usuario.get('pergunta_seguranca')
    return None


def recuperar_senha_com_pergunta(login: str, resposta: str, nova_senha: str) -> Dict:
    """
    Recupera a senha usando a pergunta de segurança.
    Retorna um dicionário com sucesso e mensagem.
    """
    usuario = obter_usuario_por_login(login)

    if not usuario:
        return {'sucesso': False, 'mensagem': 'Usuário não encontrado'}

    if not usuario.get('pergunta_seguranca') or not usuario.get('resposta_seguranca'):
        return {'sucesso': False, 'mensagem': 'Este usuário não possui pergunta de segurança configurada'}

    if not verificar_resposta_seguranca(login, resposta):
        return {'sucesso': False, 'mensagem': 'Resposta incorreta'}

    # Alterar senha
    if alterar_senha_usuario(usuario['id'], nova_senha, 'Sistema'):
        registrar_log(
            tipo_acao='RECUPERAR_SENHA',
            categoria='USUARIO',
            descricao=f'Senha recuperada via pergunta de segurança: {login}',
            entidade_tipo='usuario',
            entidade_id=usuario['id'],
            entidade_nome=usuario.get('nome_completo')
        )
        return {'sucesso': True, 'mensagem': 'Senha alterada com sucesso'}

    return {'sucesso': False, 'mensagem': 'Erro ao alterar senha'}


# =============================================================================
# Variável Global do Usuário Logado
# =============================================================================

_usuario_logado = None


def set_usuario_logado(usuario: Optional[Dict]):
    """Define o usuário logado globalmente."""
    global _usuario_logado
    _usuario_logado = usuario


def get_usuario_logado() -> Optional[Dict]:
    """Obtém o usuário logado."""
    global _usuario_logado
    return _usuario_logado


def get_nome_usuario_logado() -> str:
    """Obtém o nome do usuário logado ou 'Sistema'."""
    global _usuario_logado
    if _usuario_logado:
        return _usuario_logado.get('nome_completo', 'Sistema')
    return 'Sistema'


def usuario_pode_editar() -> bool:
    """Verifica se o usuário logado tem permissão para editar dados.
    Retorna False se for visualizador, True caso contrário."""
    global _usuario_logado
    if _usuario_logado:
        nivel = _usuario_logado.get('nivel_acesso', 'operador')
        return nivel != 'visualizador'
    return False


def get_nivel_acesso_usuario() -> str:
    """Obtém o nível de acesso do usuário logado."""
    global _usuario_logado
    if _usuario_logado:
        return _usuario_logado.get('nivel_acesso', 'operador')
    return 'operador'


def usuario_pode(permissao: str) -> bool:
    """
    Verifica se o usuário logado tem determinada permissão.
    Permissões:
    - adicionar_colaborador
    - editar_colaborador
    - excluir_colaborador
    - gerenciar_usuarios
    - fazer_backup
    - restaurar_backup
    """
    nivel = get_nivel_acesso_usuario()

    permissoes = {
        'administrador': [
            'adicionar_colaborador', 'editar_colaborador', 'excluir_colaborador',
            'gerenciar_usuarios', 'fazer_backup', 'restaurar_backup',
            'ver_colaboradores', 'ver_logs'
        ],
        'operador': [
            'adicionar_colaborador', 'editar_colaborador',
            'fazer_backup', 'ver_colaboradores', 'ver_logs'
        ],
        'visualizador': [
            'ver_colaboradores', 'ver_logs'
        ]
    }

    return permissao in permissoes.get(nivel, [])


# Inicializar banco de dados ao importar o módulo
if __name__ != "__main__":
    init_database()
    # Criar usuário admin padrão se não existir
    criar_usuario_admin_padrao()
    # Sincronizar fotos dos colaboradores ao iniciar
    sincronizar_fotos_colaboradores()
