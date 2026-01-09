"""
Constantes e funções utilitárias - Sistema de Gestão de RH
"""

import flet as ft
from datetime import datetime
import re

# Constantes de cores
COR_PRIMARIA = "#1a5276"
COR_SECUNDARIA = "#3498db"
COR_SUCESSO = "#27ae60"
COR_ALERTA = "#e67e22"
COR_ERRO = "#c0392b"
COR_FUNDO = "#f5f6fa"
COR_CINZA_CLARO = "#ecf0f1"

# Listas de opções
ESTADOS_BR = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO"
]

GRAUS_INSTRUCAO = [
    "Analfabeto", "Fundamental Incompleto", "Fundamental Completo",
    "Médio Incompleto", "Médio Completo", "Superior Incompleto",
    "Superior Completo", "Pós-Graduação", "Mestrado", "Doutorado"
]

ESTADOS_CIVIS = [
    "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)",
    "União Estável", "Separado(a)"
]

TIPOS_CONTA = ["Corrente", "Poupança", "Salário"]
FORMAS_PAGAMENTO = ["Depósito em Conta", "PIX", "Dinheiro", "Cheque"]
TIPOS_CONTRATO = ["CLT", "PJ", "Contrato de Experiência", "Temporário", "Estágio", "Jovem Aprendiz"]
PARENTESCOS = ["Filho(a)", "Cônjuge", "Pai", "Mãe", "Enteado(a)", "Menor sob Guarda"]
TIPOS_CNH = ["A", "B", "AB", "C", "D", "E", "ACC"]
TIPOS_DEFICIENCIA = ["Nenhuma", "Física", "Auditiva", "Visual", "Intelectual", "Múltipla", "Outros"]
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]


def criar_campo_texto(label: str, value: str = "", width: int = 200,
                       password: bool = False, multiline: bool = False,
                       hint_text: str = None, on_change=None,
                       read_only: bool = False, keyboard_type=None,
                       on_submit=None) -> ft.TextField:
    """Cria um campo de texto padronizado."""
    return ft.TextField(
        label=label,
        value=value,
        width=width,
        password=password,
        multiline=multiline,
        hint_text=hint_text,
        on_change=on_change,
        on_submit=on_submit,
        read_only=read_only,
        keyboard_type=keyboard_type,
        border_color=COR_SECUNDARIA,
        focused_border_color=COR_PRIMARIA,
        label_style=ft.TextStyle(color=COR_PRIMARIA),
        text_size=14,
    )


def criar_dropdown(label: str, options: list, value: str = None,
                   width: int = 200, on_change=None) -> ft.Dropdown:
    """Cria um dropdown padronizado."""
    if value and options and value not in options:
        value = None
    return ft.Dropdown(
        label=label,
        value=value,
        width=width,
        options=[ft.dropdown.Option(opt) for opt in options] if options else [],
        on_change=on_change,
        border_color=COR_SECUNDARIA,
        focused_border_color=COR_PRIMARIA,
        label_style=ft.TextStyle(color=COR_PRIMARIA),
    )


def criar_data_picker(label: str, value: str = None, on_change=None, width: int = 150) -> ft.TextField:
    """Cria um campo de data."""
    return ft.TextField(
        label=label,
        value=value if value else "",
        width=width,
        hint_text="DD/MM/AAAA",
        on_change=on_change,
        border_color=COR_SECUNDARIA,
        focused_border_color=COR_PRIMARIA,
        label_style=ft.TextStyle(color=COR_PRIMARIA),
    )


def criar_secao(titulo: str, conteudo: list) -> ft.Container:
    """Cria uma seção estilizada."""
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=COR_PRIMARIA,
                padding=10,
                border_radius=ft.border_radius.only(top_left=8, top_right=8),
            ),
            ft.Container(
                content=ft.Column(conteudo, spacing=10),
                padding=15,
                border=ft.border.all(1, COR_SECUNDARIA),
                border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            ),
        ], spacing=0),
        margin=ft.margin.only(bottom=15),
    )


def formatar_cpf(cpf: str) -> str:
    """Formata CPF para exibição."""
    if not cpf:
        return ""
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def validar_cpf(cpf: str) -> tuple:
    """
    Valida CPF incluindo dígitos verificadores.
    Retorna (True, None) se válido, ou (False, mensagem_erro) se inválido.
    """
    if not cpf:
        return False, "CPF não informado"

    # Remover caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)

    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        return False, "CPF deve ter 11 dígitos"

    # Rejeitar CPFs com todos os dígitos iguais (ex: 11111111111)
    if cpf == cpf[0] * 11:
        return False, "CPF inválido"

    # Validar primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False, "CPF inválido (dígito verificador incorreto)"

    # Validar segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if int(cpf[10]) != digito2:
        return False, "CPF inválido (dígito verificador incorreto)"

    return True, None


def formatar_data_br(data_str: str) -> str:
    """Converte data de YYYY-MM-DD para DD/MM/YYYY."""
    if not data_str:
        return ""
    try:
        data = datetime.strptime(str(data_str), '%Y-%m-%d')
        return data.strftime('%d/%m/%Y')
    except:
        return str(data_str)


def formatar_data_db(data_str: str) -> str:
    """Converte data de DD/MM/YYYY para YYYY-MM-DD."""
    if not data_str:
        return None
    try:
        data = datetime.strptime(data_str.strip(), '%d/%m/%Y')
        return data.strftime('%Y-%m-%d')
    except:
        return None


def formatar_moeda(valor) -> str:
    """Formata valor para moeda brasileira."""
    if valor is None:
        return ""
    try:
        return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return str(valor)


def criar_campo_view(label: str, valor, largura: int = 200) -> ft.Container:
    """Cria um campo apenas para visualização."""
    return ft.Container(
        content=ft.Column([
            ft.Text(label, size=11, color=COR_PRIMARIA, weight=ft.FontWeight.BOLD),
            ft.Text(str(valor) if valor else "-", size=13),
        ], spacing=2),
        width=largura,
        padding=5,
    )
