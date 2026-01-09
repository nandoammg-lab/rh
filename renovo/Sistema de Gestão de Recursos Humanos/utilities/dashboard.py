"""
Módulo de Dashboard - Sistema de Gestão de RH
RENOVO Montagens Industriais

Contém funções para obter estatísticas e dados para visualização em gráficos.
"""

import flet as ft
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from utilities import database as db
from utilities.constantes import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_SUCESSO, COR_ALERTA, COR_ERRO, COR_FUNDO,
    GRAUS_INSTRUCAO, ESTADOS_CIVIS, TIPOS_CONTRATO
)

# Meses em português
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}


def obter_nome_mes(mes: int = None) -> str:
    """Retorna o nome do mês em português."""
    if mes is None:
        mes = datetime.now().month
    return MESES_PT.get(mes, '')


# =============================================================================
# FUNÇÕES DE CONSULTA DE DADOS PARA DASHBOARDS
# =============================================================================

def obter_estatisticas_gerais() -> Dict[str, Any]:
    """Obtém estatísticas gerais dos colaboradores ativos."""
    conn = db.get_connection()
    cursor = conn.cursor()

    stats = {}

    # Total de colaboradores ativos
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO'")
    stats['total_ativos'] = cursor.fetchone()[0]

    # Total de empresas ativas
    cursor.execute("SELECT COUNT(*) FROM empresas WHERE ativa = 1")
    stats['total_empresas'] = cursor.fetchone()[0]

    # Contratos de experiência vencendo nos próximos 30 dias
    data_limite = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(*) FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        WHERE ce.status = 'VIGENTE' AND c.status = 'ATIVO'
        AND (ce.data_fim_prorrogacao <= ? OR (ce.data_fim_prorrogacao IS NULL AND ce.data_fim_inicial <= ?))
    """, (data_limite, data_limite))
    stats['contratos_vencendo'] = cursor.fetchone()[0]

    # Férias vencendo nos próximos 90 dias
    data_limite_ferias = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(*) FROM ferias f
        JOIN colaboradores c ON f.colaborador_id = c.id
        WHERE f.status = 'PENDENTE' AND c.status = 'ATIVO'
        AND f.periodo_concessivo_limite <= ?
    """, (data_limite_ferias,))
    stats['ferias_vencendo'] = cursor.fetchone()[0]

    # Aniversariantes do mês
    mes_atual = datetime.now().month
    cursor.execute("""
        SELECT COUNT(*) FROM colaboradores
        WHERE status = 'ATIVO' AND strftime('%m', data_nascimento) = ?
    """, (f'{mes_atual:02d}',))
    stats['aniversariantes_mes'] = cursor.fetchone()[0]

    # Colaboradores em férias atualmente
    hoje = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(DISTINCT c.id) FROM colaboradores c
        JOIN ferias f ON c.id = f.colaborador_id
        JOIN periodos_ferias pf ON f.id = pf.ferias_id
        WHERE c.status = 'ATIVO' AND pf.data_inicio <= ? AND pf.data_fim >= ?
    """, (hoje, hoje))
    stats['em_ferias'] = cursor.fetchone()[0]

    # Média salarial
    cursor.execute("SELECT AVG(salario) FROM colaboradores WHERE status = 'ATIVO' AND salario > 0")
    media = cursor.fetchone()[0]
    stats['media_salarial'] = media if media else 0

    # Total na folha (soma de salários)
    cursor.execute("SELECT SUM(salario) FROM colaboradores WHERE status = 'ATIVO' AND salario > 0")
    total = cursor.fetchone()[0]
    stats['total_folha'] = total if total else 0

    conn.close()
    return stats


def obter_colaboradores_por_empresa() -> List[Dict]:
    """Obtém contagem de colaboradores ativos por empresa."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.razao_social as empresa, COUNT(c.id) as quantidade
        FROM colaboradores c
        JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO'
        GROUP BY e.id, e.razao_social
        ORDER BY quantidade DESC
    """)

    resultado = [{'empresa': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_colaboradores_por_localizacao() -> List[Dict]:
    """Obtém contagem de colaboradores ativos por localização atual."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.local_nome, l.cidade, l.uf, COUNT(DISTINCT c.id) as quantidade
        FROM colaboradores c
        JOIN localizacoes l ON c.id = l.colaborador_id
        WHERE c.status = 'ATIVO' AND l.data_fim IS NULL
        GROUP BY l.local_nome, l.cidade, l.uf
        ORDER BY quantidade DESC
    """)

    resultado = []
    for row in cursor.fetchall():
        local = row[0]
        if row[1]:
            local += f" - {row[1]}"
        if row[2]:
            local += f"/{row[2]}"
        resultado.append({'local': local, 'quantidade': row[3]})

    conn.close()
    return resultado


def obter_colaboradores_por_funcao() -> List[Dict]:
    """Obtém contagem de colaboradores ativos por função."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT funcao, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND funcao IS NOT NULL AND funcao != ''
        GROUP BY funcao
        ORDER BY quantidade DESC
        LIMIT 15
    """)

    resultado = [{'funcao': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_colaboradores_por_departamento() -> List[Dict]:
    """Obtém contagem de colaboradores ativos por departamento."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT departamento, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND departamento IS NOT NULL AND departamento != ''
        GROUP BY departamento
        ORDER BY quantidade DESC
    """)

    resultado = [{'departamento': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_distribuicao_escolaridade() -> List[Dict]:
    """Obtém distribuição de escolaridade dos colaboradores ativos."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT grau_instrucao, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND grau_instrucao IS NOT NULL AND grau_instrucao != ''
        GROUP BY grau_instrucao
        ORDER BY quantidade DESC
    """)

    resultado = [{'escolaridade': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_distribuicao_estado_civil() -> List[Dict]:
    """Obtém distribuição de estado civil dos colaboradores ativos."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT estado_civil, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND estado_civil IS NOT NULL AND estado_civil != ''
        GROUP BY estado_civil
        ORDER BY quantidade DESC
    """)

    resultado = [{'estado_civil': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_distribuicao_sexo() -> List[Dict]:
    """Obtém distribuição por sexo dos colaboradores ativos."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sexo, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND sexo IS NOT NULL AND sexo != ''
        GROUP BY sexo
        ORDER BY quantidade DESC
    """)

    resultado = [{'sexo': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_distribuicao_idade() -> List[Dict]:
    """Obtém distribuição de colaboradores ativos por faixa etária."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data_nascimento FROM colaboradores
        WHERE status = 'ATIVO' AND data_nascimento IS NOT NULL
    """)

    faixas = {
        '18-25': 0,
        '26-35': 0,
        '36-45': 0,
        '46-55': 0,
        '56+': 0
    }

    hoje = date.today()
    for row in cursor.fetchall():
        try:
            nascimento = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
            idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))

            if idade < 26:
                faixas['18-25'] += 1
            elif idade < 36:
                faixas['26-35'] += 1
            elif idade < 46:
                faixas['36-45'] += 1
            elif idade < 56:
                faixas['46-55'] += 1
            else:
                faixas['56+'] += 1
        except:
            pass

    conn.close()
    resultado = [{'faixa': k, 'quantidade': v} for k, v in faixas.items() if v > 0]
    return resultado


def obter_distribuicao_tipo_contrato() -> List[Dict]:
    """Obtém distribuição de colaboradores ativos por tipo de contrato."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo_contrato, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND tipo_contrato IS NOT NULL AND tipo_contrato != ''
        GROUP BY tipo_contrato
        ORDER BY quantidade DESC
    """)

    resultado = [{'tipo': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_admissoes_por_mes(meses: int = 12) -> List[Dict]:
    """Obtém quantidade de admissões nos últimos N meses (colaboradores ativos)."""
    conn = db.get_connection()
    cursor = conn.cursor()

    data_inicio = (datetime.now() - timedelta(days=meses * 30)).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT strftime('%Y-%m', data_admissao) as mes, COUNT(*) as quantidade
        FROM colaboradores
        WHERE status = 'ATIVO' AND data_admissao >= ?
        GROUP BY mes
        ORDER BY mes
    """, (data_inicio,))

    resultado = [{'mes': row[0], 'quantidade': row[1]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_contratos_vencendo(dias: int = 30) -> List[Dict]:
    """Obtém contratos de experiência vencendo nos próximos N dias."""
    conn = db.get_connection()
    cursor = conn.cursor()

    hoje = datetime.now().strftime('%Y-%m-%d')
    data_limite = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT c.nome_completo, c.funcao, e.razao_social as empresa,
               ce.data_fim_inicial, ce.data_fim_prorrogacao,
               CASE WHEN ce.data_fim_prorrogacao IS NOT NULL
                    THEN ce.data_fim_prorrogacao
                    ELSE ce.data_fim_inicial END as data_vencimento
        FROM contratos_experiencia ce
        JOIN colaboradores c ON ce.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE ce.status = 'VIGENTE' AND c.status = 'ATIVO'
        AND (
            (ce.data_fim_prorrogacao IS NOT NULL AND ce.data_fim_prorrogacao BETWEEN ? AND ?)
            OR (ce.data_fim_prorrogacao IS NULL AND ce.data_fim_inicial BETWEEN ? AND ?)
        )
        ORDER BY data_vencimento
    """, (hoje, data_limite, hoje, data_limite))

    resultado = []
    for row in cursor.fetchall():
        data_venc = row[5] or row[4] or row[3]
        dias_restantes = (datetime.strptime(str(data_venc), '%Y-%m-%d') - datetime.now()).days
        resultado.append({
            'nome': row[0],
            'funcao': row[1] or '-',
            'empresa': row[2] or '-',
            'data_vencimento': data_venc,
            'dias_restantes': dias_restantes
        })

    conn.close()
    return resultado


def obter_ferias_vencendo(dias: int = 90) -> List[Dict]:
    """Obtém períodos de férias vencendo nos próximos N dias."""
    conn = db.get_connection()
    cursor = conn.cursor()

    hoje = datetime.now().strftime('%Y-%m-%d')
    data_limite = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT c.nome_completo, c.funcao, e.razao_social as empresa,
               f.periodo_concessivo_limite, f.dias_direito, f.dias_gozados
        FROM ferias f
        JOIN colaboradores c ON f.colaborador_id = c.id
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE f.status = 'PENDENTE' AND c.status = 'ATIVO'
        AND f.periodo_concessivo_limite BETWEEN ? AND ?
        ORDER BY f.periodo_concessivo_limite
    """, (hoje, data_limite))

    resultado = []
    for row in cursor.fetchall():
        dias_restantes = (datetime.strptime(str(row[3]), '%Y-%m-%d') - datetime.now()).days
        resultado.append({
            'nome': row[0],
            'funcao': row[1] or '-',
            'empresa': row[2] or '-',
            'limite': row[3],
            'dias_direito': row[4],
            'dias_gozados': row[5],
            'dias_restantes': dias_restantes
        })

    conn.close()
    return resultado


def obter_aniversariantes_mes(mes: int = None) -> List[Dict]:
    """Obtém aniversariantes do mês especificado (ou mês atual)."""
    if mes is None:
        mes = datetime.now().month

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.nome_completo, c.data_nascimento, c.funcao, e.razao_social as empresa
        FROM colaboradores c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        WHERE c.status = 'ATIVO' AND strftime('%m', c.data_nascimento) = ?
        ORDER BY strftime('%d', c.data_nascimento)
    """, (f'{mes:02d}',))

    resultado = []
    for row in cursor.fetchall():
        try:
            nascimento = datetime.strptime(str(row[1]), '%Y-%m-%d')
            idade = datetime.now().year - nascimento.year
            resultado.append({
                'nome': row[0],
                'dia': nascimento.day,
                'idade': idade,
                'funcao': row[2] or '-',
                'empresa': row[3] or '-'
            })
        except:
            pass

    conn.close()
    return resultado


def obter_utilizacao_beneficios() -> Dict[str, int]:
    """Obtém contagem de colaboradores ativos que utilizam cada benefício."""
    conn = db.get_connection()
    cursor = conn.cursor()

    beneficios = {}

    # Vale Transporte
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND vale_transporte = 1")
    beneficios['Vale Transporte'] = cursor.fetchone()[0]

    # Vale Refeição
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND vale_refeicao = 1")
    beneficios['Vale Refeição'] = cursor.fetchone()[0]

    # Vale Alimentação
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND vale_alimentacao = 1")
    beneficios['Vale Alimentação'] = cursor.fetchone()[0]

    # Assistência Médica
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND assistencia_medica = 1")
    beneficios['Assist. Médica'] = cursor.fetchone()[0]

    # Assistência Odontológica
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND assistencia_odontologica = 1")
    beneficios['Assist. Odonto'] = cursor.fetchone()[0]

    # Seguro de Vida
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO' AND seguro_vida = 1")
    beneficios['Seguro de Vida'] = cursor.fetchone()[0]

    conn.close()
    return beneficios


def obter_faixas_salariais() -> List[Dict]:
    """Obtém distribuição de colaboradores ativos por faixa salarial."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT salario FROM colaboradores
        WHERE status = 'ATIVO' AND salario IS NOT NULL AND salario > 0
    """)

    faixas = {
        'Até R$ 2.000': 0,
        'R$ 2.001 - 3.500': 0,
        'R$ 3.501 - 5.000': 0,
        'R$ 5.001 - 8.000': 0,
        'R$ 8.001 - 12.000': 0,
        'Acima de R$ 12.000': 0
    }

    for row in cursor.fetchall():
        salario = float(row[0])
        if salario <= 2000:
            faixas['Até R$ 2.000'] += 1
        elif salario <= 3500:
            faixas['R$ 2.001 - 3.500'] += 1
        elif salario <= 5000:
            faixas['R$ 3.501 - 5.000'] += 1
        elif salario <= 8000:
            faixas['R$ 5.001 - 8.000'] += 1
        elif salario <= 12000:
            faixas['R$ 8.001 - 12.000'] += 1
        else:
            faixas['Acima de R$ 12.000'] += 1

    conn.close()
    resultado = [{'faixa': k, 'quantidade': v} for k, v in faixas.items() if v > 0]
    return resultado


def obter_documentos_pendentes() -> Dict[str, Any]:
    """Obtém estatísticas de documentos pendentes dos colaboradores ativos."""
    conn = db.get_connection()
    cursor = conn.cursor()

    # Total de colaboradores ativos
    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO'")
    total = cursor.fetchone()[0]

    # Colaboradores com documentos completos (todos obrigatórios)
    # Simplificado: contar colaboradores que têm pelo menos 5 documentos
    cursor.execute("""
        SELECT c.id, COUNT(d.id) as docs
        FROM colaboradores c
        LEFT JOIN documentos_colaborador d ON c.id = d.colaborador_id
        WHERE c.status = 'ATIVO'
        GROUP BY c.id
        HAVING docs >= 5
    """)
    completos = len(cursor.fetchall())

    conn.close()

    return {
        'total': total,
        'completos': completos,
        'pendentes': total - completos,
        'percentual_completo': round((completos / total * 100) if total > 0 else 0, 1)
    }


# =============================================================================
# CORES PARA GRÁFICOS
# =============================================================================

CORES_GRAFICO = [
    "#1a5276",  # Azul escuro (primária)
    "#3498db",  # Azul claro (secundária)
    "#27ae60",  # Verde
    "#e67e22",  # Laranja
    "#9b59b6",  # Roxo
    "#e74c3c",  # Vermelho
    "#1abc9c",  # Verde água
    "#f39c12",  # Amarelo
    "#34495e",  # Cinza escuro
    "#16a085",  # Verde escuro
    "#8e44ad",  # Roxo escuro
    "#2980b9",  # Azul médio
    "#d35400",  # Laranja escuro
    "#c0392b",  # Vermelho escuro
    "#7f8c8d",  # Cinza
]


def obter_cor(indice: int) -> str:
    """Retorna uma cor do array de cores para gráficos."""
    return CORES_GRAFICO[indice % len(CORES_GRAFICO)]


# =============================================================================
# COMPONENTES DE INTERFACE DO DASHBOARD
# =============================================================================

class DashboardView:
    """Classe para construir a interface do Dashboard com abas."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.aba_atual = 0

    def build(self) -> ft.Container:
        """Constrói a view completa do dashboard."""

        # Abas do dashboard
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(text="Visão Geral", icon=ft.Icons.DASHBOARD),
                ft.Tab(text="Quadro de Pessoal", icon=ft.Icons.PEOPLE),
                ft.Tab(text="Contratos & Férias", icon=ft.Icons.EVENT_NOTE),
                ft.Tab(text="Demografia", icon=ft.Icons.PIE_CHART),
                ft.Tab(text="Benefícios", icon=ft.Icons.CARD_GIFTCARD),
            ],
            expand=False,
        )

        # Conteúdo das abas
        self.conteudo_aba = ft.Container(expand=True)
        self._carregar_aba(0)

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, size=28, color=COR_PRIMARIA),
                ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ], alignment=ft.MainAxisAlignment.START),
            self.tabs,
            self.conteudo_aba,
        ], expand=True, spacing=5, scroll=ft.ScrollMode.AUTO)

    def _on_tab_change(self, e):
        """Callback quando muda de aba."""
        self.aba_atual = e.control.selected_index
        self._carregar_aba(self.aba_atual)
        self.page.update()

    def _carregar_aba(self, indice: int):
        """Carrega o conteúdo da aba selecionada."""
        if indice == 0:
            self.conteudo_aba.content = self._build_visao_geral()
        elif indice == 1:
            self.conteudo_aba.content = self._build_quadro_pessoal()
        elif indice == 2:
            self.conteudo_aba.content = self._build_contratos_ferias()
        elif indice == 3:
            self.conteudo_aba.content = self._build_demografia()
        elif indice == 4:
            self.conteudo_aba.content = self._build_beneficios()

    def _criar_card_kpi(self, titulo: str, valor: str, icone, cor: str, subtitulo: str = None) -> ft.Container:
        """Cria um card de KPI estilizado."""
        conteudo = [
            ft.Row([
                ft.Container(
                    content=ft.Icon(icone, size=24, color="white"),
                    bgcolor=cor,
                    padding=10,
                    border_radius=8,
                ),
                ft.Column([
                    ft.Text(titulo, size=11, color=ft.Colors.GREY_600),
                    ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ], spacing=2, expand=True),
            ], spacing=12),
        ]

        if subtitulo:
            conteudo.append(
                ft.Text(subtitulo, size=10, color=ft.Colors.GREY_500, italic=True)
            )

        return ft.Container(
            content=ft.Column(conteudo, spacing=5),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            width=200,
        )

    def _criar_grafico_barras(self, dados: List[Dict], campo_label: str, campo_valor: str,
                               titulo: str, largura: int = 500, altura: int = 300) -> ft.Container:
        """Cria um gráfico de barras horizontal com tooltips."""
        if not dados:
            return ft.Container(
                content=ft.Text("Sem dados disponíveis", color=ft.Colors.GREY_500),
                padding=20,
            )

        max_valor = max(d[campo_valor] for d in dados) if dados else 1

        barras = []
        for i, item in enumerate(dados[:10]):  # Limitar a 10 itens
            label = str(item[campo_label])[:25]
            if len(str(item[campo_label])) > 25:
                label += "..."
            valor = item[campo_valor]
            percentual = (valor / max_valor) * 100 if max_valor > 0 else 0
            cor = obter_cor(i)

            barra = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(label, size=11, color=ft.Colors.GREY_700),
                        width=120,
                    ),
                    ft.Container(
                        content=ft.Stack([
                            ft.Container(
                                bgcolor="#e8e8e8",
                                height=20,
                                width=largura - 200,
                                border_radius=4,
                            ),
                            ft.Container(
                                bgcolor=cor,
                                height=20,
                                width=max(4, (largura - 200) * percentual / 100),
                                border_radius=4,
                            ),
                        ]),
                        expand=True,
                    ),
                    ft.Text(str(valor), size=12, weight=ft.FontWeight.BOLD, color=cor, width=40),
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=4),
                tooltip=f"{item[campo_label]}: {valor}",
            )
            barras.append(barra)

        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Column(barras, spacing=2, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            width=largura,
            height=altura,
        )

    def _criar_grafico_pizza(self, dados: List[Dict], campo_label: str, campo_valor: str,
                              titulo: str, tamanho: int = 280) -> ft.Container:
        """Cria um gráfico de pizza com legenda."""
        if not dados:
            return ft.Container(
                content=ft.Text("Sem dados disponíveis", color=ft.Colors.GREY_500),
                padding=20,
            )

        total = sum(d[campo_valor] for d in dados)
        if total == 0:
            return ft.Container(
                content=ft.Text("Sem dados disponíveis", color=ft.Colors.GREY_500),
                padding=20,
            )

        # Criar seções do gráfico de pizza
        sections = []
        for i, item in enumerate(dados[:8]):  # Limitar a 8 itens
            valor = item[campo_valor]
            percentual = (valor / total) * 100
            cor = obter_cor(i)

            sections.append(
                ft.PieChartSection(
                    value=percentual,
                    color=cor,
                    radius=40,
                    title=f"{percentual:.0f}%",
                    title_style=ft.TextStyle(
                        size=9, color="white", weight=ft.FontWeight.BOLD
                    ),
                )
            )

        # Criar legenda
        legenda_items = []
        for i, item in enumerate(dados[:8]):
            cor = obter_cor(i)
            valor = item[campo_valor]
            percentual = (valor / total) * 100

            legenda_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            bgcolor=cor,
                            width=12, height=12,
                            border_radius=2,
                        ),
                        ft.Text(
                            f"{item[campo_label][:15]}",
                            size=10, color=ft.Colors.GREY_700,
                            expand=True,
                        ),
                        ft.Text(
                            f"{valor}",
                            size=10, weight=ft.FontWeight.BOLD, color=cor,
                        ),
                    ], spacing=5),
                    tooltip=f"{item[campo_label]}: {valor} ({percentual:.1f}%)",
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Row([
                    ft.Container(
                        content=ft.PieChart(
                            sections=sections,
                            width=100,
                            height=100,
                            center_space_radius=15,
                            sections_space=1,
                        ),
                        width=100,
                        height=100,
                    ),
                    ft.Container(
                        content=ft.Column(legenda_items, spacing=4, scroll=ft.ScrollMode.AUTO),
                        expand=True,
                        padding=ft.padding.only(left=10),
                    ),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=10),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            width=tamanho,
            height=220,
        )

    def _criar_lista_alertas(self, titulo: str, items: List[Dict], tipo: str,
                              altura: int = 200) -> ft.Container:
        """Cria uma lista de alertas/items com scroll."""
        if not items:
            conteudo = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=40, color=COR_SUCESSO),
                    ft.Text("Nenhum item pendente", color=ft.Colors.GREY_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
                alignment=ft.alignment.center,
            )
        else:
            lista = []
            for item in items[:10]:
                if tipo == "contrato":
                    dias = item['dias_restantes']
                    cor_alerta = COR_ERRO if dias <= 5 else COR_ALERTA if dias <= 15 else COR_SECUNDARIA
                    lista.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(f"{dias}d", size=10, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=cor_alerta,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                                ft.Column([
                                    ft.Text(item['nome'][:25], size=11, weight=ft.FontWeight.W_500),
                                    ft.Text(item['funcao'][:20], size=9, color=ft.Colors.GREY_600),
                                ], spacing=0, expand=True),
                            ], spacing=8),
                            padding=ft.padding.symmetric(vertical=4),
                            tooltip=f"{item['nome']}\n{item['funcao']}\nVence em {dias} dias",
                        )
                    )
                elif tipo == "ferias":
                    dias = item['dias_restantes']
                    cor_alerta = COR_ERRO if dias <= 30 else COR_ALERTA if dias <= 60 else COR_SECUNDARIA
                    lista.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(f"{dias}d", size=10, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=cor_alerta,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                                ft.Column([
                                    ft.Text(item['nome'][:25], size=11, weight=ft.FontWeight.W_500),
                                    ft.Text(f"{item['dias_direito'] - item['dias_gozados']} dias restantes",
                                           size=9, color=ft.Colors.GREY_600),
                                ], spacing=0, expand=True),
                            ], spacing=8),
                            padding=ft.padding.symmetric(vertical=4),
                            tooltip=f"{item['nome']}\n{item['funcao']}\nLimite: {dias} dias",
                        )
                    )
                elif tipo == "aniversario":
                    lista.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(f"{item['dia']:02d}", size=10, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=COR_SECUNDARIA,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                                ft.Column([
                                    ft.Text(item['nome'][:25], size=11, weight=ft.FontWeight.W_500),
                                    ft.Text(f"{item['idade']} anos", size=9, color=ft.Colors.GREY_600),
                                ], spacing=0, expand=True),
                            ], spacing=8),
                            padding=ft.padding.symmetric(vertical=4),
                            tooltip=f"{item['nome']}\n{item['funcao']}\n{item['empresa']}",
                        )
                    )

            conteudo = ft.Column(lista, spacing=4, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(str(len(items)), size=12, color="white", weight=ft.FontWeight.BOLD),
                        bgcolor=COR_ALERTA if items else COR_SUCESSO,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=10,
                    ),
                ]),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=conteudo, expand=True),
            ], spacing=10),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            height=altura,
            expand=True,
        )

    # =========================================================================
    # ABAS DO DASHBOARD
    # =========================================================================

    def _build_visao_geral(self) -> ft.Container:
        """Constrói a aba de Visão Geral."""
        stats = obter_estatisticas_gerais()
        contratos_venc = obter_contratos_vencendo(30)
        ferias_venc = obter_ferias_vencendo(90)
        aniversariantes = obter_aniversariantes_mes()

        # Cards de KPIs
        kpis = ft.Row([
            self._criar_card_kpi(
                "Colaboradores Ativos",
                str(stats['total_ativos']),
                ft.Icons.PEOPLE,
                COR_PRIMARIA,
            ),
            self._criar_card_kpi(
                "Empresas",
                str(stats['total_empresas']),
                ft.Icons.BUSINESS,
                COR_SECUNDARIA,
            ),
            self._criar_card_kpi(
                "Contratos Vencendo",
                str(stats['contratos_vencendo']),
                ft.Icons.SCHEDULE,
                COR_ALERTA if stats['contratos_vencendo'] > 0 else COR_SUCESSO,
                "Próximos 30 dias",
            ),
            self._criar_card_kpi(
                "Férias Vencendo",
                str(stats['ferias_vencendo']),
                ft.Icons.BEACH_ACCESS,
                COR_ALERTA if stats['ferias_vencendo'] > 0 else COR_SUCESSO,
                "Próximos 90 dias",
            ),
            self._criar_card_kpi(
                "Em Férias",
                str(stats['em_ferias']),
                ft.Icons.FLIGHT_TAKEOFF,
                COR_SECUNDARIA,
            ),
            self._criar_card_kpi(
                "Aniversariantes",
                str(stats['aniversariantes_mes']),
                ft.Icons.CAKE,
                "#9b59b6",
                "Este mês",
            ),
        ], wrap=True, spacing=15)

        # Cards financeiros
        financeiro = ft.Row([
            self._criar_card_kpi(
                "Média Salarial",
                f"R$ {stats['media_salarial']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                ft.Icons.ATTACH_MONEY,
                COR_SUCESSO,
            ),
            self._criar_card_kpi(
                "Total em Folha",
                f"R$ {stats['total_folha']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                ft.Icons.ACCOUNT_BALANCE,
                COR_PRIMARIA,
            ),
        ], spacing=15)

        # Listas de alertas
        alertas = ft.Row([
            self._criar_lista_alertas("Contratos Vencendo (30 dias)", contratos_venc, "contrato", 250),
            self._criar_lista_alertas("Férias Vencendo (90 dias)", ferias_venc, "ferias", 250),
            self._criar_lista_alertas(f"Aniversariantes - {obter_nome_mes()}", aniversariantes, "aniversario", 250),
        ], spacing=15, expand=True)

        return ft.Column([
            kpis,
            ft.Container(height=10),
            financeiro,
            ft.Container(height=15),
            alertas,
        ], spacing=10)

    def _build_quadro_pessoal(self) -> ft.Container:
        """Constrói a aba de Quadro de Pessoal."""
        por_empresa = obter_colaboradores_por_empresa()
        por_local = obter_colaboradores_por_localizacao()
        por_funcao = obter_colaboradores_por_funcao()
        por_departamento = obter_colaboradores_por_departamento()

        # Linha 1: Empresa e Localização
        linha1 = ft.Row([
            self._criar_grafico_barras(por_empresa, 'empresa', 'quantidade',
                                        "Colaboradores por Empresa", 450, 320),
            self._criar_grafico_barras(por_local, 'local', 'quantidade',
                                        "Colaboradores por Localização", 450, 320),
        ], spacing=15, wrap=True)

        # Linha 2: Função e Departamento
        linha2 = ft.Row([
            self._criar_grafico_barras(por_funcao, 'funcao', 'quantidade',
                                        "Top 15 Funções", 450, 320),
            self._criar_grafico_barras(por_departamento, 'departamento', 'quantidade',
                                        "Colaboradores por Departamento", 450, 320),
        ], spacing=15, wrap=True)

        return ft.Column([
            linha1,
            ft.Container(height=15),
            linha2,
        ], spacing=10)

    def _build_contratos_ferias(self) -> ft.Container:
        """Constrói a aba de Contratos & Férias."""
        por_tipo_contrato = obter_distribuicao_tipo_contrato()
        admissoes = obter_admissoes_por_mes(12)

        # Gráficos: Tipo de contrato e Admissões
        linha1 = ft.Row([
            self._criar_grafico_pizza(por_tipo_contrato, 'tipo', 'quantidade',
                                       "Distribuição por Tipo de Contrato", 320),
            self._criar_grafico_barras(admissoes, 'mes', 'quantidade',
                                        "Admissões nos Últimos 12 Meses", 550, 320),
        ], spacing=15, wrap=True)

        return ft.Column([
            linha1,
        ], spacing=10)

    def _build_demografia(self) -> ft.Container:
        """Constrói a aba de Demografia."""
        por_idade = obter_distribuicao_idade()
        por_escolaridade = obter_distribuicao_escolaridade()
        por_estado_civil = obter_distribuicao_estado_civil()
        por_sexo = obter_distribuicao_sexo()

        # Linha 1: Gráficos de pizza
        linha1 = ft.Row([
            self._criar_grafico_pizza(por_sexo, 'sexo', 'quantidade',
                                       "Distribuição por Sexo", 320),
            self._criar_grafico_pizza(por_estado_civil, 'estado_civil', 'quantidade',
                                       "Estado Civil", 320),
            self._criar_grafico_pizza(por_idade, 'faixa', 'quantidade',
                                       "Faixa Etária", 320),
        ], spacing=15, wrap=True)

        # Linha 2: Escolaridade
        linha2 = ft.Row([
            self._criar_grafico_barras(por_escolaridade, 'escolaridade', 'quantidade',
                                        "Distribuição por Escolaridade", 600, 300),
        ], spacing=15)

        return ft.Column([
            linha1,
            ft.Container(height=15),
            linha2,
        ], spacing=10)

    def _build_beneficios(self) -> ft.Container:
        """Constrói a aba de Benefícios."""
        beneficios = obter_utilizacao_beneficios()
        faixas_salariais = obter_faixas_salariais()
        stats = obter_estatisticas_gerais()
        total_ativos = stats['total_ativos']

        # Converter benefícios para lista
        lista_beneficios = [{'beneficio': k, 'quantidade': v} for k, v in beneficios.items()]

        # Criar barras de progresso para benefícios
        beneficios_items = []
        for item in lista_beneficios:
            percentual = (item['quantidade'] / total_ativos * 100) if total_ativos > 0 else 0
            cor = COR_SUCESSO if percentual > 50 else COR_ALERTA if percentual > 25 else COR_SECUNDARIA

            beneficios_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(item['beneficio'], size=12, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            ft.Text(f"{item['quantidade']} ({percentual:.0f}%)", size=12, color=cor),
                        ]),
                        ft.ProgressBar(
                            value=percentual / 100,
                            color=cor,
                            bgcolor="#e8e8e8",
                            height=8,
                        ),
                    ], spacing=5),
                    padding=ft.padding.symmetric(vertical=8),
                    tooltip=f"{item['beneficio']}: {item['quantidade']} colaboradores ({percentual:.1f}%)",
                )
            )

        card_beneficios = ft.Container(
            content=ft.Column([
                ft.Text("Utilização de Benefícios", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Text(f"Base: {total_ativos} colaboradores ativos", size=10, color=ft.Colors.GREY_600),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Column(beneficios_items, spacing=0),
            ], spacing=10),
            bgcolor="white",
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            width=450,
        )

        # Linha 1: Benefícios e Faixas Salariais
        linha1 = ft.Row([
            card_beneficios,
            self._criar_grafico_barras(faixas_salariais, 'faixa', 'quantidade',
                                        "Distribuição por Faixa Salarial", 450, 350),
        ], spacing=15, wrap=True)

        # Cards de resumo financeiro
        resumo = ft.Row([
            self._criar_card_kpi(
                "Média Salarial",
                f"R$ {stats['media_salarial']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                ft.Icons.TRENDING_UP,
                COR_SUCESSO,
            ),
            self._criar_card_kpi(
                "Total Folha Mensal",
                f"R$ {stats['total_folha']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                ft.Icons.ACCOUNT_BALANCE_WALLET,
                COR_PRIMARIA,
            ),
            self._criar_card_kpi(
                "Com VT",
                str(beneficios.get('Vale Transporte', 0)),
                ft.Icons.DIRECTIONS_BUS,
                COR_SECUNDARIA,
                f"{(beneficios.get('Vale Transporte', 0) / total_ativos * 100):.0f}% do total" if total_ativos > 0 else "0%",
            ),
            self._criar_card_kpi(
                "Com Plano de Saúde",
                str(beneficios.get('Assist. Médica', 0)),
                ft.Icons.LOCAL_HOSPITAL,
                "#9b59b6",
                f"{(beneficios.get('Assist. Médica', 0) / total_ativos * 100):.0f}% do total" if total_ativos > 0 else "0%",
            ),
        ], wrap=True, spacing=15)

        return ft.Column([
            resumo,
            ft.Container(height=15),
            linha1,
        ], spacing=10)


# =============================================================================
# FUNÇÕES DE CONSULTA PARA ANÁLISE INDIVIDUAL DE COLABORADOR
# =============================================================================

def obter_historico_localizacoes(colaborador_id: int) -> List[Dict]:
    """Obtém o histórico de localizações de um colaborador com tempo em cada local."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT local_nome, cidade, uf, data_inicio, data_fim, observacoes
        FROM localizacoes
        WHERE colaborador_id = ?
        ORDER BY data_inicio DESC
    """, (colaborador_id,))

    resultado = []
    hoje = date.today()

    for row in cursor.fetchall():
        data_inicio = datetime.strptime(str(row[3]), '%Y-%m-%d').date() if row[3] else None
        data_fim = datetime.strptime(str(row[4]), '%Y-%m-%d').date() if row[4] else None

        if data_inicio:
            fim = data_fim if data_fim else hoje
            dias = (fim - data_inicio).days
            # Se foi e voltou no mesmo dia, conta como 1 dia
            if dias == 0:
                dias = 1
            meses = dias // 30
            dias_resto = dias % 30

            if meses > 0:
                tempo = f"{meses} mês(es)" + (f" e {dias_resto} dia(s)" if dias_resto > 0 else "")
            else:
                tempo = f"{dias} dia(s)"
        else:
            tempo = "-"
            dias = 0

        local = row[0]
        if row[1]:
            local += f" - {row[1]}"
        if row[2]:
            local += f"/{row[2]}"

        resultado.append({
            'local': local,
            'local_nome': row[0],
            'cidade': row[1],
            'uf': row[2],
            'data_inicio': row[3],
            'data_fim': row[4],
            'observacoes': row[5],
            'tempo': tempo,
            'dias': dias,
            'atual': data_fim is None
        })

    conn.close()
    return resultado


def obter_historico_ferias(colaborador_id: int) -> List[Dict]:
    """Obtém o histórico de férias de um colaborador."""
    # Sincronizar dados de férias antes de exibir (garante consistência)
    db.sincronizar_ferias_colaborador(colaborador_id)

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.id, f.periodo_aquisitivo_inicio, f.periodo_aquisitivo_fim,
               f.periodo_concessivo_limite, f.dias_direito, f.dias_gozados,
               f.dias_vendidos, f.status
        FROM ferias f
        WHERE f.colaborador_id = ?
        ORDER BY f.periodo_aquisitivo_inicio DESC
    """, (colaborador_id,))

    hoje = date.today()
    resultado = []
    colaborador_em_ferias = False
    ferias_atual_id = None

    for row in cursor.fetchall():
        ferias_id = row[0]

        # Buscar períodos de gozo
        cursor.execute("""
            SELECT data_inicio, data_fim, dias, abono_pecuniario
            FROM periodos_ferias
            WHERE ferias_id = ?
            ORDER BY data_inicio
        """, (ferias_id,))

        periodos = []
        em_ferias_agora = False
        dias_ja_gozados_ate_hoje = 0
        dias_restantes_ferias_atual = 0
        periodo_ferias_atual = None

        for p in cursor.fetchall():
            periodo_info = {
                'data_inicio': p[0],
                'data_fim': p[1],
                'dias': p[2],
                'abono': p[3]
            }
            periodos.append(periodo_info)

            # Verificar se está em férias agora (não é abono pecuniário)
            if p[0] and p[1] and not p[3]:  # não é abono
                try:
                    dt_inicio = datetime.strptime(p[0], '%Y-%m-%d').date()
                    dt_fim = datetime.strptime(p[1], '%Y-%m-%d').date()
                    if dt_inicio <= hoje <= dt_fim:
                        em_ferias_agora = True
                        colaborador_em_ferias = True
                        ferias_atual_id = ferias_id
                        periodo_ferias_atual = periodo_info
                        # Calcular dias já gozados até hoje (incluindo hoje)
                        dias_ja_gozados_ate_hoje = (hoje - dt_inicio).days + 1
                        # Calcular dias restantes das férias atuais
                        dias_restantes_ferias_atual = (dt_fim - hoje).days
                except:
                    pass

        status_original = row[7]
        dias_gozados = row[5]
        dias_vendidos = row[6]
        dias_direito = row[4]

        # Ajustar status e dias se estiver em férias agora
        if em_ferias_agora:
            status_display = 'EM FÉRIAS'
            # Calcular dias gozados até hoje (dias já registrados antes + dias do período atual até hoje)
            # Precisamos calcular quantos dias de outros períodos já foram gozados
            dias_outros_periodos = dias_gozados - (periodo_ferias_atual['dias'] if periodo_ferias_atual else 0)
            dias_gozados_ate_hoje = dias_outros_periodos + dias_ja_gozados_ate_hoje
            dias_restantes = dias_direito - dias_gozados_ate_hoje - dias_vendidos
        else:
            status_display = status_original
            dias_gozados_ate_hoje = dias_gozados
            dias_restantes = dias_direito - dias_gozados - dias_vendidos

        resultado.append({
            'id': ferias_id,
            'periodo_aquisitivo_inicio': row[1],
            'periodo_aquisitivo_fim': row[2],
            'periodo_concessivo_limite': row[3],
            'dias_direito': dias_direito,
            'dias_gozados': dias_gozados_ate_hoje if em_ferias_agora else dias_gozados,
            'dias_gozados_original': dias_gozados,
            'dias_vendidos': dias_vendidos,
            'dias_restantes': dias_restantes,
            'status': status_display,
            'status_original': status_original,
            'periodos': periodos,
            'em_ferias_agora': em_ferias_agora,
            'dias_ja_gozados_ate_hoje': dias_ja_gozados_ate_hoje if em_ferias_agora else 0,
            'dias_restantes_ferias_atual': dias_restantes_ferias_atual if em_ferias_agora else 0,
            'periodo_ferias_atual': periodo_ferias_atual
        })

    conn.close()

    # Se o colaborador está em férias, não mostrar o próximo período (que seria o período aquisitivo em andamento)
    if colaborador_em_ferias and len(resultado) > 1:
        # Filtrar para não mostrar períodos futuros/em aquisição quando está em férias
        resultado_filtrado = []
        for f in resultado:
            # Mostrar o período atual (em férias) e períodos já concluídos
            if f['em_ferias_agora'] or f['status_original'] == 'CONCLUIDO':
                resultado_filtrado.append(f)
            elif f['status_original'] == 'PENDENTE' and not f['em_ferias_agora']:
                # Verificar se é um período futuro (ainda em aquisição)
                try:
                    fim_aquisitivo = datetime.strptime(f['periodo_aquisitivo_fim'], '%Y-%m-%d').date()
                    # Se o período aquisitivo ainda não terminou, não mostrar
                    if fim_aquisitivo >= hoje:
                        continue
                except:
                    pass
                resultado_filtrado.append(f)
        return resultado_filtrado

    return resultado


def obter_historico_salarios(colaborador_id: int) -> List[Dict]:
    """Obtém o histórico de alterações salariais de um colaborador."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT campo, valor_anterior, valor_novo, data_alteracao
        FROM historico_alteracoes
        WHERE colaborador_id = ? AND campo = 'salario'
        ORDER BY data_alteracao DESC
    """, (colaborador_id,))

    resultado = []
    for row in cursor.fetchall():
        try:
            valor_anterior = float(row[1]) if row[1] else 0
            valor_novo = float(row[2]) if row[2] else 0
            diferenca = valor_novo - valor_anterior
            percentual = ((valor_novo - valor_anterior) / valor_anterior * 100) if valor_anterior > 0 else 0
        except:
            valor_anterior = 0
            valor_novo = 0
            diferenca = 0
            percentual = 0

        resultado.append({
            'valor_anterior': valor_anterior,
            'valor_novo': valor_novo,
            'diferenca': diferenca,
            'percentual': percentual,
            'data': row[3]
        })

    conn.close()
    return resultado


def obter_historico_funcoes(colaborador_id: int) -> List[Dict]:
    """Obtém o histórico de alterações de função de um colaborador."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT campo, valor_anterior, valor_novo, data_alteracao
        FROM historico_alteracoes
        WHERE colaborador_id = ? AND campo = 'funcao'
        ORDER BY data_alteracao DESC
    """, (colaborador_id,))

    resultado = [{'funcao_anterior': row[1], 'funcao_nova': row[2], 'data': row[3]} for row in cursor.fetchall()]
    conn.close()
    return resultado


def obter_resumo_colaborador(colaborador_id: int) -> Dict[str, Any]:
    """Obtém um resumo completo do colaborador para análise."""
    colaborador = db.obter_colaborador(colaborador_id)
    if not colaborador:
        return {}

    hoje = date.today()

    # Tempo de empresa
    data_admissao = colaborador.get('data_admissao')
    if data_admissao:
        try:
            admissao = datetime.strptime(str(data_admissao), '%Y-%m-%d').date()
            tempo_empresa_dias = (hoje - admissao).days
            anos = tempo_empresa_dias // 365
            meses = (tempo_empresa_dias % 365) // 30
            if anos > 0:
                tempo_empresa = f"{anos} ano(s)" + (f" e {meses} mês(es)" if meses > 0 else "")
            else:
                tempo_empresa = f"{meses} mês(es)" if meses > 0 else f"{tempo_empresa_dias} dia(s)"
        except:
            tempo_empresa = "-"
            tempo_empresa_dias = 0
    else:
        tempo_empresa = "-"
        tempo_empresa_dias = 0

    # Localização atual
    localizacoes = obter_historico_localizacoes(colaborador_id)
    local_atual = None
    for loc in localizacoes:
        if loc['atual']:
            local_atual = loc
            break

    # Quantidade de localizações
    qtd_localizacoes = len(localizacoes)

    # Férias
    ferias = obter_historico_ferias(colaborador_id)
    ferias_pendente = None
    ultimas_ferias_gozadas = None
    total_dias_ferias_gozados = 0
    for f in ferias:
        total_dias_ferias_gozados += f['dias_gozados']
        if f['status'] == 'PENDENTE' and not ferias_pendente:
            ferias_pendente = f
        # Buscar últimas férias gozadas (com períodos de gozo)
        if f['periodos'] and not ultimas_ferias_gozadas:
            ultimas_ferias_gozadas = f

    return {
        'colaborador': colaborador,
        'tempo_empresa': tempo_empresa,
        'tempo_empresa_dias': tempo_empresa_dias,
        'local_atual': local_atual,
        'qtd_localizacoes': qtd_localizacoes,
        'ferias_pendente': ferias_pendente,
        'ultimas_ferias_gozadas': ultimas_ferias_gozadas,
        'total_dias_ferias_gozados': total_dias_ferias_gozados,
        'localizacoes': localizacoes,
        'ferias': ferias
    }


# =============================================================================
# DIÁLOGO DE ANÁLISE INDIVIDUAL DO COLABORADOR
# =============================================================================

class AnaliseColaboradorDialog:
    """Diálogo para análise individual de um colaborador."""

    def __init__(self, page: ft.Page, colaborador_id: int):
        self.page = page
        self.colaborador_id = colaborador_id
        self.dialog = None

    def mostrar(self, aba_inicial: int = 0):
        """Mostra o diálogo de análise.

        Args:
            aba_inicial: Índice da aba a ser exibida (0=Resumo, 1=Localizações, 2=Férias, 3=Salários, 4=Funções)
        """
        resumo = obter_resumo_colaborador(self.colaborador_id)
        if not resumo:
            return

        colaborador = resumo['colaborador']
        localizacoes = resumo['localizacoes']
        ferias = resumo['ferias']
        historico_salarios = obter_historico_salarios(self.colaborador_id)
        historico_funcoes = obter_historico_funcoes(self.colaborador_id)

        # Criar abas (guardar referência para atualização posterior)
        self.tabs = ft.Tabs(
            selected_index=aba_inicial,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Resumo",
                    icon=ft.Icons.DASHBOARD,
                    content=self._build_aba_resumo(resumo),
                ),
                ft.Tab(
                    text="Localizações",
                    icon=ft.Icons.LOCATION_ON,
                    content=self._build_aba_localizacoes(localizacoes),
                ),
                ft.Tab(
                    text="Férias",
                    icon=ft.Icons.BEACH_ACCESS,
                    content=self._build_aba_ferias(ferias),
                ),
                ft.Tab(
                    text="Salários",
                    icon=ft.Icons.ATTACH_MONEY,
                    content=self._build_aba_salarios(historico_salarios, colaborador),
                ),
                ft.Tab(
                    text="Funções",
                    icon=ft.Icons.WORK,
                    content=self._build_aba_funcoes(historico_funcoes, colaborador),
                ),
            ],
            expand=True,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, color=COR_PRIMARIA),
                ft.Text(f"Análise - {colaborador.get('nome_completo', '')[:40]}", weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                content=self.tabs,
                width=950,
                height=550,
            ),
            actions=[
                ft.TextButton("Fechar", on_click=self._fechar),
            ],
        )

        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _fechar(self, e):
        """Fecha o diálogo."""
        self.dialog.open = False
        self.page.update()

    def _formatar_data(self, data_str: str) -> str:
        """Formata data para exibição."""
        if not data_str:
            return "-"
        try:
            data = datetime.strptime(str(data_str), '%Y-%m-%d')
            return data.strftime('%d/%m/%Y')
        except:
            return str(data_str)

    def _formatar_moeda(self, valor) -> str:
        """Formata valor para moeda."""
        if valor is None:
            return "R$ 0,00"
        try:
            return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "R$ 0,00"

    def _build_aba_resumo(self, resumo: Dict) -> ft.Container:
        """Constrói a aba de resumo."""
        colaborador = resumo['colaborador']
        local_atual = resumo['local_atual']

        # Cards de resumo
        cards = ft.Row([
            self._criar_card_info("Tempo de Empresa", resumo['tempo_empresa'], ft.Icons.ACCESS_TIME, COR_PRIMARIA),
            self._criar_card_info("Localizações", str(resumo['qtd_localizacoes']), ft.Icons.LOCATION_ON, COR_SECUNDARIA),
            self._criar_card_info("Dias de Férias Gozados", str(resumo['total_dias_ferias_gozados']), ft.Icons.BEACH_ACCESS, COR_SUCESSO),
        ], wrap=True, spacing=15)

        # Informações atuais
        info_atual = ft.Column([
            ft.Text("Situação Atual", size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ft.Divider(height=1),
            ft.Row([
                ft.Text("Função:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(colaborador.get('funcao', '-')),
            ]),
            ft.Row([
                ft.Text("Departamento:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(colaborador.get('departamento', '-')),
            ]),
            ft.Row([
                ft.Text("Salário:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(self._formatar_moeda(colaborador.get('salario'))),
            ]),
            ft.Row([
                ft.Text("Local Atual:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(local_atual['local'] if local_atual else "Não definido"),
            ]),
            ft.Row([
                ft.Text("Tempo no Local:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(local_atual['tempo'] if local_atual else "-"),
            ]),
        ], spacing=8)

        # Informações de férias
        ferias_info = ft.Column([
            ft.Text("Férias", size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ft.Divider(height=1),
        ], spacing=8)

        # Últimas férias gozadas
        if resumo.get('ultimas_ferias_gozadas'):
            uf = resumo['ultimas_ferias_gozadas']
            ultimo_periodo = uf['periodos'][0] if uf['periodos'] else None
            if ultimo_periodo:
                ferias_info.controls.extend([
                    ft.Text("Últimas Férias Gozadas", size=12, weight=ft.FontWeight.BOLD, color=COR_SUCESSO),
                    ft.Row([
                        ft.Text("Período:", weight=ft.FontWeight.BOLD, width=150),
                        ft.Text(f"{self._formatar_data(ultimo_periodo['data_inicio'])} a {self._formatar_data(ultimo_periodo['data_fim'])} ({ultimo_periodo['dias']} dias)"),
                    ]),
                    ft.Container(height=10),
                ])

        # Próximas férias
        if resumo['ferias_pendente']:
            fp = resumo['ferias_pendente']
            ferias_info.controls.extend([
                ft.Text("Próximas Férias", size=12, weight=ft.FontWeight.BOLD, color=COR_ALERTA),
                ft.Row([
                    ft.Text("Período Aquisitivo:", weight=ft.FontWeight.BOLD, width=150),
                    ft.Text(f"{self._formatar_data(fp['periodo_aquisitivo_inicio'])} a {self._formatar_data(fp['periodo_aquisitivo_fim'])}"),
                ]),
                ft.Row([
                    ft.Text("Período Concessivo:", weight=ft.FontWeight.BOLD, width=150),
                    ft.Text(f"{self._formatar_data(fp['periodo_aquisitivo_fim'])} a {self._formatar_data(fp['periodo_concessivo_limite'])}"),
                ]),
                ft.Row([
                    ft.Text("Dias Restantes:", weight=ft.FontWeight.BOLD, width=150),
                    ft.Text(f"{fp['dias_restantes']} dias"),
                ]),
            ])
        else:
            ferias_info.controls.append(ft.Text("Nenhum período de férias pendente", italic=True, color=ft.Colors.GREY))

        return ft.Container(
            content=ft.Column([
                cards,
                ft.Container(height=15),
                ft.Row([
                    ft.Container(content=info_atual, expand=True, padding=15, bgcolor="#f8f9fa", border_radius=8),
                    ft.Container(content=ferias_info, expand=True, padding=15, bgcolor="#f8f9fa", border_radius=8),
                ], spacing=15),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
        )

    def _criar_card_info(self, titulo: str, valor: str, icone, cor: str) -> ft.Container:
        """Cria um card de informação."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icone, size=20, color=cor),
                    ft.Text(titulo, size=11, color=ft.Colors.GREY_600),
                ], spacing=5),
                ft.Text(valor, size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            width=180,
        )

    def _build_aba_localizacoes(self, localizacoes: List[Dict]) -> ft.Container:
        """Constrói a aba de localizações com gráfico de barras."""
        if not localizacoes:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCATION_OFF, size=50, color=ft.Colors.GREY),
                    ft.Text("Nenhuma localização registrada", color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=50,
                alignment=ft.alignment.center,
            )

        # Ordenar por dias (maior para menor) para o gráfico
        localizacoes_ordenadas = sorted(localizacoes, key=lambda x: x['dias'], reverse=True)
        max_dias = max(loc['dias'] for loc in localizacoes_ordenadas) if localizacoes_ordenadas else 1

        # Criar gráfico de barras horizontais
        barras = []
        for i, loc in enumerate(localizacoes_ordenadas[:10]):
            percentual = (loc['dias'] / max_dias) * 100 if max_dias > 0 else 0
            cor = COR_SUCESSO if loc['atual'] else obter_cor(i)

            barra = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(loc['local_nome'][:20], size=11, color=ft.Colors.GREY_700),
                        width=150,
                    ),
                    ft.Container(
                        content=ft.Stack([
                            ft.Container(bgcolor="#e8e8e8", height=18, width=300, border_radius=4),
                            ft.Container(bgcolor=cor, height=18, width=max(4, 300 * percentual / 100), border_radius=4),
                        ]),
                        expand=True,
                    ),
                    ft.Text(loc['tempo'], size=11, weight=ft.FontWeight.BOLD, color=cor, width=100),
                    ft.Container(
                        content=ft.Text("ATUAL", size=9, color="white"),
                        bgcolor=COR_SUCESSO,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4,
                        visible=loc['atual'],
                    ),
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=4),
                tooltip=f"{loc['local']}\n{self._formatar_data(loc['data_inicio'])} - {self._formatar_data(loc['data_fim']) if loc['data_fim'] else 'Atual'}",
            )
            barras.append(barra)

        # Timeline/Lista detalhada
        timeline = []
        for loc in localizacoes:
            cor_borda = COR_SUCESSO if loc['atual'] else COR_SECUNDARIA
            timeline.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.LOCATION_ON, size=16, color="white"),
                            bgcolor=cor_borda,
                            padding=8,
                            border_radius=20,
                        ),
                        ft.Column([
                            ft.Text(loc['local'], weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(f"{self._formatar_data(loc['data_inicio'])} - {self._formatar_data(loc['data_fim']) if loc['data_fim'] else 'Atual'}", size=11, color=ft.Colors.GREY_600),
                            ft.Text(f"Tempo: {loc['tempo']}", size=11, color=cor_borda),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    padding=10,
                    border=ft.border.only(left=ft.BorderSide(3, cor_borda)),
                    bgcolor="#f8f9fa",
                    margin=ft.margin.only(bottom=5),
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Text("Tempo por Localização", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Container(
                    content=ft.Column(barras, spacing=2),
                    bgcolor="white",
                    padding=15,
                    border_radius=8,
                    border=ft.border.all(1, "#e0e0e0"),
                ),
                ft.Container(height=15),
                ft.Text("Histórico de Localizações", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Container(
                    content=ft.Column(timeline, spacing=0, scroll=ft.ScrollMode.AUTO),
                    height=180,
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
        )

    def _build_aba_ferias(self, ferias: List[Dict]) -> ft.Container:
        """Constrói a aba de férias."""
        if not ferias:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BEACH_ACCESS, size=50, color=ft.Colors.GREY),
                    ft.Text("Nenhum período de férias registrado", color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=50,
                alignment=ft.alignment.center,
            )

        items = []
        for f in ferias:
            # Definir cor do status
            em_ferias_agora = f.get('em_ferias_agora', False)
            if f['status'] == 'CONCLUIDO':
                status_cor = COR_SUCESSO
            elif f['status'] == 'EM FÉRIAS':
                status_cor = COR_SECUNDARIA  # Azul para em férias
            elif f['status'] == 'PENDENTE':
                status_cor = COR_ALERTA
            else:
                status_cor = COR_SECUNDARIA

            # Calcular período concessivo (dia seguinte ao fim do aquisitivo até o limite)
            periodo_concessivo_inicio = ""
            periodo_concessivo_inicio_dt = None
            if f['periodo_aquisitivo_fim']:
                try:
                    fim_aquisitivo = datetime.strptime(str(f['periodo_aquisitivo_fim']), '%Y-%m-%d')
                    inicio_concessivo = fim_aquisitivo + timedelta(days=1)
                    periodo_concessivo_inicio = inicio_concessivo.strftime('%Y-%m-%d')
                    periodo_concessivo_inicio_dt = inicio_concessivo
                except:
                    periodo_concessivo_inicio = f['periodo_aquisitivo_fim']

            # Verificar se está no período concessivo (após o período aquisitivo)
            hoje = datetime.now().date()
            esta_no_periodo_concessivo = False
            if f['periodo_aquisitivo_fim']:
                try:
                    fim_aquisitivo_dt = datetime.strptime(str(f['periodo_aquisitivo_fim']), '%Y-%m-%d').date()
                    esta_no_periodo_concessivo = hoje > fim_aquisitivo_dt
                except:
                    pass

            # Determinar se deve mostrar o botão de inserir férias
            # Só aparece se: status PENDENTE e está no período concessivo (e não está em férias agora)
            mostrar_botao_inserir = f['status'] == 'PENDENTE' and esta_no_periodo_concessivo and not em_ferias_agora

            # Períodos de gozo (férias gozadas) - separar férias de abono
            periodos_widgets = []
            periodos_ferias = [p for p in f['periodos'] if not p['abono']]
            periodos_abono = [p for p in f['periodos'] if p['abono']]
            total_dias_abono = sum(p['dias'] for p in periodos_abono)

            if periodos_ferias:
                periodos_widgets.append(
                    ft.Text("Férias Gozadas:" if not em_ferias_agora else "Férias:", size=11, weight=ft.FontWeight.BOLD, color=COR_SUCESSO if not em_ferias_agora else COR_SECUNDARIA)
                )
                for p in periodos_ferias:
                    # Verificar se é o período atual de férias
                    periodo_atual = f.get('periodo_ferias_atual')
                    is_periodo_atual = periodo_atual and p['data_inicio'] == periodo_atual['data_inicio'] and p['data_fim'] == periodo_atual['data_fim']

                    if is_periodo_atual and em_ferias_agora:
                        # Mostrar informação especial para período atual
                        dias_gozados_hoje = f.get('dias_ja_gozados_ate_hoje', 0)
                        dias_restantes_ferias = f.get('dias_restantes_ferias_atual', 0)
                        periodos_widgets.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.BEACH_ACCESS, size=14, color=COR_SECUNDARIA),
                                        ft.Text(f"{self._formatar_data(p['data_inicio'])} a {self._formatar_data(p['data_fim'])} ({p['dias']} dias)", size=11, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Icon(ft.Icons.TODAY, size=12, color=COR_PRIMARIA),
                                        ft.Text(f"Hoje: {dias_gozados_hoje}º dia de férias", size=10, color=COR_PRIMARIA, weight=ft.FontWeight.BOLD),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Icon(ft.Icons.HOURGLASS_BOTTOM, size=12, color=COR_ALERTA),
                                        ft.Text(f"Retorno em {dias_restantes_ferias} dia(s)", size=10, color=COR_ALERTA),
                                    ], spacing=5),
                                ], spacing=3),
                                bgcolor="#e3f2fd",
                                padding=8,
                                border_radius=6,
                                margin=ft.margin.only(top=5),
                            )
                        )
                    else:
                        periodos_widgets.append(
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=COR_SUCESSO),
                                ft.Text(f"{self._formatar_data(p['data_inicio'])} a {self._formatar_data(p['data_fim'])} ({p['dias']} dias)", size=11, color=ft.Colors.GREY_700),
                            ], spacing=5)
                        )
            else:
                periodos_widgets.append(
                    ft.Text("Nenhum período de férias gozado ainda", size=11, italic=True, color=ft.Colors.GREY_500)
                )

            # Mostrar abono pecuniário apenas como quantidade de dias vendidos
            if total_dias_abono > 0:
                periodos_widgets.append(
                    ft.Row([
                        ft.Icon(ft.Icons.ATTACH_MONEY, size=14, color=COR_SECUNDARIA),
                        ft.Text(f"Abono Pecuniário: {total_dias_abono} dia(s) vendido(s)", size=11, color=COR_SECUNDARIA, weight=ft.FontWeight.BOLD),
                    ], spacing=5)
                )

            # Criar botão de inserir férias se aplicável
            botao_inserir_ferias = ft.Container()
            if mostrar_botao_inserir:
                botao_inserir_ferias = ft.Container(
                    content=ft.ElevatedButton(
                        "Inserir Férias",
                        icon=ft.Icons.ADD_CIRCLE,
                        bgcolor=COR_SUCESSO,
                        color="white",
                        on_click=lambda e, ferias_id=f['id'], paf=f['periodo_aquisitivo_fim'], pcl=f['periodo_concessivo_limite']: self._abrir_dialog_inserir_ferias(ferias_id, paf, pcl),
                    ),
                    padding=ft.padding.only(top=10),
                )

            items.append(
                ft.Container(
                    content=ft.Column([
                        # Cabeçalho com status
                        ft.Row([
                            ft.Text("Período de Férias", weight=ft.FontWeight.BOLD, size=14, color=COR_PRIMARIA),
                            ft.Container(
                                content=ft.Text(f['status'], size=10, color="white"),
                                bgcolor=status_cor,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color="#e0e0e0"),

                        # Período Aquisitivo
                        ft.Row([
                            ft.Icon(ft.Icons.DATE_RANGE, size=16, color=COR_PRIMARIA),
                            ft.Text("Período Aquisitivo:", weight=ft.FontWeight.BOLD, size=12, width=140),
                            ft.Text(f"{self._formatar_data(f['periodo_aquisitivo_inicio'])} a {self._formatar_data(f['periodo_aquisitivo_fim'])}", size=12),
                        ], spacing=5),

                        # Período Concessivo
                        ft.Row([
                            ft.Icon(ft.Icons.EVENT_AVAILABLE, size=16, color=COR_ALERTA),
                            ft.Text("Período Concessivo:", weight=ft.FontWeight.BOLD, size=12, width=140),
                            ft.Text(f"{self._formatar_data(periodo_concessivo_inicio)} a {self._formatar_data(f['periodo_concessivo_limite'])}", size=12),
                        ], spacing=5),

                        # Resumo de dias
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Direito", size=10, color=ft.Colors.GREY_600),
                                        ft.Text(f"{f['dias_direito']}d", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=8,
                                    bgcolor="#f0f4f8",
                                    border_radius=6,
                                    width=80,
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Gozados", size=10, color=ft.Colors.GREY_600),
                                        ft.Text(f"{f['dias_gozados']}d", size=14, weight=ft.FontWeight.BOLD, color=COR_SUCESSO),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=8,
                                    bgcolor="#e8f5e9",
                                    border_radius=6,
                                    width=80,
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Vendidos", size=10, color=ft.Colors.GREY_600),
                                        ft.Text(f"{f['dias_vendidos']}d", size=14, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=8,
                                    bgcolor="#e3f2fd",
                                    border_radius=6,
                                    width=80,
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Restantes", size=10, color=ft.Colors.GREY_600),
                                        ft.Text(f"{f['dias_restantes']}d", size=14, weight=ft.FontWeight.BOLD,
                                               color=COR_ERRO if f['dias_restantes'] > 0 and f['status'] == 'PENDENTE' else COR_PRIMARIA),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=8,
                                    bgcolor="#fff3e0" if f['dias_restantes'] > 0 else "#f0f4f8",
                                    border_radius=6,
                                    width=80,
                                ),
                            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                            padding=ft.padding.only(top=8, bottom=8),
                        ),

                        # Férias gozadas
                        ft.Container(
                            content=ft.Column(periodos_widgets, spacing=4),
                            padding=ft.padding.only(top=5),
                        ),

                        # Botão de inserir férias (só aparece se pendente e no período concessivo)
                        botao_inserir_ferias,
                    ], spacing=8),
                    padding=15,
                    bgcolor="white",
                    border_radius=10,
                    border=ft.border.all(1, status_cor),
                    margin=ft.margin.only(bottom=10),
                )
            )

        return ft.Container(
            content=ft.Column(items, scroll=ft.ScrollMode.AUTO),
            padding=10,
        )

    def _abrir_dialog_inserir_ferias(self, ferias_id: int, periodo_aquisitivo_fim: str, periodo_concessivo_limite: str):
        """Abre diálogo para registrar período de férias."""
        # Calcular início do período concessivo (dia seguinte ao fim do aquisitivo)
        periodo_concessivo_inicio = datetime.strptime(periodo_aquisitivo_fim, '%Y-%m-%d') + timedelta(days=1)
        periodo_concessivo_fim = datetime.strptime(periodo_concessivo_limite, '%Y-%m-%d')

        data_inicio = ft.TextField(label="Data Início *", width=130, hint_text="DD/MM/AAAA")
        data_fim = ft.TextField(label="Data Fim *", width=130, hint_text="DD/MM/AAAA")
        dias = ft.TextField(label="Dias Férias *", width=80, value="30", keyboard_type=ft.KeyboardType.NUMBER)
        abono = ft.Checkbox(label="Abono Pecuniário (venda de dias)", value=False)

        # Campos para abono pecuniário
        dias_vender = ft.TextField(label="Dias a Vender *", width=100, value="10", keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        dias_ferias_abono = ft.TextField(label="Dias de Férias *", width=100, value="20", keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        total_dias_info = ft.Text("Total: 30 dias", size=12, color=COR_SUCESSO, weight=ft.FontWeight.BOLD, visible=False)
        container_abono = ft.Container(
            content=ft.Column([
                ft.Text("Distribuição dos 30 dias:", size=11, color=COR_SECUNDARIA, weight=ft.FontWeight.BOLD),
                ft.Row([dias_ferias_abono, dias_vender, total_dias_info], spacing=10, alignment=ft.MainAxisAlignment.START),
            ], spacing=5),
            visible=False,
            padding=ft.padding.only(top=5),
        )

        obs = ft.TextField(label="Observações", width=380, multiline=True, min_lines=1, max_lines=2)
        justificativa = ft.TextField(label="Justificativa (férias antecipadas) *", width=380, multiline=True, min_lines=1, max_lines=2, visible=False)
        aviso_atraso = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COR_ERRO, size=16),
                ft.Text("ATENÇÃO: Férias após o período concessivo! Isso deve ser evitado.", color=COR_ERRO, size=12, weight=ft.FontWeight.BOLD),
            ], spacing=5),
            visible=False,
            padding=ft.padding.only(top=5),
        )

        # Flag para evitar loops infinitos
        atualizando_campos = False

        def on_abono_change(e):
            """Mostra/esconde campos de abono pecuniário."""
            if abono.value:
                # Mostrar campos de abono
                container_abono.visible = True
                dias_vender.visible = True
                dias_ferias_abono.visible = True
                total_dias_info.visible = True
                dias.visible = False
                # Definir valores padrão
                dias_vender.value = "10"
                dias_ferias_abono.value = "20"
                atualizar_total_dias()
                # Recalcular data fim baseado nos dias de férias
                if data_inicio.value and len(data_inicio.value) == 10:
                    calcular_data_fim_por_dias_abono()
            else:
                # Esconder campos de abono
                container_abono.visible = False
                dias_vender.visible = False
                dias_ferias_abono.visible = False
                total_dias_info.visible = False
                dias.visible = True
                dias.value = "30"
                # Recalcular data fim
                if data_inicio.value and len(data_inicio.value) == 10:
                    calcular_data_fim_por_dias()
            self.page.update()

        def atualizar_total_dias():
            """Atualiza o texto do total de dias."""
            try:
                d_vender = int(dias_vender.value) if dias_vender.value else 0
                d_ferias = int(dias_ferias_abono.value) if dias_ferias_abono.value else 0
                total = d_vender + d_ferias
                if total == 30:
                    total_dias_info.value = f"Total: {total} dias"
                    total_dias_info.color = COR_SUCESSO
                else:
                    total_dias_info.value = f"Total: {total} dias (deve ser 30)"
                    total_dias_info.color = COR_ERRO
            except:
                total_dias_info.value = "Total: inválido"
                total_dias_info.color = COR_ERRO

        def on_dias_vender_change(e):
            """Atualiza dias de férias quando dias a vender muda."""
            try:
                d_vender = int(dias_vender.value) if dias_vender.value else 0
                if d_vender > 10:
                    d_vender = 10
                    dias_vender.value = "10"
                if d_vender < 0:
                    d_vender = 0
                    dias_vender.value = "0"
                dias_ferias_abono.value = str(30 - d_vender)
                atualizar_total_dias()
                calcular_data_fim_por_dias_abono()
                self.page.update()
            except:
                pass

        def on_dias_ferias_abono_change(e):
            """Atualiza dias a vender quando dias de férias muda."""
            try:
                d_ferias = int(dias_ferias_abono.value) if dias_ferias_abono.value else 0
                if d_ferias > 30:
                    d_ferias = 30
                    dias_ferias_abono.value = "30"
                if d_ferias < 20:
                    d_ferias = 20
                    dias_ferias_abono.value = "20"
                dias_vender.value = str(30 - d_ferias)
                atualizar_total_dias()
                calcular_data_fim_por_dias_abono()
                self.page.update()
            except:
                pass

        def calcular_data_fim_por_dias_abono():
            """Calcula a data fim baseada nos dias de férias (não inclui dias vendidos)."""
            nonlocal atualizando_campos
            if atualizando_campos:
                return
            try:
                if data_inicio.value and dias_ferias_abono.value:
                    dt_inicio = datetime.strptime(data_inicio.value, '%d/%m/%Y')
                    qtd_dias = int(dias_ferias_abono.value)
                    if qtd_dias > 0:
                        dt_fim = dt_inicio + timedelta(days=qtd_dias - 1)
                        atualizando_campos = True
                        data_fim.value = dt_fim.strftime('%d/%m/%Y')
                        self.page.update()
                        atualizando_campos = False
            except ValueError:
                pass

        abono.on_change = on_abono_change
        dias_vender.on_change = on_dias_vender_change
        dias_ferias_abono.on_change = on_dias_ferias_abono_change

        def aplicar_mascara_data(campo):
            """Aplica máscara de data DD/MM/AAAA no campo."""
            texto = campo.value or ""
            # Remover tudo que não é número
            apenas_numeros = ''.join(c for c in texto if c.isdigit())
            # Limitar a 8 dígitos
            apenas_numeros = apenas_numeros[:8]
            # Aplicar máscara
            resultado = ""
            for i, c in enumerate(apenas_numeros):
                if i == 2 or i == 4:
                    resultado += "/"
                resultado += c
            return resultado

        def calcular_dias_entre_datas():
            """Calcula a quantidade de dias entre data início e data fim."""
            nonlocal atualizando_campos
            if atualizando_campos:
                return
            try:
                if data_inicio.value and data_fim.value:
                    dt_inicio = datetime.strptime(data_inicio.value, '%d/%m/%Y')
                    dt_fim = datetime.strptime(data_fim.value, '%d/%m/%Y')
                    if dt_fim >= dt_inicio:
                        diferenca = (dt_fim - dt_inicio).days + 1  # +1 porque inclui o dia inicial
                        atualizando_campos = True
                        dias.value = str(diferenca)
                        self.page.update()
                        atualizando_campos = False
            except ValueError:
                pass  # Data inválida, ignorar

        def calcular_data_fim_por_dias():
            """Calcula a data fim baseada na data início e quantidade de dias."""
            nonlocal atualizando_campos
            if atualizando_campos:
                return
            try:
                if data_inicio.value and dias.value:
                    dt_inicio = datetime.strptime(data_inicio.value, '%d/%m/%Y')
                    qtd_dias = int(dias.value)
                    if qtd_dias > 0:
                        dt_fim = dt_inicio + timedelta(days=qtd_dias - 1)  # -1 porque o dia inicial conta
                        atualizando_campos = True
                        data_fim.value = dt_fim.strftime('%d/%m/%Y')
                        self.page.update()
                        atualizando_campos = False
            except ValueError:
                pass  # Valor inválido, ignorar

        def validar_periodo_concessivo():
            """Valida se a data de início está dentro do período concessivo."""
            try:
                if data_inicio.value:
                    dt_inicio = datetime.strptime(data_inicio.value, '%d/%m/%Y')

                    # Antes do período concessivo - precisa justificativa
                    if dt_inicio < periodo_concessivo_inicio:
                        justificativa.visible = True
                        aviso_atraso.visible = False
                    # Depois do período concessivo - mostrar aviso
                    elif dt_inicio > periodo_concessivo_fim:
                        justificativa.visible = False
                        aviso_atraso.visible = True
                    # Dentro do período concessivo - ok
                    else:
                        justificativa.visible = False
                        aviso_atraso.visible = False

                    self.page.update()
            except ValueError:
                pass

        def on_data_inicio_change(e):
            # Aplicar máscara de data
            valor_formatado = aplicar_mascara_data(data_inicio)
            if data_inicio.value != valor_formatado:
                data_inicio.value = valor_formatado
                self.page.update()
                return
            # Se tem data fim, calcular dias; senão, se tem dias, calcular data fim
            if len(data_inicio.value) == 10:
                if abono.value:
                    # Com abono, usar dias de férias do abono
                    calcular_data_fim_por_dias_abono()
                elif data_fim.value:
                    calcular_dias_entre_datas()
                elif dias.value:
                    calcular_data_fim_por_dias()
            # Validar período concessivo
            if len(data_inicio.value) == 10:
                validar_periodo_concessivo()

        def on_data_fim_change(e):
            # Aplicar máscara de data
            valor_formatado = aplicar_mascara_data(data_fim)
            if data_fim.value != valor_formatado:
                data_fim.value = valor_formatado
                self.page.update()
                return
            if len(data_fim.value) == 10:
                calcular_dias_entre_datas()

        def on_dias_change(e):
            calcular_data_fim_por_dias()

        data_inicio.on_change = on_data_inicio_change
        data_fim.on_change = on_data_fim_change
        dias.on_change = on_dias_change

        def formatar_data_db(data_br: str) -> str:
            """Converte data de DD/MM/AAAA para AAAA-MM-DD."""
            if not data_br:
                return None
            try:
                partes = data_br.split('/')
                if len(partes) == 3:
                    return f"{partes[2]}-{partes[1]}-{partes[0]}"
            except:
                pass
            return None

        def salvar_periodo(ev2):
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para editar dados."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            if not data_inicio.value or not data_fim.value:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Preencha os campos obrigatórios!"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Validações específicas para abono
            if abono.value:
                try:
                    d_vender = int(dias_vender.value) if dias_vender.value else 0
                    d_ferias = int(dias_ferias_abono.value) if dias_ferias_abono.value else 0
                    if d_vender + d_ferias != 30:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text("A soma dos dias deve ser 30!"), bgcolor=COR_ERRO)
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                    if d_vender > 10:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text("Máximo de 10 dias podem ser vendidos!"), bgcolor=COR_ERRO)
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                    if d_ferias < 20:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text("Mínimo de 20 dias de férias obrigatório!"), bgcolor=COR_ERRO)
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                except:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Valores de dias inválidos!"), bgcolor=COR_ERRO)
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
            else:
                if not dias.value:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Preencha os campos obrigatórios!"), bgcolor=COR_ERRO)
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

            # Verificar se precisa de justificativa (férias antecipadas)
            try:
                dt_inicio = datetime.strptime(data_inicio.value, '%d/%m/%Y')
                if dt_inicio < periodo_concessivo_inicio and not justificativa.value.strip():
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Férias antecipadas requerem justificativa!"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
            except ValueError:
                pass

            try:
                data_inicio_db = formatar_data_db(data_inicio.value)
                data_fim_db = formatar_data_db(data_fim.value)

                # Montar observações com justificativa se houver
                observacoes_final = obs.value or ""
                if justificativa.visible and justificativa.value.strip():
                    observacoes_final = f"[FÉRIAS ANTECIPADAS] Justificativa: {justificativa.value.strip()}" + (f"\n{obs.value}" if obs.value else "")
                elif aviso_atraso.visible:
                    observacoes_final = f"[FÉRIAS APÓS PERÍODO CONCESSIVO]" + (f"\n{obs.value}" if obs.value else "")

                if abono.value:
                    # Com abono pecuniário: registrar férias e abono separadamente
                    d_ferias = int(dias_ferias_abono.value)
                    d_vender = int(dias_vender.value)

                    # Registrar período de férias (não é abono)
                    db.registrar_gozo_ferias(
                        ferias_id, data_inicio_db, data_fim_db,
                        d_ferias, False, observacoes_final
                    )

                    # Registrar abono pecuniário (apenas dias vendidos, sem período)
                    db.registrar_gozo_ferias(
                        ferias_id, None, None,  # sem datas para abono
                        d_vender, True, f"Abono Pecuniário - {d_vender} dias vendidos"
                    )

                    # Registrar no histórico
                    db.registrar_alteracao(
                        self.colaborador_id,
                        'ferias_registradas',
                        None,
                        f"{data_inicio.value} a {data_fim.value} ({d_ferias} dias férias + {d_vender} dias abono)"
                    )
                else:
                    # Sem abono: registrar normalmente
                    dias_int = int(dias.value)
                    db.registrar_gozo_ferias(
                        ferias_id, data_inicio_db, data_fim_db,
                        dias_int, False, observacoes_final
                    )

                    # Registrar no histórico
                    db.registrar_alteracao(
                        self.colaborador_id,
                        'ferias_registradas',
                        None,
                        f"{data_inicio.value} a {data_fim.value} ({dias_int} dias)"
                    )

                # Fechar o sub-diálogo de inserção
                sub_dialog.open = False
                self.page.update()

                # Mostrar mensagem de sucesso
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Férias registradas com sucesso!"), bgcolor=COR_SUCESSO)
                self.page.snack_bar.open = True
                self.page.update()

                # Reabrir o diálogo de análise com dados atualizados na aba Férias
                self.mostrar(aba_inicial=2)

            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {str(ex)}"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()

        def cancelar_sub(ev2):
            sub_dialog.open = False
            self.page.update()
            # Reabrir o diálogo de análise na aba Férias
            self.mostrar(aba_inicial=2)

        # Informação do período concessivo
        info_periodo = ft.Container(
            content=ft.Text(
                f"Período Concessivo: {periodo_concessivo_inicio.strftime('%d/%m/%Y')} a {periodo_concessivo_fim.strftime('%d/%m/%Y')}",
                size=11, italic=True, color=COR_SECUNDARIA
            ),
            padding=ft.padding.only(bottom=5),
        )

        sub_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Período de Férias"),
            content=ft.Container(
                content=ft.Column([
                    info_periodo,
                    ft.Row([data_inicio, data_fim, dias], spacing=10),
                    abono,
                    container_abono,
                    justificativa,
                    aviso_atraso,
                    obs,
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=420,
                height=280,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_sub),
                ft.ElevatedButton("Salvar", on_click=salvar_periodo, bgcolor=COR_SUCESSO, color="white"),
            ],
        )

        self.page.overlay.append(sub_dialog)
        sub_dialog.open = True
        self.page.update()

    def _atualizar_aba_ferias(self):
        """Atualiza o conteúdo da aba de férias após inserir férias."""
        # Recarregar dados de férias
        ferias = obter_historico_ferias(self.colaborador_id)

        # Reconstruir a aba de férias
        novo_conteudo = self._build_aba_ferias(ferias)

        # Atualizar a aba de férias no diálogo (índice 2)
        if hasattr(self, 'tabs') and self.tabs and len(self.tabs.tabs) > 2:
            self.tabs.tabs[2].content = novo_conteudo
            self.page.update()

    def _build_aba_salarios(self, historico: List[Dict], colaborador: Dict) -> ft.Container:
        """Constrói a aba de histórico salarial."""
        salario_atual = colaborador.get('salario', 0)

        # Card do salário atual
        card_atual = ft.Container(
            content=ft.Column([
                ft.Text("Salário Atual", size=12, color=ft.Colors.GREY_600),
                ft.Text(self._formatar_moeda(salario_atual), size=24, weight=ft.FontWeight.BOLD, color=COR_SUCESSO),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, COR_SUCESSO),
            width=200,
        )

        if not historico:
            return ft.Container(
                content=ft.Column([
                    card_atual,
                    ft.Container(height=20),
                    ft.Text("Nenhuma alteração salarial registrada", color=ft.Colors.GREY, italic=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
            )

        # Lista de alterações
        items = []
        for h in historico:
            cor = COR_SUCESSO if h['diferenca'] > 0 else COR_ERRO if h['diferenca'] < 0 else COR_SECUNDARIA
            icone = ft.Icons.TRENDING_UP if h['diferenca'] > 0 else ft.Icons.TRENDING_DOWN if h['diferenca'] < 0 else ft.Icons.TRENDING_FLAT

            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icone, color=cor, size=24),
                        ft.Column([
                            ft.Text(self._formatar_data(h['data']), size=11, color=ft.Colors.GREY_600),
                            ft.Row([
                                ft.Text(self._formatar_moeda(h['valor_anterior']), size=12),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.GREY),
                                ft.Text(self._formatar_moeda(h['valor_novo']), size=12, weight=ft.FontWeight.BOLD),
                            ], spacing=5),
                        ], spacing=2, expand=True),
                        ft.Column([
                            ft.Text(f"{'+' if h['diferenca'] > 0 else ''}{self._formatar_moeda(h['diferenca'])}", color=cor, weight=ft.FontWeight.BOLD),
                            ft.Text(f"({'+' if h['percentual'] > 0 else ''}{h['percentual']:.1f}%)", size=11, color=cor),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
                    ], spacing=10),
                    padding=12,
                    bgcolor="white",
                    border_radius=8,
                    border=ft.border.all(1, "#e0e0e0"),
                    margin=ft.margin.only(bottom=8),
                )
            )

        return ft.Container(
            content=ft.Column([
                card_atual,
                ft.Container(height=15),
                ft.Text("Histórico de Alterações", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Column(items, scroll=ft.ScrollMode.AUTO),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
        )

    def _build_aba_funcoes(self, historico: List[Dict], colaborador: Dict) -> ft.Container:
        """Constrói a aba de histórico de funções."""
        funcao_atual = colaborador.get('funcao', '-')

        # Card da função atual
        card_atual = ft.Container(
            content=ft.Column([
                ft.Text("Função Atual", size=12, color=ft.Colors.GREY_600),
                ft.Text(funcao_atual, size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, COR_PRIMARIA),
            width=300,
        )

        if not historico:
            return ft.Container(
                content=ft.Column([
                    card_atual,
                    ft.Container(height=20),
                    ft.Text("Nenhuma alteração de função registrada", color=ft.Colors.GREY, italic=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
            )

        # Lista de alterações
        items = []
        for h in historico:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SWAP_HORIZ, color=COR_SECUNDARIA, size=24),
                        ft.Column([
                            ft.Text(self._formatar_data(h['data']), size=11, color=ft.Colors.GREY_600),
                            ft.Row([
                                ft.Text(h['funcao_anterior'] or '-', size=12),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.GREY),
                                ft.Text(h['funcao_nova'] or '-', size=12, weight=ft.FontWeight.BOLD),
                            ], spacing=5),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    padding=12,
                    bgcolor="white",
                    border_radius=8,
                    border=ft.border.all(1, "#e0e0e0"),
                    margin=ft.margin.only(bottom=8),
                )
            )

        return ft.Container(
            content=ft.Column([
                card_atual,
                ft.Container(height=15),
                ft.Text("Histórico de Alterações", size=14, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Column(items, scroll=ft.ScrollMode.AUTO),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
        )
