"""
Sistema ERP Integrado - RENOVO Montagens Industriais
Gerenciador principal de módulos empresariais
Versão 1.0
"""

import flet as ft
import os
import sys
import subprocess
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime
import multiprocessing
import threading
import time
import argparse
from PIL import Image
import pystray

# Corrigir sys.stdin/stdout/stderr para PyInstaller --noconsole
if getattr(sys, 'frozen', False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    if sys.stdin is None:
        sys.stdin = open(os.devnull, 'r')

multiprocessing.freeze_support()

# Versão do sistema
VERSAO = "1.0"

# Paleta de cores (azul escuro, azul claro, verde, branco)
COR_AZUL_ESCURO = "#0D47A1"
COR_AZUL_MEDIO = "#1565C0"
COR_AZUL_CLARO = "#42A5F5"
COR_VERDE = "#2E7D32"
COR_VERDE_CLARO = "#4CAF50"
COR_BRANCO = "#FFFFFF"
COR_FUNDO = "#F5F7FA"
COR_TEXTO = "#263238"
COR_TEXTO_SECUNDARIO = "#546E7A"
COR_ERRO = "#C62828"
COR_ALERTA = "#F57C00"

# Cores para módulos - tons claros (fundo do header)
COR_MODULO_CRM = "#FFCC80"           # Laranja claro - CRM
COR_MODULO_COMPRAS = "#CE93D8"       # Roxo claro - Compras
COR_MODULO_RH = "#EF9A9A"            # Vermelho claro - RH
COR_MODULO_PATRIMONIO = "#90CAF9"    # Azul claro - Patrimônio
COR_MODULO_DOCUMENTOS = "#80CBC4"    # Teal claro - Documentos
COR_MODULO_SSMA = "#A5D6A7"          # Verde claro - SSMA

# Cores para módulos - tons escuros (ícones e botões)
COR_MODULO_CRM_ESCURO = "#E65100"           # Laranja escuro - CRM
COR_MODULO_COMPRAS_ESCURO = "#6A1B9A"       # Roxo escuro - Compras
COR_MODULO_RH_ESCURO = "#B71C1C"            # Vermelho escuro - RH
COR_MODULO_PATRIMONIO_ESCURO = "#0D47A1"    # Azul escuro - Patrimônio
COR_MODULO_DOCUMENTOS_ESCURO = "#004D40"    # Teal escuro - Documentos
COR_MODULO_SSMA_ESCURO = "#1B5E20"          # Verde escuro - SSMA


def get_base_path():
    """Retorna o caminho base do aplicativo"""
    return os.path.dirname(os.path.abspath(__file__))


def get_db_path():
    """Retorna o caminho do banco de dados"""
    db_dir = os.path.join(get_base_path(), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return os.path.join(db_dir, "erp_sistema.db")


def get_config_path():
    """Retorna o caminho do arquivo de configuração"""
    config_dir = os.path.join(get_base_path(), "config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return config_dir


def hash_senha(senha):
    """Gera hash SHA256 da senha"""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def gerar_codigo_recuperacao():
    """Gera código de recuperação aleatório"""
    chars = string.ascii_uppercase + string.digits
    codigo = ''.join(secrets.choice(chars) for _ in range(8))
    return f"REC-{codigo}"


def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Tabela de tipos de conta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_conta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            is_admin INTEGER DEFAULT 0,
            protegido INTEGER DEFAULT 0,
            data_criacao TEXT
        )
    ''')

    # Tabela de permissões por tipo de conta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_conta_id INTEGER,
            modulo TEXT NOT NULL,
            permitido INTEGER DEFAULT 1,
            FOREIGN KEY (tipo_conta_id) REFERENCES tipos_conta(id)
        )
    ''')

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT,
            email TEXT,
            tipo_conta_id INTEGER,
            codigo_recuperacao TEXT,
            ativo INTEGER DEFAULT 0,
            aprovado INTEGER DEFAULT 0,
            data_criacao TEXT,
            data_ultimo_acesso TEXT,
            FOREIGN KEY (tipo_conta_id) REFERENCES tipos_conta(id)
        )
    ''')

    # Tabela de logs de acesso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_acesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_login TEXT,
            acao TEXT,
            modulo TEXT,
            data TEXT,
            hora TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Tabela de favoritos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            modulo TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Tabela de configurações (para lembrar login)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_local (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE,
            valor TEXT
        )
    ''')

    # Criar tipo Administrador padrão se não existir
    cursor.execute("SELECT id FROM tipos_conta WHERE nome = 'Administrador'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO tipos_conta (nome, descricao, is_admin, protegido, data_criacao)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Administrador', 'Acesso total ao sistema', 1, 1, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        tipo_admin_id = cursor.lastrowid

        # Adicionar permissões para todos os módulos
        modulos = ['CRM - Gestão Comercial', 'Gestão de Compras', 'Recursos Humanos',
                   'Gestão Patrimonial', 'Gestão de Documentos', 'SMS - Segurança e Meio Ambiente']
        for modulo in modulos:
            cursor.execute('''
                INSERT INTO permissoes (tipo_conta_id, modulo, permitido)
                VALUES (?, ?, ?)
            ''', (tipo_admin_id, modulo, 1))

    # Criar usuário admin padrão se não existir
    cursor.execute("SELECT id FROM usuarios WHERE login = 'admin'")
    if not cursor.fetchone():
        cursor.execute("SELECT id FROM tipos_conta WHERE nome = 'Administrador'")
        tipo_admin = cursor.fetchone()
        if tipo_admin:
            codigo_rec = gerar_codigo_recuperacao()
            cursor.execute('''
                INSERT INTO usuarios (login, senha_hash, nome, cargo, email, tipo_conta_id,
                                     codigo_recuperacao, ativo, aprovado, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', hash_senha('admin'), 'Administrador', 'Administrador do Sistema',
                  'admin@renovo.com.br', tipo_admin[0], codigo_rec, 1, 1,
                  datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

    conn.commit()
    conn.close()


def get_connection():
    """Retorna uma conexão com o banco de dados"""
    return sqlite3.connect(get_db_path())


def registrar_log(usuario_id, usuario_login, acao, modulo="ERP"):
    """Registra um log de acesso"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs_acesso (usuario_id, usuario_login, acao, modulo, data, hora)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (usuario_id, usuario_login, acao, modulo,
          datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S")))
    conn.commit()
    conn.close()


def carregar_logs(limite=100, usuario_login=None):
    """Carrega os logs de acesso. Se usuario_login for informado, filtra apenas os logs desse usuário."""
    conn = get_connection()
    cursor = conn.cursor()
    if usuario_login:
        cursor.execute('''
            SELECT usuario_login, acao, modulo, data, hora
            FROM logs_acesso
            WHERE usuario_login = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (usuario_login, limite))
    else:
        cursor.execute('''
            SELECT usuario_login, acao, modulo, data, hora
            FROM logs_acesso
            ORDER BY id DESC
            LIMIT ?
        ''', (limite,))
    logs = cursor.fetchall()
    conn.close()
    return [{"usuario": l[0], "acao": l[1], "modulo": l[2], "data": l[3], "hora": l[4]} for l in logs]


def carregar_favoritos(usuario_id):
    """Carrega os favoritos do usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT modulo FROM favoritos WHERE usuario_id = ?', (usuario_id,))
    favoritos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return favoritos


def salvar_favorito(usuario_id, modulo, adicionar=True):
    """Adiciona ou remove favorito"""
    conn = get_connection()
    cursor = conn.cursor()
    if adicionar:
        cursor.execute('INSERT INTO favoritos (usuario_id, modulo) VALUES (?, ?)', (usuario_id, modulo))
    else:
        cursor.execute('DELETE FROM favoritos WHERE usuario_id = ? AND modulo = ?', (usuario_id, modulo))
    conn.commit()
    conn.close()


def salvar_config_local(chave, valor):
    """Salva configuração local"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO config_local (chave, valor) VALUES (?, ?)', (chave, valor))
    conn.commit()
    conn.close()


def carregar_config_local(chave):
    """Carrega configuração local"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT valor FROM config_local WHERE chave = ?', (chave,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def obter_permissoes_usuario(tipo_conta_id):
    """Obtém as permissões de um tipo de conta"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT modulo FROM permissoes
        WHERE tipo_conta_id = ? AND permitido = 1
    ''', (tipo_conta_id,))
    permissoes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return permissoes


def verificar_admin(tipo_conta_id):
    """Verifica se o tipo de conta é administrador"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM tipos_conta WHERE id = ?', (tipo_conta_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False


class ModuloInfo:
    """Classe para armazenar informações de cada módulo"""
    def __init__(self, nome, descricao, icone, pasta, arquivo_principal, cor="#1565C0", cor_escura="#0D47A1", ativo=True):
        self.nome = nome
        self.descricao = descricao
        self.icone = icone
        self.pasta = pasta
        self.arquivo_principal = arquivo_principal
        self.cor = cor  # Cor clara para fundo
        self.cor_escura = cor_escura  # Cor escura para ícones e botões
        self.ativo = ativo


class TelaLogin:
    """Tela de login do sistema"""
    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success
        self.build_ui()

    def build_ui(self):
        """Constrói a interface de login"""
        self.page.controls.clear()
        self.page.title = "Login - Sistema ERP Integrado"
        self.page.window.maximized = True
        self.page.bgcolor = COR_BRANCO  # Fundo branco para destacar a logomarca
        self.page.padding = 0

        base_path = get_base_path()
        logo_path = os.path.join(base_path, "imagens_principal", "Logomarca Renovo.png")

        # Criar elemento do logo
        if os.path.exists(logo_path):
            logo_element = ft.Image(
                src=logo_path,
                width=260,
                height=160,
                fit=ft.ImageFit.CONTAIN
            )
        else:
            logo_element = ft.Icon(
                ft.Icons.BUSINESS,
                size=80,
                color=COR_AZUL_ESCURO
            )

        # Carregar login lembrado
        login_lembrado = carregar_config_local("ultimo_login") or ""

        self.txt_usuario = ft.TextField(
            label="Usuário",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO,
            value=login_lembrado,
            on_submit=self.fazer_login
        )

        self.txt_senha = ft.TextField(
            label="Senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO,
            on_submit=self.fazer_login
        )

        self.chk_lembrar = ft.Checkbox(
            label="Lembrar meu login",
            value=bool(login_lembrado),
            active_color=COR_AZUL_ESCURO
        )

        self.lbl_erro = ft.Text(
            "",
            color=COR_ERRO,
            size=14,
            visible=False
        )

        login_card = ft.Container(
            content=ft.Column([
                # Logo com fundo destacado
                logo_element,
                ft.Text(
                    "Sistema ERP Integrado",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=COR_AZUL_ESCURO
                ),
                ft.Text(
                    "RENOVO Montagens Industriais",
                    size=16,
                    color=COR_TEXTO_SECUNDARIO
                ),
                ft.Container(height=30),
                self.txt_usuario,
                ft.Container(height=10),
                self.txt_senha,
                ft.Container(height=5),
                ft.Row([self.chk_lembrar], alignment=ft.MainAxisAlignment.CENTER),
                self.lbl_erro,
                ft.Container(height=15),
                ft.FilledButton(
                    "Entrar",
                    icon=ft.Icons.LOGIN,
                    width=300,
                    height=45,
                    bgcolor=COR_AZUL_ESCURO,
                    color=COR_BRANCO,
                    on_click=self.fazer_login
                ),
                ft.Container(height=15),
                ft.Row([
                    ft.TextButton(
                        "Esqueci minha senha",
                        on_click=self.abrir_esqueci_senha
                    ),
                    ft.Text("|", color=COR_TEXTO_SECUNDARIO),
                    ft.TextButton(
                        "Criar conta",
                        on_click=self.abrir_criar_conta
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.Text(
                    f"Versão {VERSAO}",
                    size=12,
                    color=COR_TEXTO_SECUNDARIO
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5),
            bgcolor=COR_BRANCO,
            padding=50,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 4)
            )
        )

        self.page.add(
            ft.Container(
                content=login_card,
                expand=True,
                alignment=ft.alignment.center,
                bgcolor=COR_BRANCO
            )
        )
        self.page.update()

        if login_lembrado:
            self.txt_senha.focus()
        else:
            self.txt_usuario.focus()

    def fazer_login(self, e):
        """Realiza o login"""
        usuario = self.txt_usuario.value.strip().lower()
        senha = self.txt_senha.value

        if not usuario or not senha:
            self.mostrar_erro("Preencha usuário e senha")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, login, senha_hash, nome, cargo, email, tipo_conta_id, ativo, aprovado
            FROM usuarios WHERE login = ?
        ''', (usuario,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, login, senha_hash, nome, cargo, email, tipo_conta_id, ativo, aprovado = user

            if senha_hash != hash_senha(senha):
                self.mostrar_erro("Senha incorreta")
                return

            if not aprovado:
                self.mostrar_erro("Conta aguardando aprovação do administrador")
                return

            if not ativo:
                self.mostrar_erro("Conta inativa. Contate o administrador.")
                return

            # Salvar ou limpar login lembrado
            if self.chk_lembrar.value:
                salvar_config_local("ultimo_login", login)
            else:
                salvar_config_local("ultimo_login", "")

            # Atualizar último acesso
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios SET data_ultimo_acesso = ? WHERE id = ?
            ''', (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_id))
            conn.commit()
            conn.close()

            # Registrar log
            registrar_log(user_id, login, "Login no sistema", "ERP")

            # Chamar callback de sucesso
            user_data = {
                "id": user_id,
                "login": login,
                "nome": nome,
                "cargo": cargo,
                "email": email,
                "tipo_conta_id": tipo_conta_id,
                "is_admin": verificar_admin(tipo_conta_id)
            }
            self.on_login_success(login, user_data)
        else:
            self.mostrar_erro("Usuário não encontrado")

    def mostrar_erro(self, mensagem):
        """Mostra mensagem de erro"""
        self.lbl_erro.value = mensagem
        self.lbl_erro.visible = True
        self.page.update()

    def abrir_esqueci_senha(self, e):
        """Abre a tela de recuperação de senha"""
        TelaEsqueciSenha(self.page, self.voltar_login)

    def abrir_criar_conta(self, e):
        """Abre a tela de criação de conta"""
        TelaCriarConta(self.page, self.voltar_login)

    def voltar_login(self):
        """Volta para a tela de login"""
        self.build_ui()


class TelaEsqueciSenha:
    """Tela de recuperação de senha"""
    def __init__(self, page: ft.Page, on_voltar):
        self.page = page
        self.on_voltar = on_voltar
        self.build_ui()

    def build_ui(self):
        """Constrói a interface"""
        self.page.controls.clear()

        self.txt_login = ft.TextField(
            label="Login",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.txt_codigo = ft.TextField(
            label="Código de Recuperação",
            prefix_icon=ft.Icons.KEY,
            width=300,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO,
            hint_text="Ex: REC-XXXXXXXX"
        )

        self.lbl_mensagem = ft.Text(
            "",
            size=14,
            visible=False
        )

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_RESET, size=60, color=COR_AZUL_ESCURO),
                ft.Text(
                    "Recuperar Senha",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=COR_AZUL_ESCURO
                ),
                ft.Text(
                    "Digite seu login e código de recuperação",
                    size=14,
                    color=COR_TEXTO_SECUNDARIO
                ),
                ft.Container(height=20),
                self.txt_login,
                ft.Container(height=10),
                self.txt_codigo,
                ft.Container(height=5),
                self.lbl_mensagem,
                ft.Container(height=20),
                ft.FilledButton(
                    "Recuperar Senha",
                    icon=ft.Icons.REFRESH,
                    width=300,
                    height=45,
                    bgcolor=COR_AZUL_ESCURO,
                    color=COR_BRANCO,
                    on_click=self.recuperar_senha
                ),
                ft.Container(height=10),
                ft.TextButton(
                    "Voltar ao login",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self.on_voltar()
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5),
            bgcolor=COR_BRANCO,
            padding=50,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 4)
            )
        )

        self.page.add(
            ft.Container(
                content=card,
                expand=True,
                alignment=ft.alignment.center,
                bgcolor=COR_FUNDO
            )
        )
        self.page.update()

    def recuperar_senha(self, e):
        """Processa a recuperação de senha"""
        login = self.txt_login.value.strip().lower()
        codigo = self.txt_codigo.value.strip().upper()

        if not login or not codigo:
            self.mostrar_mensagem("Preencha todos os campos", erro=True)
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, codigo_recuperacao FROM usuarios WHERE login = ?
        ''', (login,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            self.mostrar_mensagem("Usuário não encontrado", erro=True)
            return

        user_id, codigo_salvo = user

        if codigo != codigo_salvo:
            conn.close()
            self.mostrar_mensagem("Código de recuperação inválido", erro=True)
            return

        # Resetar senha para "renovo"
        nova_senha_hash = hash_senha("renovo")
        novo_codigo = gerar_codigo_recuperacao()

        cursor.execute('''
            UPDATE usuarios SET senha_hash = ?, codigo_recuperacao = ? WHERE id = ?
        ''', (nova_senha_hash, novo_codigo, user_id))
        conn.commit()
        conn.close()

        # Mostrar nova senha e código
        self.mostrar_dialogo_sucesso(novo_codigo)

    def mostrar_mensagem(self, mensagem, erro=False):
        """Mostra mensagem"""
        self.lbl_mensagem.value = mensagem
        self.lbl_mensagem.color = COR_ERRO if erro else COR_VERDE
        self.lbl_mensagem.visible = True
        self.page.update()

    def mostrar_dialogo_sucesso(self, novo_codigo):
        """Mostra diálogo de sucesso com novo código"""
        def fechar(e):
            dlg.open = False
            self.page.update()
            self.on_voltar()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=COR_VERDE),
                ft.Text("Senha Resetada!")
            ], spacing=10),
            content=ft.Column([
                ft.Text("Sua senha foi resetada com sucesso!"),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Nova senha:", weight=ft.FontWeight.BOLD),
                        ft.Text("renovo", size=20, color=COR_AZUL_ESCURO, selectable=True),
                    ]),
                    bgcolor=COR_FUNDO,
                    padding=15,
                    border_radius=8
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Novo código de recuperação:", weight=ft.FontWeight.BOLD),
                        ft.Text(novo_codigo, size=16, color=COR_AZUL_ESCURO, selectable=True),
                        ft.Text("(Anote este código em local seguro!)",
                               size=12, color=COR_ERRO, italic=True)
                    ]),
                    bgcolor=COR_FUNDO,
                    padding=15,
                    border_radius=8
                )
            ], tight=True),
            actions=[
                ft.FilledButton("OK, entendi", on_click=fechar)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


class TelaCriarConta:
    """Tela de criação de conta"""
    def __init__(self, page: ft.Page, on_voltar):
        self.page = page
        self.on_voltar = on_voltar
        self.build_ui()

    def build_ui(self):
        """Constrói a interface"""
        self.page.controls.clear()

        # Carregar tipos de conta disponíveis
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome FROM tipos_conta WHERE is_admin = 0')
        tipos = cursor.fetchall()
        conn.close()

        # Se não houver tipos não-admin, mostrar mensagem
        if not tipos:
            tipos_opcoes = [ft.dropdown.Option(key="0", text="Aguardando criação de tipos")]
        else:
            tipos_opcoes = [ft.dropdown.Option(key=str(t[0]), text=t[1]) for t in tipos]

        self.txt_nome = ft.TextField(
            label="Nome Completo *",
            prefix_icon=ft.Icons.PERSON,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.txt_cargo = ft.TextField(
            label="Cargo *",
            prefix_icon=ft.Icons.WORK,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.txt_email = ft.TextField(
            label="E-mail *",
            prefix_icon=ft.Icons.EMAIL,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.txt_login = ft.TextField(
            label="Login *",
            prefix_icon=ft.Icons.ACCOUNT_CIRCLE,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO,
            hint_text="Será usado para acessar o sistema"
        )

        self.txt_senha = ft.TextField(
            label="Senha *",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.txt_senha_confirm = ft.TextField(
            label="Confirmar Senha *",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            width=350,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.ddl_tipo = ft.Dropdown(
            label="Tipo de Conta *",
            width=350,
            options=tipos_opcoes,
            border_color=COR_AZUL_MEDIO,
            focused_border_color=COR_AZUL_ESCURO
        )

        self.lbl_mensagem = ft.Text(
            "",
            size=14,
            visible=False
        )

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PERSON_ADD, size=50, color=COR_AZUL_ESCURO),
                ft.Text(
                    "Criar Nova Conta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=COR_AZUL_ESCURO
                ),
                ft.Text(
                    "Preencha os dados para solicitar acesso",
                    size=14,
                    color=COR_TEXTO_SECUNDARIO
                ),
                ft.Container(height=15),
                self.txt_nome,
                self.txt_cargo,
                self.txt_email,
                self.txt_login,
                self.txt_senha,
                self.txt_senha_confirm,
                self.ddl_tipo if tipos else ft.Text(
                    "Nenhum tipo de conta disponível. Contate o administrador.",
                    color=COR_ALERTA, size=12
                ),
                self.lbl_mensagem,
                ft.Container(height=15),
                ft.FilledButton(
                    "Criar Conta",
                    icon=ft.Icons.PERSON_ADD,
                    width=350,
                    height=45,
                    bgcolor=COR_AZUL_ESCURO,
                    color=COR_BRANCO,
                    on_click=self.criar_conta,
                    disabled=not tipos
                ),
                ft.Container(height=10),
                ft.TextButton(
                    "Voltar ao login",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self.on_voltar()
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            scroll=ft.ScrollMode.AUTO),
            bgcolor=COR_BRANCO,
            padding=40,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 4)
            )
        )

        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    card
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
                expand=True,
                alignment=ft.alignment.top_center,
                bgcolor=COR_FUNDO,
                padding=ft.padding.only(top=20)
            )
        )
        self.page.update()

    def criar_conta(self, e):
        """Cria a conta do usuário"""
        nome = self.txt_nome.value.strip()
        cargo = self.txt_cargo.value.strip()
        email = self.txt_email.value.strip()
        login = self.txt_login.value.strip().lower()
        senha = self.txt_senha.value
        senha_confirm = self.txt_senha_confirm.value
        tipo_id = self.ddl_tipo.value

        # Validações
        if not all([nome, cargo, email, login, senha, senha_confirm, tipo_id]):
            self.mostrar_mensagem("Preencha todos os campos obrigatórios", erro=True)
            return

        if senha != senha_confirm:
            self.mostrar_mensagem("As senhas não coincidem", erro=True)
            return

        if len(senha) < 4:
            self.mostrar_mensagem("A senha deve ter pelo menos 4 caracteres", erro=True)
            return

        if "@" not in email:
            self.mostrar_mensagem("E-mail inválido", erro=True)
            return

        # Verificar se login já existe
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE login = ?', (login,))
        if cursor.fetchone():
            conn.close()
            self.mostrar_mensagem("Este login já está em uso", erro=True)
            return

        # Gerar código de recuperação
        codigo_rec = gerar_codigo_recuperacao()

        # Inserir usuário
        cursor.execute('''
            INSERT INTO usuarios (login, senha_hash, nome, cargo, email, tipo_conta_id,
                                 codigo_recuperacao, ativo, aprovado, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (login, hash_senha(senha), nome, cargo, email, int(tipo_id),
              codigo_rec, 0, 0, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        conn.commit()
        conn.close()

        # Mostrar diálogo de sucesso com código
        self.mostrar_dialogo_sucesso(codigo_rec)

    def mostrar_mensagem(self, mensagem, erro=False):
        """Mostra mensagem"""
        self.lbl_mensagem.value = mensagem
        self.lbl_mensagem.color = COR_ERRO if erro else COR_VERDE
        self.lbl_mensagem.visible = True
        self.page.update()

    def mostrar_dialogo_sucesso(self, codigo):
        """Mostra diálogo de sucesso"""
        def fechar(e):
            dlg.open = False
            self.page.update()
            self.on_voltar()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=COR_VERDE),
                ft.Text("Conta Criada!")
            ], spacing=10),
            content=ft.Column([
                ft.Text("Sua conta foi criada com sucesso!"),
                ft.Container(
                    content=ft.Text(
                        "Aguarde a aprovação de um administrador para acessar o sistema.",
                        color=COR_ALERTA
                    ),
                    bgcolor=ft.Colors.AMBER_50,
                    padding=10,
                    border_radius=8
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Seu código de recuperação:", weight=ft.FontWeight.BOLD),
                        ft.Text(codigo, size=18, color=COR_AZUL_ESCURO, selectable=True),
                        ft.Text("IMPORTANTE: Anote este código em local seguro!",
                               size=12, color=COR_ERRO, italic=True),
                        ft.Text("Você precisará dele para recuperar sua senha.",
                               size=12, color=COR_TEXTO_SECUNDARIO)
                    ]),
                    bgcolor=COR_FUNDO,
                    padding=15,
                    border_radius=8
                )
            ], tight=True),
            actions=[
                ft.FilledButton("OK, anotei o código", on_click=fechar)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


class ERPIntegrado:
    def __init__(self, page: ft.Page, usuario: str, user_data: dict):
        self.page = page
        self.usuario = usuario
        self.user_data = user_data
        self.favoritos = carregar_favoritos(user_data["id"])
        self.is_admin = user_data.get("is_admin", False)
        self.permissoes = obter_permissoes_usuario(user_data["tipo_conta_id"]) if not self.is_admin else None
        self.tray_icon = None  # Referência ao ícone da bandeja
        self.setup_page()
        self.modulos = self.configurar_modulos()
        self.build_ui()

    def setup_page(self):
        """Configurações iniciais da página"""
        self.page.title = "Sistema ERP Integrado - RENOVO"
        self.page.window.maximized = True
        self.page.window.min_width = 1200
        self.page.window.min_height = 700
        self.page.padding = 0
        self.page.bgcolor = COR_FUNDO

        # Interceptar fechamento forçado da janela (X)
        self.page.window.prevent_close = True
        self.page.window.on_event = self._on_window_event

        # Tema
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
            font_family="Segoe UI",
        )

    def _on_window_event(self, e):
        """Intercepta eventos da janela"""
        if e.data == "close":
            self.confirmar_fechar_erp(None)

    def configurar_modulos(self):
        """Configura os módulos disponíveis no sistema"""
        base_path = get_base_path()

        todos_modulos = [
            ModuloInfo(
                nome="CRM - Gestão Comercial",
                descricao="Gerenciamento de clientes, leads, oportunidades e pedidos",
                icone=ft.Icons.PEOPLE_ALT_ROUNDED,
                pasta=os.path.join(base_path, "Gerenciamento de Relacionamento com o Cliente"),
                arquivo_principal="app.py",
                cor=COR_MODULO_CRM,
                cor_escura=COR_MODULO_CRM_ESCURO
            ),
            ModuloInfo(
                nome="Gestão de Compras",
                descricao="Requisições, cotações e pedidos de compra",
                icone=ft.Icons.SHOPPING_CART_ROUNDED,
                pasta=os.path.join(base_path, "Gestão de Compras"),
                arquivo_principal="gc.py",
                cor=COR_MODULO_COMPRAS,
                cor_escura=COR_MODULO_COMPRAS_ESCURO
            ),
            ModuloInfo(
                nome="Recursos Humanos",
                descricao="Cadastro de colaboradores, folha de pagamento e documentos",
                icone=ft.Icons.BADGE_ROUNDED,
                pasta=os.path.join(base_path, "Sistema de Gestão de Recursos Humanos"),
                arquivo_principal="app.py",
                cor=COR_MODULO_RH,
                cor_escura=COR_MODULO_RH_ESCURO
            ),
            ModuloInfo(
                nome="Gestão Patrimonial",
                descricao="Controle de patrimônio, equipamentos e ativos",
                icone=ft.Icons.INVENTORY_2_ROUNDED,
                pasta=os.path.join(base_path, "Sistema de Gestão Patrimonial"),
                arquivo_principal="app.py",
                cor=COR_MODULO_PATRIMONIO,
                cor_escura=COR_MODULO_PATRIMONIO_ESCURO
            ),
            ModuloInfo(
                nome="Gestão de Documentos",
                descricao="Armazenamento e controle de documentos empresariais",
                icone=ft.Icons.FOLDER_ROUNDED,
                pasta="",
                arquivo_principal="",
                cor=COR_MODULO_DOCUMENTOS,
                cor_escura=COR_MODULO_DOCUMENTOS_ESCURO,
                ativo=False
            ),
            ModuloInfo(
                nome="SSMA - Segurança e Meio Ambiente",
                descricao="Saúde, segurança do trabalho e meio ambiente",
                icone=ft.Icons.HEALTH_AND_SAFETY_ROUNDED,
                pasta="",
                arquivo_principal="",
                cor=COR_MODULO_SSMA,
                cor_escura=COR_MODULO_SSMA_ESCURO,
                ativo=False
            ),
        ]

        # Filtrar por permissões se não for admin
        if not self.is_admin and self.permissoes is not None:
            return [m for m in todos_modulos if m.nome in self.permissoes or not m.ativo]

        return todos_modulos

    def toggle_favorito(self, modulo_nome):
        """Adiciona ou remove módulo dos favoritos"""
        if modulo_nome in self.favoritos:
            self.favoritos.remove(modulo_nome)
            salvar_favorito(self.user_data["id"], modulo_nome, adicionar=False)
        else:
            self.favoritos.append(modulo_nome)
            salvar_favorito(self.user_data["id"], modulo_nome, adicionar=True)
        self.atualizar_grid()

    def criar_card_modulo(self, modulo: ModuloInfo):
        """Cria um card para o módulo"""
        is_favorito = modulo.nome in self.favoritos

        def on_click(e):
            if modulo.ativo:
                self.abrir_modulo(modulo)
            else:
                self.mostrar_dialogo(
                    "Módulo em Desenvolvimento",
                    f"O módulo '{modulo.nome}' ainda está em desenvolvimento e será disponibilizado em breve.",
                    tipo="info"
                )

        def on_favorito_click(e):
            self.toggle_favorito(modulo.nome)

        card = ft.Container(
            content=ft.Column([
                # Header com ícone e favorito (fundo claro, ícones escuros)
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Icon(
                                modulo.icone,
                                size=48,
                                color=modulo.cor_escura  # Ícone com cor escura
                            ),
                            alignment=ft.alignment.center,
                            expand=True
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.STAR if is_favorito else ft.Icons.STAR_BORDER,
                                icon_color=ft.Colors.AMBER_600 if is_favorito else modulo.cor_escura,
                                icon_size=24,
                                tooltip="Favorito" if is_favorito else "Adicionar aos favoritos",
                                on_click=on_favorito_click
                            ),
                            alignment=ft.alignment.top_right
                        )
                    ]),
                    bgcolor=modulo.cor,  # Fundo claro
                    padding=ft.padding.all(20),
                    border_radius=ft.border_radius.only(
                        top_left=12,
                        top_right=12
                    ),
                    height=100
                ),
                # Conteúdo
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            modulo.nome,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COR_TEXTO
                        ),
                        ft.Text(
                            modulo.descricao,
                            size=13,
                            color=COR_TEXTO_SECUNDARIO,
                            max_lines=2
                        ),
                        ft.Container(height=10),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    "ATIVO" if modulo.ativo else "EM BREVE",
                                    size=10,
                                    color=COR_BRANCO,
                                    weight=ft.FontWeight.BOLD
                                ),
                                bgcolor=COR_VERDE if modulo.ativo else COR_TEXTO_SECUNDARIO,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            ),
                            ft.FilledButton(
                                "Abrir",
                                on_click=on_click,
                                disabled=not modulo.ativo,
                                bgcolor=modulo.cor_escura if modulo.ativo else ft.Colors.GREY_400,  # Botão com cor escura
                                color=COR_BRANCO,
                                height=32
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ], spacing=8),
                    padding=ft.padding.all(16)
                )
            ], spacing=0),
            bgcolor=COR_BRANCO,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            ),
            border=ft.border.all(2, ft.Colors.YELLOW_400) if is_favorito else None,
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            on_hover=lambda e: self.on_card_hover(e)
        )

        return card

    def on_card_hover(self, e):
        """Animação ao passar o mouse sobre o card"""
        if e.data == "true":
            e.control.scale = 1.03
        else:
            e.control.scale = 1.0
        e.control.update()

    def atualizar_grid(self):
        """Atualiza o grid de módulos"""
        # Ordenar: favoritos primeiro
        modulos_ordenados = sorted(
            self.modulos,
            key=lambda m: (m.nome not in self.favoritos, not m.ativo, m.nome)
        )

        self.grid_modulos.controls = [
            ft.Container(
                self.criar_card_modulo(modulo),
                col={"sm": 12, "md": 6, "lg": 4}
            )
            for modulo in modulos_ordenados
        ]
        self.page.update()

    def build_ui(self):
        """Constrói a interface do usuário"""
        self.page.controls.clear()

        # Caminho da logomarca
        base_path = get_base_path()
        logo_path = os.path.join(base_path, "imagens_principal", "Logomarca Renovo.png")

        # Botões do header baseado em permissões
        header_buttons = [
            ft.Column([
                ft.Text(
                    f"Olá, {self.user_data.get('nome', self.usuario)}",
                    color=COR_AZUL_ESCURO,
                    size=16,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    self.user_data.get('cargo', ''),
                    color=COR_TEXTO_SECUNDARIO,
                    size=12
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
        ]

        # Adicionar botão de administração se for admin
        if self.is_admin:
            # Contar contas pendentes para badge
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE aprovado = 0')
            qtd_pendentes = cursor.fetchone()[0]
            conn.close()

            if qtd_pendentes > 0:
                # Botão com badge de notificação
                header_buttons.append(
                    ft.Stack(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                                icon_color=COR_AZUL_ESCURO,
                                tooltip=f"Administração ({qtd_pendentes} pendente{'s' if qtd_pendentes > 1 else ''})",
                                on_click=self.abrir_admin
                            ),
                            ft.Container(
                                content=ft.Text(
                                    str(qtd_pendentes),
                                    size=10,
                                    color=COR_BRANCO,
                                    weight=ft.FontWeight.BOLD
                                ),
                                bgcolor=COR_ERRO,
                                border_radius=10,
                                padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                right=0,
                                top=0
                            )
                        ]
                    )
                )
            else:
                header_buttons.append(
                    ft.IconButton(
                        icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                        icon_color=COR_AZUL_ESCURO,
                        tooltip="Administração",
                        on_click=self.abrir_admin
                    )
                )

        header_buttons.extend([
            ft.IconButton(
                icon=ft.Icons.HISTORY,
                icon_color=COR_AZUL_ESCURO,
                tooltip="Histórico de acessos",
                on_click=self.mostrar_historico
            ),
            ft.IconButton(
                icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                icon_color=COR_AZUL_ESCURO,
                tooltip="Sobre o sistema",
                on_click=self.mostrar_sobre
            ),
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                icon_color=COR_AZUL_ESCURO,
                tooltip="Deslogar",
                on_click=self.fazer_logout
            ),
            ft.IconButton(
                icon=ft.Icons.POWER_SETTINGS_NEW,
                icon_color=COR_ERRO,
                tooltip="Fechar ERP",
                on_click=self.confirmar_fechar_erp
            )
        ])

        # Header com fundo branco
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Image(
                        src=logo_path,
                        width=200,
                        height=120,
                        fit=ft.ImageFit.CONTAIN
                    ) if os.path.exists(logo_path) else ft.Icon(ft.Icons.DASHBOARD_ROUNDED, size=32, color=COR_AZUL_ESCURO),
                    ft.Column([
                        ft.Text(
                            "Sistema ERP Integrado",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=COR_AZUL_ESCURO
                        ),
                        ft.Text(
                            "RENOVO Montagens Industriais",
                            size=14,
                            color=COR_TEXTO_SECUNDARIO
                        )
                    ], spacing=2)
                ], spacing=16),
                ft.Row(header_buttons, spacing=8)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=COR_BRANCO,
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            border=ft.border.only(bottom=ft.BorderSide(2, COR_AZUL_CLARO)),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )

        # Ordenar módulos: favoritos primeiro
        modulos_ordenados = sorted(
            self.modulos,
            key=lambda m: (m.nome not in self.favoritos, not m.ativo, m.nome)
        )

        # Grid de módulos
        self.grid_modulos = ft.ResponsiveRow([
            ft.Container(
                self.criar_card_modulo(modulo),
                col={"sm": 12, "md": 6, "lg": 4}
            )
            for modulo in modulos_ordenados
        ], spacing=20)

        # Container principal com scroll
        main_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Módulos Disponíveis",
                        size=20,
                        weight=ft.FontWeight.W_500,
                        color=COR_TEXTO
                    ),
                    ft.Text(
                        f"| {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO
                    )
                ], spacing=10),
                ft.Divider(height=20, thickness=1, color=ft.Colors.GREY_300),
                self.grid_modulos
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(24),
            expand=True
        )

        # Footer
        footer = ft.Container(
            content=ft.Row([
                ft.Text(
                    f"Sistema ERP Integrado - Versão {VERSAO}",
                    size=12,
                    color=COR_TEXTO_SECUNDARIO
                ),
                ft.Text(
                    "RENOVO Montagens Industriais",
                    size=12,
                    color=COR_TEXTO_SECUNDARIO
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=COR_BRANCO,
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
        )

        # Layout principal
        self.page.add(
            ft.Column([
                header,
                ft.Container(
                    content=main_content,
                    expand=True,
                    bgcolor=COR_FUNDO
                ),
                footer
            ], spacing=0, expand=True)
        )
        self.page.update()

    def abrir_modulo(self, modulo: ModuloInfo):
        """Abre o módulo selecionado"""
        # Verifica se é o módulo de Compras - mostra diálogo de escolha
        if modulo.nome == "Gestão de Compras":
            self.mostrar_escolha_compras(modulo)
            return

        self._executar_abertura_modulo(modulo, modulo.arquivo_principal)

    def mostrar_escolha_compras(self, modulo: ModuloInfo):
        """Mostra diálogo para escolher qual submódulo de Compras abrir"""
        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()

        def abrir_gestao_compras(e):
            dialog.open = False
            self.page.update()
            self._executar_abertura_modulo(modulo, "gc.py", "Gestão de Compras")

        def abrir_relatorio_compras(e):
            dialog.open = False
            self.page.update()
            self._executar_abertura_modulo(modulo, "rcn.py", "Relatório de Compras e Notas")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SHOPPING_CART_ROUNDED, color=COR_MODULO_COMPRAS_ESCURO, size=28),
                ft.Text("Módulo de Compras", weight=ft.FontWeight.BOLD, size=18),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Selecione qual área deseja acessar:",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO
                    ),
                    ft.Container(height=15),
                    # Opção 1 - Gestão de Compras
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.INVENTORY_ROUNDED, color=COR_BRANCO, size=24),
                                bgcolor=COR_MODULO_COMPRAS_ESCURO,
                                border_radius=8,
                                padding=12,
                            ),
                            ft.Column([
                                ft.Text("Gestão de Compras", weight=ft.FontWeight.BOLD, size=14),
                                ft.Text("Requisições, cotações e pedidos de compra", size=11, color=COR_TEXTO_SECUNDARIO),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=COR_TEXTO_SECUNDARIO),
                        ], spacing=15),
                        padding=15,
                        border_radius=10,
                        bgcolor=COR_FUNDO,
                        ink=True,
                        on_click=abrir_gestao_compras,
                    ),
                    ft.Container(height=10),
                    # Opção 2 - Relatório de Compras e Notas
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=COR_BRANCO, size=24),
                                bgcolor=COR_MODULO_COMPRAS_ESCURO,
                                border_radius=8,
                                padding=12,
                            ),
                            ft.Column([
                                ft.Text("Relatório de Compras e Notas", weight=ft.FontWeight.BOLD, size=14),
                                ft.Text("Visualização e relatórios de compras e notas fiscais", size=11, color=COR_TEXTO_SECUNDARIO),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=COR_TEXTO_SECUNDARIO),
                        ], spacing=15),
                        padding=15,
                        border_radius=10,
                        bgcolor=COR_FUNDO,
                        ink=True,
                        on_click=abrir_relatorio_compras,
                    ),
                ], spacing=0, tight=True),
                width=400,
                padding=10,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _executar_abertura_modulo(self, modulo: ModuloInfo, arquivo: str, nome_submodulo: str = None):
        """Executa a abertura do módulo"""
        try:
            # Verifica se o arquivo existe
            arquivo_completo = os.path.join(modulo.pasta, arquivo)

            if not os.path.exists(arquivo_completo):
                self.mostrar_dialogo(
                    "Erro",
                    f"Arquivo não encontrado: {arquivo_completo}",
                    tipo="erro"
                )
                return

            # Registra o acesso no log
            nome_log = nome_submodulo if nome_submodulo else modulo.nome
            registrar_log(self.user_data["id"], self.usuario, "Acessou módulo", nome_log)

            # Monta o comando para executar o módulo diretamente com Python
            # Passa os dados do usuário como argumentos
            if arquivo.endswith('.py'):
                # Preparar argumentos (substituir espaços por underscores temporariamente se necessário)
                nome_usuario = self.user_data.get("nome", "") or "Usuario"
                cargo_usuario = self.user_data.get("cargo", "") or "Cargo"

                comando = [
                    sys.executable,
                    arquivo_completo,
                    "--usuario", self.usuario,
                    "--nome", nome_usuario,
                    "--cargo", cargo_usuario,
                    "--erp_path", os.path.abspath(__file__)
                ]
            else:
                self.mostrar_dialogo(
                    "Erro",
                    "Tipo de arquivo não suportado",
                    tipo="erro"
                )
                return

            # Mostra tela de standby
            nome_standby = nome_submodulo if nome_submodulo else modulo.nome
            self.mostrar_standby(nome_standby)

            # Função para executar o módulo em thread separada
            def executar_modulo():
                time.sleep(0.5)  # Pequeno delay para UI atualizar
                subprocess.Popen(comando, cwd=modulo.pasta)
                time.sleep(1)  # Aguarda módulo iniciar
                # Minimiza o ERP para o tray
                self.minimizar_para_tray()

            # Inicia em thread separada para não bloquear a UI
            threading.Thread(target=executar_modulo, daemon=True).start()

        except Exception as ex:
            self.build_ui()
            self.mostrar_dialogo(
                "Erro ao abrir módulo",
                f"Não foi possível abrir o módulo: {str(ex)}",
                tipo="erro"
            )

    def mostrar_standby(self, nome_modulo):
        """Mostra tela de standby enquanto o módulo abre"""
        self.page.controls.clear()

        base_path = get_base_path()
        logo_path = os.path.join(base_path, "imagens_principal", "Logomarca Renovo.png")

        standby_screen = ft.Container(
            content=ft.Column([
                ft.Image(
                    src=logo_path,
                    width=200,
                    height=120,
                    fit=ft.ImageFit.CONTAIN
                ) if os.path.exists(logo_path) else ft.Icon(ft.Icons.HOURGLASS_EMPTY, size=60, color=COR_AZUL_ESCURO),
                ft.Container(height=30),
                ft.ProgressRing(
                    width=50,
                    height=50,
                    stroke_width=4,
                    color=COR_AZUL_ESCURO
                ),
                ft.Container(height=20),
                ft.Text(
                    "Aguardando Abertura do Módulo",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=COR_AZUL_ESCURO
                ),
                ft.Text(
                    nome_modulo,
                    size=16,
                    color=COR_TEXTO_SECUNDARIO
                ),
                ft.Container(height=20),
                ft.Text(
                    "O módulo será aberto em instantes...",
                    size=14,
                    color=COR_TEXTO_SECUNDARIO,
                    italic=True
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=COR_BRANCO
        )

        self.page.add(standby_screen)
        self.page.update()

    def minimizar_para_tray(self):
        """Minimiza o ERP para a bandeja do sistema (tray icon)"""
        base_path = get_base_path()
        logo_path = os.path.join(base_path, "imagens_principal", "Logomarca Renovo.png")
        signal_file = os.path.join(base_path, ".erp_restore_signal")

        # Remove arquivo de sinal se existir
        if os.path.exists(signal_file):
            try:
                os.remove(signal_file)
            except:
                pass

        # Cria o ícone para o tray
        try:
            if os.path.exists(logo_path):
                icon_image = Image.open(logo_path)
                icon_image = icon_image.resize((64, 64))
            else:
                # Cria um ícone simples se não encontrar a logo
                icon_image = Image.new('RGB', (64, 64), color=(13, 71, 161))
        except:
            icon_image = Image.new('RGB', (64, 64), color=(13, 71, 161))

        # Flag para controlar o monitoramento
        self.tray_monitoring = True

        def restaurar_erp_interno():
            """Restaura a janela do ERP (interno)"""
            self.tray_monitoring = False
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
            # Remove arquivo de sinal
            if os.path.exists(signal_file):
                try:
                    os.remove(signal_file)
                except:
                    pass
            # Restaura a janela
            self.page.window.visible = True
            self.page.window.minimized = False
            self.page.window.maximized = True
            self.build_ui()
            self.page.update()

        def restaurar_erp(icon, item):
            """Restaura a janela do ERP (via menu)"""
            restaurar_erp_interno()

        def fechar_erp(icon, item):
            """Fecha o ERP completamente"""
            self.tray_monitoring = False
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
            # Remove arquivo de sinal
            if os.path.exists(signal_file):
                try:
                    os.remove(signal_file)
                except:
                    pass
            self.page.window.close()

        def monitorar_sinal():
            """Monitora o arquivo de sinal para restaurar o ERP"""
            while self.tray_monitoring:
                if os.path.exists(signal_file):
                    # Sinal recebido - restaurar ERP
                    restaurar_erp_interno()
                    break
                time.sleep(0.5)  # Verifica a cada 500ms

        # Menu do tray icon
        menu = pystray.Menu(
            pystray.MenuItem("Abrir ERP", restaurar_erp, default=True),
            pystray.MenuItem("Fechar", fechar_erp)
        )

        # Cria o ícone na bandeja
        self.tray_icon = pystray.Icon(
            "ERP Renovo",
            icon_image,
            "ERP Integrado - Renovo",
            menu
        )

        # Esconde a janela do ERP
        self.page.window.visible = False
        self.page.update()

        # Executa o tray icon em thread separada
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

        # Inicia o monitoramento do arquivo de sinal
        threading.Thread(target=monitorar_sinal, daemon=True).start()

    def abrir_admin(self, e):
        """Abre o painel de administração"""
        PainelAdmin(self.page, self.user_data, self.voltar_erp)

    def voltar_erp(self):
        """Volta para o ERP"""
        self.build_ui()

    def fazer_logout(self, e):
        """Realiza o logout"""
        registrar_log(self.user_data["id"], self.usuario, "Logout do sistema", "ERP")
        self.page.controls.clear()
        self.page.update()
        # Reinicia com a tela de login
        def on_login_success(usuario, user_data):
            self.page.controls.clear()
            self.page.update()
            ERPIntegrado(self.page, usuario, user_data)
        TelaLogin(self.page, on_login_success)

    def confirmar_fechar_erp(self, e):
        """Mostra diálogo de confirmação para fechar o ERP"""
        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()

        def confirmar_fechamento(e):
            dialog.open = False
            self.page.update()
            self.fechar_erp_seguro()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color=COR_ERRO, size=24),
                ft.Text("Fechar Sistema ERP", weight=ft.FontWeight.BOLD, color=COR_AZUL_ESCURO, size=16)
            ], spacing=8),
            content=ft.Text(
                "Deseja realmente fechar o Sistema ERP?\nTodas as conexões serão encerradas de forma segura.",
                size=13,
                color=COR_TEXTO
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=fechar_dialogo
                ),
                ft.ElevatedButton(
                    "Fechar ERP",
                    icon=ft.Icons.POWER_SETTINGS_NEW,
                    bgcolor=COR_ERRO,
                    color=COR_BRANCO,
                    on_click=confirmar_fechamento
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def fechar_erp_seguro(self):
        """Fecha o ERP de forma segura, salvando tudo e encerrando conexões"""
        try:
            # Registrar log de fechamento
            registrar_log(self.user_data["id"], self.usuario, "Fechamento seguro do sistema", "ERP")

            # Fechar ícone do tray se existir
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                    self.tray_icon = None
                except:
                    pass

            # Remover arquivo de sinal se existir
            signal_file = os.path.join(get_base_path(), ".erp_restore_signal")
            if os.path.exists(signal_file):
                try:
                    os.remove(signal_file)
                except:
                    pass

            # Fechar conexão com banco de dados (commit final)
            try:
                conn = get_connection()
                conn.commit()
                conn.close()
            except:
                pass

        except Exception:
            pass
        finally:
            # Fechar a janela
            self.page.window.destroy()

    def mostrar_historico(self, e):
        """Mostra histórico de acessos - Admin vê todos, usuários comuns veem apenas os próprios"""
        # Administradores veem todos os logs, usuários comuns apenas os próprios
        if self.is_admin:
            logs = carregar_logs(100)
            titulo_log = "Histórico de Acessos (Todos)"
        else:
            logs = carregar_logs(100, usuario_login=self.usuario)
            titulo_log = "Meu Histórico de Acessos"

        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()

        # Criar lista de logs
        log_items = []
        for log in logs:
            log_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.PERSON if log["acao"] == "Login no sistema" else
                            ft.Icons.LOGOUT if log["acao"] == "Logout do sistema" else
                            ft.Icons.OPEN_IN_NEW,
                            size=20,
                            color=COR_AZUL_MEDIO
                        ),
                        ft.Column([
                            ft.Text(
                                f"{log['usuario']} - {log['acao']}",
                                size=13,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Text(
                                f"{log['modulo']} | {log['data']} às {log['hora']}",
                                size=11,
                                color=COR_TEXTO_SECUNDARIO
                            )
                        ], spacing=2, expand=True)
                    ], spacing=10),
                    padding=ft.padding.symmetric(vertical=8, horizontal=4),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
                )
            )

        # Mensagem informativa para usuários não-admin
        info_text = None
        if not self.is_admin:
            info_text = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=COR_TEXTO_SECUNDARIO),
                    ft.Text(
                        "Você está visualizando apenas suas próprias atividades.",
                        size=11,
                        color=COR_TEXTO_SECUNDARIO,
                        italic=True
                    )
                ], spacing=5),
                padding=ft.padding.only(bottom=10)
            )

        content_items = []
        if info_text:
            content_items.append(info_text)
        if log_items:
            content_items.extend(log_items)
        else:
            content_items.append(ft.Text("Nenhum registro encontrado"))

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.HISTORY, color=COR_AZUL_ESCURO),
                ft.Text(titulo_log)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(
                    content_items,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=500,
                height=400
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar_dialogo)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def mostrar_sobre(self, e):
        """Mostra informações sobre o sistema"""

        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.INFO, color=COR_AZUL_ESCURO),
                ft.Text("Sobre o Sistema")
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Sistema ERP Integrado",
                        weight=ft.FontWeight.BOLD,
                        size=18,
                        color=COR_AZUL_ESCURO
                    ),
                    ft.Text(
                        "RENOVO Montagens Industriais",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO
                    ),
                    ft.Divider(height=15),
                    # Informações do desenvolvedor
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Desenvolvedor", size=14, weight=ft.FontWeight.BOLD, color=COR_AZUL_ESCURO),
                            ft.Text(
                                "Fernando Albéniz Machado de Moura Guedes",
                                size=13,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Row([
                                ft.Icon(ft.Icons.PHONE, size=16, color=COR_TEXTO_SECUNDARIO),
                                ft.Text("83 9 9638-1689", size=12),
                            ], spacing=8),
                            ft.Row([
                                ft.Icon(ft.Icons.EMAIL, size=16, color=COR_TEXTO_SECUNDARIO),
                                ft.Text("fernando.guedes@renovomontagens.com.br", size=12),
                            ], spacing=8),
                        ], spacing=5),
                        bgcolor=COR_FUNDO,
                        padding=15,
                        border_radius=8
                    ),
                    ft.Divider(height=15),
                    # Informações do sistema
                    ft.Row([
                        ft.Text("Versão:", weight=ft.FontWeight.W_500),
                        ft.Text(f"{VERSAO}"),
                    ], spacing=8),
                    ft.Row([
                        ft.Text("Tecnologia:", weight=ft.FontWeight.W_500),
                        ft.Text("Python + Flet Framework"),
                    ], spacing=8),
                    ft.Divider(height=15),
                    ft.Text("Módulos integrados:", weight=ft.FontWeight.BOLD),
                    ft.Text("• CRM - Gestão Comercial"),
                    ft.Text("• Gestão de Compras"),
                    ft.Text("• Recursos Humanos"),
                    ft.Text("• Gestão Patrimonial"),
                    ft.Divider(height=10),
                    ft.Text("Em desenvolvimento:", weight=ft.FontWeight.BOLD),
                    ft.Text("• Gestão de Documentos"),
                    ft.Text("• SMS - Segurança e Meio Ambiente"),
                    ft.Divider(height=15),
                    ft.Text(
                        "© 2025 RENOVO Montagens - Todos os direitos reservados",
                        size=11,
                        color=COR_TEXTO_SECUNDARIO,
                        text_align=ft.TextAlign.CENTER
                    ),
                ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar_dialogo)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def mostrar_dialogo(self, titulo, mensagem, tipo="info"):
        """Mostra diálogo de mensagem"""

        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()

        # Define cor e ícone baseado no tipo
        if tipo == "erro":
            cor = COR_ERRO
            icone = ft.Icons.ERROR_OUTLINE_ROUNDED
        elif tipo == "sucesso":
            cor = COR_VERDE
            icone = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
        elif tipo == "alerta":
            cor = COR_ALERTA
            icone = ft.Icons.WARNING_AMBER_ROUNDED
        else:
            cor = COR_AZUL_MEDIO
            icone = ft.Icons.INFO_OUTLINE_ROUNDED

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(icone, color=cor),
                ft.Text(titulo)
            ], spacing=8),
            content=ft.Text(mensagem),
            actions=[
                ft.TextButton("OK", on_click=fechar_dialogo)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


class PainelAdmin:
    """Painel de administração do sistema"""
    def __init__(self, page: ft.Page, user_data: dict, on_voltar):
        self.page = page
        self.user_data = user_data
        self.on_voltar = on_voltar
        self.aba_atual = 0
        self.build_ui()

    def build_ui(self):
        """Constrói a interface do painel"""
        self.page.controls.clear()

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=32, color=COR_BRANCO),
                    ft.Text(
                        "Painel de Administração",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=COR_BRANCO
                    )
                ], spacing=16),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=COR_BRANCO,
                    tooltip="Voltar ao sistema",
                    on_click=lambda e: self.on_voltar()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=COR_AZUL_ESCURO,
            padding=ft.padding.symmetric(horizontal=24, vertical=16)
        )

        # Contar contas pendentes para o badge
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE aprovado = 0')
        qtd_pendentes = cursor.fetchone()[0]
        conn.close()

        # Tab de contas pendentes com badge
        if qtd_pendentes > 0:
            tab_pendentes = ft.Tab(
                tab_content=ft.Row([
                    ft.Icon(ft.Icons.PENDING_ACTIONS, size=20),
                    ft.Text("Contas Pendentes"),
                    ft.Container(
                        content=ft.Text(
                            str(qtd_pendentes),
                            size=12,
                            color=COR_BRANCO,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=COR_ERRO,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)
                    )
                ], spacing=8),
                content=self.criar_aba_pendentes()
            )
        else:
            tab_pendentes = ft.Tab(
                text="Contas Pendentes",
                icon=ft.Icons.PENDING_ACTIONS,
                content=self.criar_aba_pendentes()
            )

        # Tabs
        self.tabs = ft.Tabs(
            selected_index=self.aba_atual,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Usuários",
                    icon=ft.Icons.PEOPLE,
                    content=self.criar_aba_usuarios()
                ),
                tab_pendentes,
                ft.Tab(
                    text="Tipos de Conta",
                    icon=ft.Icons.CATEGORY,
                    content=self.criar_aba_tipos()
                ),
            ],
            expand=True,
            on_change=self.on_tab_change
        )

        self.page.add(
            ft.Column([
                header,
                ft.Container(
                    content=self.tabs,
                    expand=True,
                    bgcolor=COR_FUNDO,
                    padding=20
                )
            ], spacing=0, expand=True)
        )
        self.page.update()

    def on_tab_change(self, e):
        """Atualiza a aba atual"""
        self.aba_atual = e.control.selected_index

    def criar_aba_usuarios(self):
        """Cria a aba de gerenciamento de usuários"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.login, u.nome, u.cargo, u.email, t.nome, u.ativo, u.aprovado, u.data_criacao
            FROM usuarios u
            LEFT JOIN tipos_conta t ON u.tipo_conta_id = t.id
            WHERE u.aprovado = 1
            ORDER BY u.nome
        ''')
        usuarios = cursor.fetchall()
        conn.close()

        rows = []
        for u in usuarios:
            user_id, login, nome, cargo, email, tipo, ativo, aprovado, data = u
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(login)),
                        ft.DataCell(ft.Text(nome)),
                        ft.DataCell(ft.Text(cargo or "-")),
                        ft.DataCell(ft.Text(tipo or "-")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("Ativo" if ativo else "Inativo",
                                              color=COR_BRANCO, size=11),
                                bgcolor=COR_VERDE if ativo else COR_ERRO,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=COR_AZUL_MEDIO,
                                    tooltip="Editar",
                                    on_click=lambda e, uid=user_id: self.editar_usuario(uid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.LOCK_RESET,
                                    icon_color=COR_ALERTA,
                                    tooltip="Resetar senha",
                                    on_click=lambda e, uid=user_id: self.resetar_senha(uid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.BLOCK if ativo else ft.Icons.CHECK_CIRCLE,
                                    icon_color=COR_ERRO if ativo else COR_VERDE,
                                    tooltip="Desativar" if ativo else "Ativar",
                                    on_click=lambda e, uid=user_id, at=ativo: self.toggle_ativo(uid, at)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_FOREVER,
                                    icon_color=COR_ERRO,
                                    tooltip="Excluir usuário",
                                    on_click=lambda e, uid=user_id, ulogin=login: self.excluir_usuario(uid, ulogin)
                                ),
                            ], spacing=0)
                        )
                    ]
                )
            )

        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Login")),
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Cargo")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.GREY_100,
        )

        return ft.Container(
            content=ft.Column([
                ft.Text("Usuários Cadastrados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Container(
                    content=tabela,
                    bgcolor=COR_BRANCO,
                    border_radius=8,
                    padding=10
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def criar_aba_pendentes(self):
        """Cria a aba de contas pendentes de aprovação"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.login, u.nome, u.cargo, u.email, t.nome, u.data_criacao
            FROM usuarios u
            LEFT JOIN tipos_conta t ON u.tipo_conta_id = t.id
            WHERE u.aprovado = 0
            ORDER BY u.data_criacao DESC
        ''')
        pendentes = cursor.fetchall()
        conn.close()

        if not pendentes:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=60, color=COR_VERDE),
                    ft.Text("Nenhuma conta pendente de aprovação", size=16)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                alignment=ft.alignment.center
            )

        rows = []
        for p in pendentes:
            user_id, login, nome, cargo, email, tipo, data = p
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(login)),
                        ft.DataCell(ft.Text(nome)),
                        ft.DataCell(ft.Text(cargo or "-")),
                        ft.DataCell(ft.Text(email or "-")),
                        ft.DataCell(ft.Text(tipo or "-")),
                        ft.DataCell(ft.Text(data or "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.FilledButton(
                                    "Aprovar",
                                    bgcolor=COR_VERDE,
                                    color=COR_BRANCO,
                                    on_click=lambda e, uid=user_id: self.aprovar_conta(uid)
                                ),
                                ft.OutlinedButton(
                                    "Rejeitar",
                                    on_click=lambda e, uid=user_id: self.rejeitar_conta(uid)
                                )
                            ], spacing=5)
                        )
                    ]
                )
            )

        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Login")),
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Cargo")),
                ft.DataColumn(ft.Text("E-mail")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.GREY_100,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Contas Pendentes de Aprovação", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(f"{len(pendentes)}", color=COR_BRANCO, size=12),
                        bgcolor=COR_ALERTA,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=12
                    )
                ], spacing=10),
                ft.Container(height=10),
                ft.Container(
                    content=tabela,
                    bgcolor=COR_BRANCO,
                    border_radius=8,
                    padding=10
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def criar_aba_tipos(self):
        """Cria a aba de gerenciamento de tipos de conta"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome, descricao, is_admin, protegido FROM tipos_conta ORDER BY nome')
        tipos = cursor.fetchall()
        conn.close()

        rows = []
        for t in tipos:
            tipo_id, nome, descricao, is_admin, protegido = t

            # Carregar permissões do tipo
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT modulo FROM permissoes WHERE tipo_conta_id = ? AND permitido = 1', (tipo_id,))
            perms = [p[0] for p in cursor.fetchall()]
            conn.close()

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(nome, weight=ft.FontWeight.BOLD if is_admin else None)),
                        ft.DataCell(ft.Text(descricao or "-")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("Sim" if is_admin else "Não", color=COR_BRANCO, size=11),
                                bgcolor=COR_AZUL_ESCURO if is_admin else COR_TEXTO_SECUNDARIO,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            )
                        ),
                        ft.DataCell(ft.Text(", ".join(perms[:3]) + ("..." if len(perms) > 3 else "") if perms else "Nenhum")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=COR_AZUL_MEDIO,
                                    tooltip="Editar",
                                    on_click=lambda e, tid=tipo_id: self.editar_tipo(tid),
                                    disabled=protegido == 1
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=COR_ERRO,
                                    tooltip="Excluir",
                                    on_click=lambda e, tid=tipo_id: self.excluir_tipo(tid),
                                    disabled=protegido == 1
                                ),
                            ], spacing=0)
                        )
                    ]
                )
            )

        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Admin?")),
                ft.DataColumn(ft.Text("Permissões")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.GREY_100,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Tipos de Conta", size=18, weight=ft.FontWeight.BOLD),
                    ft.FilledButton(
                        "Novo Tipo",
                        icon=ft.Icons.ADD,
                        bgcolor=COR_AZUL_ESCURO,
                        color=COR_BRANCO,
                        on_click=self.novo_tipo
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Container(
                    content=tabela,
                    bgcolor=COR_BRANCO,
                    border_radius=8,
                    padding=10
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def aprovar_conta(self, user_id):
        """Aprova uma conta pendente"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE usuarios SET aprovado = 1, ativo = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        self.build_ui()
        self.mostrar_snackbar("Conta aprovada com sucesso!")

    def rejeitar_conta(self, user_id):
        """Rejeita (exclui) uma conta pendente"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        self.build_ui()
        self.mostrar_snackbar("Conta rejeitada e removida.")

    def toggle_ativo(self, user_id, ativo_atual):
        """Ativa ou desativa um usuário"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE usuarios SET ativo = ? WHERE id = ?', (0 if ativo_atual else 1, user_id))
        conn.commit()
        conn.close()
        self.build_ui()
        self.mostrar_snackbar("Status do usuário atualizado!")

    def resetar_senha(self, user_id):
        """Reseta a senha do usuário para 'renovo'"""
        conn = get_connection()
        cursor = conn.cursor()
        novo_codigo = gerar_codigo_recuperacao()
        cursor.execute('''
            UPDATE usuarios SET senha_hash = ?, codigo_recuperacao = ? WHERE id = ?
        ''', (hash_senha("renovo"), novo_codigo, user_id))
        conn.commit()
        conn.close()

        # Mostrar diálogo com informações
        def fechar(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Senha Resetada"),
            content=ft.Column([
                ft.Text("A senha foi resetada com sucesso!"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Nova senha: renovo", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Novo código: {novo_codigo}", size=12)
                    ]),
                    bgcolor=COR_FUNDO,
                    padding=15,
                    border_radius=8
                )
            ], tight=True),
            actions=[ft.TextButton("OK", on_click=fechar)]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def excluir_usuario(self, user_id, login):
        """Exclui um usuário do sistema com confirmação"""
        # Verificar se não é o próprio usuário logado
        if user_id == self.user_data.get("id"):
            self.mostrar_snackbar("Você não pode excluir sua própria conta!")
            return

        def confirmar_exclusao(e):
            dlg_confirm.open = False
            self.page.update()

            # Buscar informações do usuário antes de excluir
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT nome, cargo, email FROM usuarios WHERE id = ?', (user_id,))
            user_info = cursor.fetchone()
            conn.close()

            if user_info:
                nome_excluido, cargo_excluido, email_excluido = user_info
                # Registrar log da exclusão com informações do usuário excluído
                admin_login = self.user_data.get("login", "admin")
                admin_id = self.user_data.get("id", 0)
                registrar_log(
                    admin_id,
                    admin_login,
                    f"Conta excluída - Usuário: {login} | Nome: {nome_excluido} | Cargo: {cargo_excluido or 'N/A'} | Email: {email_excluido or 'N/A'}",
                    "Administração"
                )

            # Excluir o usuário
            conn = get_connection()
            cursor = conn.cursor()
            # Excluir favoritos do usuário primeiro
            cursor.execute('DELETE FROM favoritos WHERE usuario_id = ?', (user_id,))
            # Excluir o usuário
            cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()

            self.build_ui()
            self.mostrar_snackbar(f"Usuário '{login}' excluído com sucesso!")

        def cancelar(e):
            dlg_confirm.open = False
            self.page.update()

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color=COR_ERRO, size=28),
                ft.Text("Confirmar Exclusão", color=COR_ERRO)
            ], spacing=8),
            content=ft.Column([
                ft.Text(f"Tem certeza que deseja excluir o usuário '{login}'?"),
                ft.Text("Esta ação não pode ser desfeita!",
                       size=12, color=COR_ERRO, italic=True),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.FilledButton(
                    "Excluir",
                    bgcolor=COR_ERRO,
                    color=COR_BRANCO,
                    on_click=confirmar_exclusao
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.overlay.append(dlg_confirm)
        dlg_confirm.open = True
        self.page.update()

    def editar_usuario(self, user_id):
        """Abre diálogo para editar usuário"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT login, nome, cargo, email, tipo_conta_id FROM usuarios WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        cursor.execute('SELECT id, nome FROM tipos_conta')
        tipos = cursor.fetchall()
        conn.close()

        if not user:
            return

        login, nome, cargo, email, tipo_id = user

        txt_nome = ft.TextField(label="Nome", value=nome, width=300)
        txt_cargo = ft.TextField(label="Cargo", value=cargo or "", width=300)
        txt_email = ft.TextField(label="E-mail", value=email or "", width=300)
        ddl_tipo = ft.Dropdown(
            label="Tipo de Conta",
            width=300,
            value=str(tipo_id) if tipo_id else None,
            options=[ft.dropdown.Option(key=str(t[0]), text=t[1]) for t in tipos]
        )

        def salvar(e):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios SET nome = ?, cargo = ?, email = ?, tipo_conta_id = ? WHERE id = ?
            ''', (txt_nome.value, txt_cargo.value, txt_email.value, int(ddl_tipo.value) if ddl_tipo.value else None, user_id))
            conn.commit()
            conn.close()
            dlg.open = False
            self.page.update()
            self.build_ui()
            self.mostrar_snackbar("Usuário atualizado!")

        def fechar(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar Usuário: {login}"),
            content=ft.Column([txt_nome, txt_cargo, txt_email, ddl_tipo], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton("Salvar", on_click=salvar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def novo_tipo(self, e):
        """Abre diálogo para criar novo tipo de conta"""
        txt_nome = ft.TextField(label="Nome do Tipo *", width=300)
        txt_descricao = ft.TextField(label="Descrição", width=300)
        chk_admin = ft.Checkbox(label="É administrador?", value=False)

        # Lista de módulos
        modulos = ['CRM - Gestão Comercial', 'Gestão de Compras', 'Recursos Humanos',
                   'Gestão Patrimonial', 'Gestão de Documentos', 'SMS - Segurança e Meio Ambiente']

        checkboxes_modulos = [ft.Checkbox(label=m, value=False) for m in modulos]

        def salvar(e):
            if not txt_nome.value:
                return

            conn = get_connection()
            cursor = conn.cursor()

            # Verificar se já existe
            cursor.execute('SELECT id FROM tipos_conta WHERE nome = ?', (txt_nome.value,))
            if cursor.fetchone():
                conn.close()
                # Mostrar alerta de tipo já existente
                def fechar_alerta(ev):
                    alerta.open = False
                    self.page.update()

                alerta = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Tipo já existe"),
                    content=ft.Text(f"O tipo de conta '{txt_nome.value}' já está cadastrado."),
                    actions=[ft.TextButton("OK", on_click=fechar_alerta)]
                )
                self.page.overlay.append(alerta)
                alerta.open = True
                self.page.update()
                return

            # Inserir tipo
            cursor.execute('''
                INSERT INTO tipos_conta (nome, descricao, is_admin, protegido, data_criacao)
                VALUES (?, ?, ?, 0, ?)
            ''', (txt_nome.value, txt_descricao.value, 1 if chk_admin.value else 0,
                  datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
            tipo_id = cursor.lastrowid

            # Inserir permissões
            for i, cb in enumerate(checkboxes_modulos):
                cursor.execute('''
                    INSERT INTO permissoes (tipo_conta_id, modulo, permitido)
                    VALUES (?, ?, ?)
                ''', (tipo_id, modulos[i], 1 if cb.value else 0))

            conn.commit()
            conn.close()

            dlg.open = False
            self.page.update()
            self.build_ui()
            self.mostrar_snackbar("Tipo de conta criado!")

        def fechar(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Novo Tipo de Conta"),
            content=ft.Column([
                txt_nome,
                txt_descricao,
                chk_admin,
                ft.Divider(),
                ft.Text("Permissões de Módulos:", weight=ft.FontWeight.BOLD),
                *checkboxes_modulos
            ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO, height=500),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton("Criar", on_click=salvar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def editar_tipo(self, tipo_id):
        """Abre diálogo para editar tipo de conta"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT nome, descricao, is_admin FROM tipos_conta WHERE id = ?', (tipo_id,))
        tipo = cursor.fetchone()
        cursor.execute('SELECT modulo, permitido FROM permissoes WHERE tipo_conta_id = ?', (tipo_id,))
        perms = {p[0]: p[1] for p in cursor.fetchall()}
        conn.close()

        if not tipo:
            return

        nome, descricao, is_admin = tipo

        txt_nome = ft.TextField(label="Nome do Tipo *", value=nome, width=300)
        txt_descricao = ft.TextField(label="Descrição", value=descricao or "", width=300)
        chk_admin = ft.Checkbox(label="É administrador?", value=bool(is_admin))

        modulos = ['CRM - Gestão Comercial', 'Gestão de Compras', 'Recursos Humanos',
                   'Gestão Patrimonial', 'Gestão de Documentos', 'SMS - Segurança e Meio Ambiente']

        checkboxes_modulos = [ft.Checkbox(label=m, value=perms.get(m, 0) == 1) for m in modulos]

        def salvar(e):
            if not txt_nome.value:
                return

            conn = get_connection()
            cursor = conn.cursor()

            # Atualizar tipo
            cursor.execute('''
                UPDATE tipos_conta SET nome = ?, descricao = ?, is_admin = ? WHERE id = ?
            ''', (txt_nome.value, txt_descricao.value, 1 if chk_admin.value else 0, tipo_id))

            # Atualizar permissões
            cursor.execute('DELETE FROM permissoes WHERE tipo_conta_id = ?', (tipo_id,))
            for i, cb in enumerate(checkboxes_modulos):
                cursor.execute('''
                    INSERT INTO permissoes (tipo_conta_id, modulo, permitido)
                    VALUES (?, ?, ?)
                ''', (tipo_id, modulos[i], 1 if cb.value else 0))

            conn.commit()
            conn.close()

            dlg.open = False
            self.page.update()
            self.build_ui()
            self.mostrar_snackbar("Tipo de conta atualizado!")

        def fechar(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar: {nome}"),
            content=ft.Column([
                txt_nome,
                txt_descricao,
                chk_admin,
                ft.Divider(),
                ft.Text("Permissões de Módulos:", weight=ft.FontWeight.BOLD),
                *checkboxes_modulos
            ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO, height=500),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton("Salvar", on_click=salvar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def excluir_tipo(self, tipo_id):
        """Exclui um tipo de conta"""
        # Verificar se há usuários usando este tipo
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE tipo_conta_id = ?', (tipo_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            conn.close()
            self.mostrar_snackbar(f"Não é possível excluir: {count} usuário(s) usam este tipo!", erro=True)
            return

        cursor.execute('DELETE FROM permissoes WHERE tipo_conta_id = ?', (tipo_id,))
        cursor.execute('DELETE FROM tipos_conta WHERE id = ?', (tipo_id,))
        conn.commit()
        conn.close()

        self.build_ui()
        self.mostrar_snackbar("Tipo de conta excluído!")

    def mostrar_snackbar(self, mensagem, erro=False):
        """Mostra snackbar com mensagem"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensagem, color=COR_BRANCO),
            bgcolor=COR_ERRO if erro else COR_VERDE
        )
        self.page.snack_bar.open = True
        self.page.update()


def parse_args():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description='ERP Integrado - Renovo')
    parser.add_argument('--usuario', type=str, default='', help='Login do usuário para auto-login')
    parser.add_argument('--auto_login', type=str, default='', help='Se "true", faz login automático')
    args, unknown = parser.parse_known_args()
    return args


# Argumentos globais
ERP_ARGS = parse_args()


def main(page: ft.Page):
    """Função principal do aplicativo"""
    # Inicializar banco de dados
    init_database()

    def on_login_success(usuario, user_data):
        page.controls.clear()
        page.update()
        ERPIntegrado(page, usuario, user_data)

    # Verificar se deve fazer auto-login (voltando de um módulo)
    if ERP_ARGS.auto_login == "true" and ERP_ARGS.usuario:
        # Garantir que a janela esteja visível e maximizada
        page.window.visible = True
        page.window.minimized = False
        page.window.maximized = True
        page.update()

        # Buscar dados do usuário no banco
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, login, nome, cargo, is_admin, tipo_conta_id, ativo
            FROM usuarios WHERE login = ? AND ativo = 1
        """, (ERP_ARGS.usuario,))
        user_row = cursor.fetchone()
        conn.close()

        if user_row:
            user_data = {
                "id": user_row[0],
                "login": user_row[1],
                "nome": user_row[2],
                "cargo": user_row[3],
                "is_admin": bool(user_row[4]),
                "tipo_conta_id": user_row[5]
            }
            # Registrar log de retorno
            registrar_log(user_data["id"], user_row[1], "Retorno ao ERP (via módulo)", "ERP")
            # Ir direto para o ERP
            on_login_success(ERP_ARGS.usuario, user_data)
            return

    # Login normal
    TelaLogin(page, on_login_success)


if __name__ == "__main__":
    ft.app(target=main)
