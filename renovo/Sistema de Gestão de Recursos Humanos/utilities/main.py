"""
Sistema de Gestão de RH - RENOVO Montagens Industriais
Componentes e Utilitários

Versão: 1.0.0
"""

import flet as ft
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import os
import shutil
import re

# Importar módulos locais
from . import database as db
from .pdf_generator import gerar_ficha_registro_pdf
from .excel_export import (
    exportar_colaboradores_excel,
    exportar_aniversariantes_excel,
    exportar_contratos_vencendo_excel,
    exportar_ferias_vencendo_excel
)

# Importar constantes e funções do módulo constantes
from .constantes import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_SUCESSO, COR_ALERTA, COR_ERRO, COR_FUNDO, COR_CINZA_CLARO,
    ESTADOS_BR, GRAUS_INSTRUCAO, ESTADOS_CIVIS, TIPOS_CONTA, FORMAS_PAGAMENTO,
    TIPOS_CONTRATO, PARENTESCOS, TIPOS_CNH,
    criar_campo_texto, criar_dropdown, criar_data_picker, criar_secao,
    formatar_cpf, formatar_data_br, formatar_data_db, formatar_moeda, criar_campo_view
)
from .dashboard import AnaliseColaboradorDialog


def criar_alertas_widget(on_click_contrato=None, on_click_ferias=None) -> ft.Column:
    """Widget para exibir alertas de contratos e férias."""
    # Contratos: alerta quando faltam 5 dias ou menos para vencer
    contratos_vencendo = db.listar_contratos_vencendo(5)
    # Férias: alerta quando faltam 90 dias (3 meses) ou menos para vencer o período concessivo
    ferias_vencendo = db.listar_ferias_vencendo_dias(90)

    alertas = []

    if contratos_vencendo:
        alertas.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color="white", size=20),
                    ft.Text(f"{len(contratos_vencendo)} contrato(s) de experiência vencendo em até 5 dias!",
                           color="white", weight=ft.FontWeight.BOLD),
                    ft.TextButton("Ver", on_click=on_click_contrato,
                                 style=ft.ButtonStyle(color="white")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=COR_ERRO,
                padding=10,
                border_radius=8,
                margin=ft.margin.only(bottom=5),
            )
        )

    if ferias_vencendo:
        alertas.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BEACH_ACCESS, color="white", size=20),
                    ft.Text(f"{len(ferias_vencendo)} período(s) de férias vencendo em até 90 dias!",
                           color="white", weight=ft.FontWeight.BOLD),
                    ft.TextButton("Ver", on_click=on_click_ferias,
                                 style=ft.ButtonStyle(color="white")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=COR_ALERTA,
                padding=10,
                border_radius=8,
                margin=ft.margin.only(bottom=5),
            )
        )

    return ft.Column(alertas) if alertas else ft.Container()


class BlocklistChecker:
    """Verifica CPF na blocklist."""
    
    @staticmethod
    def verificar(cpf: str, page: ft.Page) -> list:
        """Verifica se o CPF está na blocklist e mostra alerta."""
        cpf_limpo = re.sub(r'\D', '', cpf)
        if len(cpf_limpo) != 11:
            return []
        
        historico = db.verificar_blocklist(cpf_limpo)
        
        if historico:
            def fechar_dialog(e):
                dialog.open = False
                page.update()
            
            lista_hist = []
            for h in historico:
                lista_hist.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"Empresa: {h.get('empresa_nome', 'N/A')}", 
                                   weight=ft.FontWeight.BOLD),
                            ft.Text(f"Período: {formatar_data_br(h.get('data_admissao'))} a "
                                   f"{formatar_data_br(h.get('data_desligamento'))}"),
                            ft.Text(f"Motivo: {h.get('motivo_desligamento', 'Não informado')}"),
                        ], spacing=5),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY),
                        border_radius=8,
                    )
                )
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=COR_ALERTA, size=30),
                    ft.Text("ATENÇÃO: Histórico!", color=COR_ALERTA),
                ]),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"CPF {formatar_cpf(cpf_limpo)} possui registro(s):"),
                        ft.Divider(),
                        ft.Column(lista_hist, scroll=ft.ScrollMode.AUTO),
                    ], spacing=10),
                    width=400,
                    height=250,
                ),
                actions=[ft.TextButton("OK", on_click=fechar_dialog)],
            )
            
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
        
        return historico


class FichaColaborador:
    """Tela de visualização da ficha do colaborador."""
    
    def __init__(self, page: ft.Page, colaborador_id: int, on_voltar=None):
        self.page = page
        self.colaborador_id = colaborador_id
        self.on_voltar_callback = on_voltar
        self.colaborador = None
        self.dependentes = []
    
    def build(self) -> ft.Container:
        self.colaborador = db.obter_colaborador(self.colaborador_id)
        if not self.colaborador:
            return ft.Container(content=ft.Text("Colaborador não encontrado", color=COR_ERRO))

        self.dependentes = db.listar_dependentes(self.colaborador_id)
        c = self.colaborador
        sim_nao = lambda v: "Sim" if v else "Não"

        # Lista de dependentes
        lista_dep = []
        if not self.dependentes:
            lista_dep.append(ft.Text("Nenhum dependente cadastrado", italic=True, color=ft.Colors.GREY))
        else:
            for dep in self.dependentes:
                lista_dep.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(dep.get('nome', ''), weight=ft.FontWeight.BOLD),
                            ft.Text(f"{dep.get('parentesco', '')} - Nasc: {formatar_data_br(dep.get('data_nascimento'))} - CPF: {formatar_cpf(dep.get('cpf', ''))}"),
                        ], spacing=2),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                    )
                )

        # Criar conteúdo das abas
        aba_dados_pessoais = self._criar_aba_dados_pessoais_view(c, sim_nao)
        aba_documentos = self._criar_aba_documentos_view(c)
        aba_contrato = self._criar_aba_contrato_view(c, sim_nao)
        aba_beneficios = self._criar_aba_beneficios_view(c, sim_nao, lista_dep)

        # Tabs organizadas
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Dados Pessoais",
                    icon=ft.Icons.PERSON,
                    content=aba_dados_pessoais,
                ),
                ft.Tab(
                    text="Documentos",
                    icon=ft.Icons.BADGE,
                    content=aba_documentos,
                ),
                ft.Tab(
                    text="Contrato",
                    icon=ft.Icons.WORK,
                    content=aba_contrato,
                ),
                ft.Tab(
                    text="Benefícios e Outros",
                    icon=ft.Icons.CARD_GIFTCARD,
                    content=aba_beneficios,
                ),
            ],
            expand=1,
        )

        return ft.Column([
            self._criar_header(),
            ft.Container(
                content=tabs,
                bgcolor="white",
                border_radius=8,
                padding=10,
                expand=1,
            ),
        ], spacing=10, expand=1)

    def _criar_aba_dados_pessoais_view(self, c, sim_nao):
        """Cria o conteúdo da aba Dados Pessoais para visualização."""
        conteudo = [
            criar_secao("Dados Pessoais", [
                ft.Row([
                    criar_campo_view("Nome Completo", c.get('nome_completo'), 300),
                    criar_campo_view("Data Nascimento", formatar_data_br(c.get('data_nascimento'))),
                    criar_campo_view("Sexo", c.get('sexo')),
                    criar_campo_view("Estado Civil", c.get('estado_civil')),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Naturalidade", c.get('naturalidade')),
                    criar_campo_view("UF Nat.", c.get('uf_naturalidade'), 80),
                    criar_campo_view("Grau de Instrução", c.get('grau_instrucao'), 180),
                    criar_campo_view("Curso/Formação", c.get('curso_formacao'), 200),
                    criar_campo_view("Deficiência", c.get('deficiencia') or "Nenhuma"),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Nome da Mãe", c.get('nome_mae'), 300),
                    criar_campo_view("CPF Mãe", formatar_cpf(c.get('cpf_mae', ''))),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Nome do Pai", c.get('nome_pai'), 300),
                    criar_campo_view("CPF Pai", formatar_cpf(c.get('cpf_pai', ''))),
                ], wrap=True),
            ]),
            criar_secao("Endereço", [
                ft.Row([
                    criar_campo_view("Endereço", c.get('endereco'), 300),
                    criar_campo_view("Número", c.get('numero'), 80),
                    criar_campo_view("Complemento", c.get('complemento'), 150),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Bairro", c.get('bairro'), 200),
                    criar_campo_view("CEP", c.get('cep'), 100),
                    criar_campo_view("Cidade", c.get('cidade'), 200),
                    criar_campo_view("UF", c.get('uf_endereco'), 80),
                ], wrap=True),
            ]),
            criar_secao("Contato", [
                ft.Row([
                    criar_campo_view("Telefone", c.get('telefone')),
                    criar_campo_view("Celular", c.get('celular')),
                    criar_campo_view("E-mail", c.get('email'), 250),
                ], wrap=True),
            ]),
        ]

        # Adicionar cônjuge se casado
        if c.get('estado_civil') == 'Casado(a)':
            conteudo[0].content.controls[1].controls.append(
                ft.Row([
                    criar_campo_view("Nome Cônjuge", c.get('nome_conjuge'), 300),
                    criar_campo_view("Data Casamento", formatar_data_br(c.get('data_casamento'))),
                ], wrap=True)
            )

        return ft.Column(conteudo, spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_documentos_view(self, c):
        """Cria o conteúdo da aba Documentos para visualização."""
        return ft.Column([
            criar_secao("Documentos Principais", [
                ft.Row([
                    criar_campo_view("CPF", formatar_cpf(c.get('cpf', ''))),
                    criar_campo_view("RG", c.get('rg')),
                    criar_campo_view("Órgão Emissor", c.get('orgao_emissor_rg')),
                    criar_campo_view("UF RG", c.get('uf_rg'), 80),
                    criar_campo_view("Data Emissão RG", formatar_data_br(c.get('data_emissao_rg'))),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("CTPS", c.get('carteira_profissional')),
                    criar_campo_view("Série", c.get('serie_carteira')),
                    criar_campo_view("UF CTPS", c.get('uf_carteira'), 80),
                    criar_campo_view("Data Emissão CTPS", formatar_data_br(c.get('data_emissao_carteira'))),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("PIS", c.get('pis')),
                    criar_campo_view("Data Cadastro PIS", formatar_data_br(c.get('data_cadastramento_pis'))),
                ], wrap=True),
            ]),
            criar_secao("Título de Eleitor", [
                ft.Row([
                    criar_campo_view("Título de Eleitor", c.get('titulo_eleitor')),
                    criar_campo_view("Zona", c.get('zona_eleitor'), 80),
                    criar_campo_view("Seção", c.get('secao_eleitor'), 80),
                ], wrap=True),
            ]),
            criar_secao("CNH e Reservista", [
                ft.Row([
                    criar_campo_view("CNH", c.get('habilitacao')),
                    criar_campo_view("Categoria CNH", c.get('tipo_cnh')),
                    criar_campo_view("Validade CNH", formatar_data_br(c.get('validade_cnh'))),
                    criar_campo_view("Reservista", c.get('reservista')),
                ], wrap=True),
            ]),
            criar_secao("Último Emprego", [
                ft.Row([
                    criar_campo_view("Empresa Anterior", c.get('empresa_ultimo_emprego'), 300),
                    criar_campo_view("CNPJ Anterior", c.get('cnpj_ultimo_emprego'), 180),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Admissão Anterior", formatar_data_br(c.get('data_admissao_ultimo'))),
                    criar_campo_view("Saída Anterior", formatar_data_br(c.get('data_saida_ultimo'))),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Primeiro Registro?", c.get('primeiro_registro')),
                    criar_campo_view("Últ. Contrib. Sindical", formatar_data_br(c.get('data_ultima_contribuicao_sindical'))),
                ], wrap=True),
            ]),
            criar_secao("Exame Médico", [
                ft.Row([
                    criar_campo_view("Data Exame", formatar_data_br(c.get('data_exame_medico'))),
                    criar_campo_view("Tipo de Exames", c.get('tipo_exames'), 250),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Médico", c.get('nome_medico'), 250),
                    criar_campo_view("CRM", c.get('crm')),
                    criar_campo_view("UF CRM", c.get('uf_crm'), 80),
                ], wrap=True),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_contrato_view(self, c, sim_nao):
        """Cria o conteúdo da aba Contrato para visualização."""
        return ft.Column([
            criar_secao("Dados do Contrato", [
                ft.Row([
                    criar_campo_view("Empresa", c.get('empresa_nome'), 300),
                    criar_campo_view("CNPJ Empresa", c.get('empresa_cnpj'), 180),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Admissão", formatar_data_br(c.get('data_admissao'))),
                    criar_campo_view("Função", c.get('funcao'), 200),
                    criar_campo_view("Departamento", c.get('departamento'), 200),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Salário", formatar_moeda(c.get('salario'))),
                    criar_campo_view("Forma Pagamento", c.get('forma_pagamento')),
                    criar_campo_view("Tipo Contrato", c.get('tipo_contrato')),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Prazo Experiência", f"{c.get('prazo_experiencia') or '-'} dias"),
                    criar_campo_view("Prorrogação", f"{c.get('prorrogacao') or '-'} dias"),
                ], wrap=True),
            ]),
            criar_secao("Horário de Trabalho", [
                ft.Row([
                    criar_campo_view("Horário de Trabalho", c.get('horario_trabalho'), 200),
                    criar_campo_view("Intervalo", c.get('intervalo')),
                    criar_campo_view("Dias de Trabalho", c.get('dias_trabalho'), 200),
                ], wrap=True),
            ]),
            criar_secao("Dados Bancários", [
                ft.Row([
                    criar_campo_view("Tipo Conta", c.get('tipo_conta')),
                    criar_campo_view("Banco", c.get('banco'), 200),
                    criar_campo_view("Agência", c.get('agencia')),
                    criar_campo_view("Conta", c.get('conta')),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Observações Banco", c.get('observacoes_banco'), 400),
                ], wrap=True),
            ]),
            criar_secao("Observações do Contrato", [
                ft.Text(c.get('observacoes_contrato') or "Nenhuma observação", size=13),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_beneficios_view(self, c, sim_nao, lista_dep):
        """Cria o conteúdo da aba Benefícios e Outros para visualização."""
        return ft.Column([
            criar_secao("Benefícios", [
                ft.Row([
                    criar_campo_view("Vale Transporte", sim_nao(c.get('vale_transporte'))),
                    criar_campo_view("VT Valor Diário", formatar_moeda(c.get('vt_valor_diario'))),
                    criar_campo_view("VT % Desconto", f"{c.get('vt_percentual_desconto') or 0}%"),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Vale Refeição", sim_nao(c.get('vale_refeicao'))),
                    criar_campo_view("VR Valor Diário", formatar_moeda(c.get('vr_valor_diario'))),
                    criar_campo_view("VR % Desconto", f"{c.get('vr_percentual_desconto') or 0}%"),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Vale Alimentação", sim_nao(c.get('vale_alimentacao'))),
                    criar_campo_view("VA Valor Diário", formatar_moeda(c.get('va_valor_diario'))),
                    criar_campo_view("VA % Desconto", f"{c.get('va_percentual_desconto') or 0}%"),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Assist. Médica", sim_nao(c.get('assistencia_medica'))),
                    criar_campo_view("AM Desconto", formatar_moeda(c.get('am_valor_desconto'))),
                    criar_campo_view("Assist. Odonto", sim_nao(c.get('assistencia_odontologica'))),
                    criar_campo_view("AO Desconto", formatar_moeda(c.get('ao_valor_desconto'))),
                ], wrap=True),
                ft.Row([
                    criar_campo_view("Seguro Vida", sim_nao(c.get('seguro_vida'))),
                    criar_campo_view("SV Desconto", formatar_moeda(c.get('sv_valor_desconto'))),
                    criar_campo_view("Adiantamento", sim_nao(c.get('adiantamento'))),
                    criar_campo_view("% Adiantamento", f"{c.get('percentual_adiantamento') or 0}%"),
                ], wrap=True),
            ]),
            criar_secao("Dependentes", lista_dep),
            criar_secao("Observações Gerais", [
                ft.Text(c.get('observacoes_gerais') or "Nenhuma observação", size=13),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_header(self):
        # Verificar se há foto do colaborador
        foto_path = self.colaborador.get('foto_path')
        if foto_path and os.path.exists(foto_path):
            foto_widget = ft.Image(src=foto_path, width=100, height=120, fit=ft.ImageFit.COVER, border_radius=8)
        else:
            foto_widget = ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=60, color=ft.Colors.GREY),
                width=100,
                height=120,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
            )

        status_atual = self.colaborador.get('status', 'ATIVO')
        status_color = COR_SUCESSO if status_atual == 'ATIVO' else COR_ERRO

        # Verificar se está na blocklist
        cpf_colaborador = self.colaborador.get('cpf', '')
        na_blocklist = db.verificar_blocklist(cpf_colaborador) if cpf_colaborador else []

        # Botão de alternar status
        btn_status_texto = "Inativar" if status_atual == 'ATIVO' else "Ativar"
        btn_status_cor = COR_ALERTA if status_atual == 'ATIVO' else COR_SUCESSO
        btn_status_icon = ft.Icons.PERSON_OFF if status_atual == 'ATIVO' else ft.Icons.PERSON

        # Verificar se é contrato de experiência para mostrar botão de renovar
        is_contrato_experiencia = self.colaborador.get('tipo_contrato') == 'Contrato de Experiência'

        # Obter status dos documentos para o contador
        status_docs = db.obter_status_documentos_colaborador(self.colaborador_id)
        docs_anexados = status_docs['completos']
        docs_total = status_docs['total_obrigatorios']

        # Cores das categorias
        COR_DADOS = "#3498db"      # Azul - Dados/Informações
        COR_GESTAO = "#e67e22"     # Laranja - Gestão de Pessoal
        COR_ACOES = "#7f8c8d"      # Cinza - Ações gerais

        # Linha 1: DADOS - Editar, Documentos, Histórico, [Análise - apenas admin]
        linha1_botoes = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FOLDER_SHARED, size=16, color=COR_DADOS),
                    ft.Text("DADOS", size=11, weight=ft.FontWeight.BOLD, color=COR_DADOS),
                ], spacing=5),
                margin=ft.margin.only(right=10),
            ),
            ft.ElevatedButton("Editar", icon=ft.Icons.EDIT,
                             on_click=self.toggle_edicao,
                             bgcolor=COR_DADOS, color="white"),
            ft.ElevatedButton(f"Documentos {docs_anexados}/{docs_total}", icon=ft.Icons.FOLDER_OPEN,
                             on_click=self._abrir_documentos,
                             bgcolor=COR_DADOS, color="white"),
            ft.ElevatedButton("Histórico", icon=ft.Icons.HISTORY,
                             on_click=self._abrir_historico,
                             bgcolor=COR_DADOS, color="white"),
        ]

        # Botão Análise - apenas para administradores
        if db.usuario_pode('gerenciar_usuarios'):
            linha1_botoes.append(
                ft.ElevatedButton("Análise", icon=ft.Icons.ANALYTICS,
                                 on_click=self._abrir_analise,
                                 bgcolor=COR_DADOS, color="white")
            )

        # Linha 2: GESTÃO - Férias, Localização, Tipo Contrato, [Renovar]
        linha2_botoes = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.MANAGE_ACCOUNTS, size=16, color=COR_GESTAO),
                    ft.Text("GESTÃO", size=11, weight=ft.FontWeight.BOLD, color=COR_GESTAO),
                ], spacing=5),
                margin=ft.margin.only(right=10),
            ),
            ft.ElevatedButton("Férias", icon=ft.Icons.BEACH_ACCESS,
                             on_click=self._abrir_ferias,
                             bgcolor=COR_GESTAO, color="white"),
            ft.ElevatedButton("Localização", icon=ft.Icons.LOCATION_ON,
                             on_click=self._abrir_localizacao,
                             bgcolor=COR_GESTAO, color="white"),
            ft.ElevatedButton("Tipo Contrato", icon=ft.Icons.DESCRIPTION,
                             on_click=self._alterar_tipo_contrato,
                             bgcolor=COR_GESTAO, color="white"),
        ]

        # Adicionar botão de renovar contrato se for contrato de experiência
        if is_contrato_experiencia:
            linha2_botoes.append(
                ft.ElevatedButton("Renovar", icon=ft.Icons.AUTORENEW,
                                 on_click=self._renovar_contrato,
                                 bgcolor=COR_GESTAO, color="white"),
            )

        # Linha 3: AÇÕES - Status, PDF, Voltar
        linha3_botoes = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, size=16, color=COR_ACOES),
                    ft.Text("AÇÕES", size=11, weight=ft.FontWeight.BOLD, color=COR_ACOES),
                ], spacing=5),
                margin=ft.margin.only(right=10),
            ),
            ft.ElevatedButton(btn_status_texto, icon=btn_status_icon,
                             on_click=self._alternar_status,
                             bgcolor=COR_ACOES, color="white"),
            ft.ElevatedButton("Ficha Registro (PDF)", icon=ft.Icons.PICTURE_AS_PDF,
                             on_click=self.gerar_pdf,
                             bgcolor=COR_ACOES, color="white"),
            ft.OutlinedButton("Voltar", icon=ft.Icons.ARROW_BACK,
                             on_click=self.voltar),
        ]

        return ft.Container(
            content=ft.Row([
                foto_widget,
                ft.Column([
                    ft.Text(self.colaborador.get('nome_completo', ''),
                           size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(f"CPF: {formatar_cpf(self.colaborador.get('cpf', ''))}", size=14),
                    ft.Text(f"{self.colaborador.get('funcao', '')} - {self.colaborador.get('departamento', '')}",
                           size=14, color=ft.Colors.GREY),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(status_atual, color="white", size=12),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            border_radius=4,
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.BLOCK, color="white", size=14),
                                ft.Text("BLOCKLIST", color="white", size=11, weight=ft.FontWeight.BOLD),
                            ], spacing=3),
                            bgcolor=COR_ERRO,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=4,
                            visible=len(na_blocklist) > 0,
                        ),
                    ], spacing=8),
                ], spacing=5, expand=True),
                ft.Column([
                    ft.Row(linha1_botoes, spacing=5),
                    ft.Row(linha2_botoes, spacing=5),
                    ft.Row(linha3_botoes, spacing=5),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20,
            bgcolor="white",
            border_radius=8,
            margin=ft.margin.only(bottom=10),
        )

    def _renovar_contrato(self, e):
        """Abre diálogo para renovar contrato de experiência."""
        from datetime import datetime, timedelta

        # Obter contrato atual
        contrato = db.obter_contrato_colaborador(self.colaborador_id)

        # Informações do contrato atual
        if contrato:
            data_inicio = contrato.get('data_inicio', '')
            prazo_inicial = contrato.get('prazo_inicial', 0)
            prorrogacao_atual = contrato.get('prorrogacao')
            data_fim_inicial = contrato.get('data_fim_inicial', '')
            data_fim_prorrogacao = contrato.get('data_fim_prorrogacao')

            # Determinar período atual
            hoje = datetime.now().date()
            fim_inicial_date = datetime.strptime(data_fim_inicial, '%Y-%m-%d').date() if data_fim_inicial else None

            if prorrogacao_atual and fim_inicial_date and hoje > fim_inicial_date:
                # Já passou do 1º período e tem prorrogação - está no 2º período
                periodo_atual = 2
            elif prorrogacao_atual:
                # Tem prorrogação mas ainda está no 1º período
                periodo_atual = 1
            else:
                # Não tem prorrogação
                periodo_atual = 1
        else:
            # Usar dados do colaborador
            data_inicio = self.colaborador.get('data_admissao', '')
            prazo_inicial = self.colaborador.get('prazo_experiencia', 45)
            prorrogacao_atual = self.colaborador.get('prorrogacao')
            periodo_atual = 2 if prorrogacao_atual else 1

        # Calcular máximo de prorrogação possível (90 - prazo_inicial)
        prazo_inicial_int = int(prazo_inicial or 0)
        prorrogacao_atual_int = int(prorrogacao_atual or 0)

        # Se prazo_inicial é 0, usar o valor do colaborador
        if prazo_inicial_int == 0:
            prazo_inicial_int = int(self.colaborador.get('prazo_experiencia') or 45)

        max_prorrogacao = 90 - prazo_inicial_int

        # Dias disponíveis = máximo - o que já tem de prorrogação
        dias_disponiveis = max_prorrogacao - prorrogacao_atual_int
        pode_renovar = dias_disponiveis > 0

        # Campos do formulário - valor padrão é o mínimo entre 45 e dias disponíveis
        valor_padrao = min(45, dias_disponiveis) if dias_disponiveis > 0 else 0
        dias_renovacao = ft.TextField(
            label=f"Dias de Prorrogação * (máx: {dias_disponiveis})",
            width=250,
            value=str(valor_padrao),
            hint_text=f"Máximo: {dias_disponiveis} dias",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Calcular data prevista de término
        info_container = ft.Container()

        def calcular_previsao(ev=None):
            try:
                dias = int(dias_renovacao.value) if dias_renovacao.value else 0
                if data_inicio and prazo_inicial:
                    inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                    # O dia de início conta como dia 1, então o fim é início + prazo - 1
                    fim_inicial = inicio + timedelta(days=int(prazo_inicial) - 1)

                    # Nova prorrogação total = atual + nova adição
                    nova_prorrog_total = prorrogacao_atual_int + dias
                    fim_prorrogacao = fim_inicial + timedelta(days=nova_prorrog_total)
                    dias_restantes = (fim_prorrogacao.date() - datetime.now().date()).days

                    # Total do contrato
                    total_contrato = int(prazo_inicial) + nova_prorrog_total
                    excede_limite = dias > dias_disponiveis

                    info_items = [
                        ft.Text(f"Data início do contrato: {formatar_data_br(data_inicio)}", size=13),
                        ft.Text(f"Prazo inicial: {prazo_inicial} dias", size=13),
                    ]

                    if prorrogacao_atual_int > 0:
                        info_items.append(ft.Text(f"Prorrogação atual: {prorrogacao_atual_int} dias", size=13))

                    info_items.extend([
                        ft.Divider(height=10),
                        ft.Text(f"Adicionar: +{dias} dias", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Prorrogação total: {nova_prorrog_total} dias", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Total do contrato: {total_contrato} dias", size=13,
                               weight=ft.FontWeight.BOLD,
                               color=COR_ERRO if excede_limite else COR_PRIMARIA),
                    ])

                    if excede_limite:
                        info_items.append(ft.Text(f"⚠ Excede o limite! Máximo: {dias_disponiveis} dias", size=13, color=COR_ERRO, weight=ft.FontWeight.BOLD))
                    else:
                        info_items.extend([
                            ft.Text(f"Novo término: {formatar_data_br(fim_prorrogacao.strftime('%Y-%m-%d'))}", size=13, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                            ft.Text(f"Dias restantes: {dias_restantes} dias", size=13, color=COR_SUCESSO if dias_restantes > 0 else COR_ERRO),
                        ])

                    info_container.content = ft.Column(info_items, spacing=5)
                    self.page.update()
            except:
                pass

        dias_renovacao.on_change = calcular_previsao
        calcular_previsao()  # Calcular inicialmente

        # Declarar dialog antes das funções para uso com nonlocal
        dialog = None

        def salvar_renovacao(ev):
            nonlocal dialog
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para editar dados."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            if not dias_renovacao.value:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Informe os dias de prorrogação!"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()
                return

            try:
                dias = int(dias_renovacao.value)
                if dias <= 0:
                    raise ValueError("Dias deve ser maior que zero")

                if not data_inicio or not prazo_inicial:
                    raise ValueError("Dados do contrato incompletos. Verifique a data de admissão e prazo de experiência.")

                # Validar limite
                if dias > dias_disponiveis:
                    raise ValueError(f"Máximo permitido: {dias_disponiveis} dias.")

                # Calcular prorrogação total (atual + nova adição)
                prorrog_total = prorrogacao_atual_int + dias
                total_contrato = int(prazo_inicial) + prorrog_total

                # Calcular novas datas
                # O dia de início conta como dia 1, então o fim é início + prazo - 1
                inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                fim_inicial = inicio + timedelta(days=int(prazo_inicial) - 1)
                # A prorrogação total começa no dia seguinte ao fim do período inicial
                fim_prorrogacao = fim_inicial + timedelta(days=prorrog_total)

                if contrato:
                    # Atualizar contrato existente
                    db.atualizar_contrato(contrato['id'], {
                        'prorrogacao': prorrog_total,
                        'data_fim_inicial': fim_inicial.strftime('%Y-%m-%d'),
                        'data_fim_prorrogacao': fim_prorrogacao.strftime('%Y-%m-%d'),
                    })
                else:
                    # Criar novo contrato na tabela
                    db.criar_contrato_experiencia(
                        self.colaborador_id,
                        data_inicio,
                        int(prazo_inicial),
                        prorrog_total
                    )

                # Atualizar dados do colaborador também
                db.atualizar_colaborador(self.colaborador_id, {
                    'prorrogacao': prorrog_total,
                    'prazo_experiencia': int(prazo_inicial)
                })

                # Registrar no histórico
                db.registrar_alteracao(
                    self.colaborador_id,
                    'prorrogacao_contrato',
                    str(prorrogacao_atual_int) if prorrogacao_atual_int else '0',
                    str(prorrog_total)
                )

                # Fechar o dialog
                if dialog:
                    dialog.open = False

                # Mostrar mensagem de sucesso
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Contrato renovado! Novo término: {formatar_data_br(fim_prorrogacao.strftime('%Y-%m-%d'))} (Total: {total_contrato} dias)"),
                    bgcolor=COR_SUCESSO
                )
                self.page.snack_bar.open = True
                self.page.update()

                # Recarregar a ficha completamente
                if self.on_voltar_callback:
                    self.on_voltar_callback(visualizar_id=self.colaborador_id)

            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {str(ex)}"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()

        def cancelar(ev):
            nonlocal dialog
            if dialog:
                dialog.open = False
            self.page.update()

        # Verificar se ainda pode renovar (limite de 90 dias)
        total_atual = int(prazo_inicial or 0) + prorrogacao_atual_int
        if not pode_renovar:
            conteudo = ft.Column([
                ft.Icon(ft.Icons.WARNING, size=50, color=COR_ALERTA),
                ft.Text("Limite de 90 dias atingido!", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("O contrato de experiência não pode exceder 90 dias.", size=14),
                ft.Text(f"Prazo inicial: {prazo_inicial} dias", size=13),
                ft.Text(f"Prorrogação atual: {prorrogacao_atual_int} dias", size=13),
                ft.Text(f"Total: {total_atual} dias", size=13, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            acoes = [ft.TextButton("Fechar", on_click=cancelar)]
        else:
            conteudo = ft.Column([
                ft.Text("Prorrogação do Contrato de Experiência", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                info_container,
                ft.Divider(height=10),
                dias_renovacao,
                ft.Text(f"* O contrato pode ter no máximo 90 dias. Disponível: {dias_disponiveis} dias.", size=11, italic=True, color=ft.Colors.GREY),
            ], spacing=10)
            acoes = [
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Renovar", on_click=salvar_renovacao, bgcolor=COR_SUCESSO, color="white"),
            ]

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Renovar Contrato"),
            content=ft.Container(content=conteudo, width=400),
            actions=acoes,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _alternar_status(self, e):
        """Alterna o status do colaborador entre ATIVO e INATIVO."""
        status_atual = self.colaborador.get('status', 'ATIVO')
        novo_status = 'INATIVO' if status_atual == 'ATIVO' else 'ATIVO'

        # Se está ativando, processo simples
        if novo_status == 'ATIVO':
            self._ativar_colaborador_simples()
            return

        # Se está inativando, mostrar diálogo com justificativas
        self._mostrar_dialog_inativacao()

    def _ativar_colaborador_simples(self):
        """Ativa um colaborador sem necessidade de justificativa."""
        dialog = None

        def confirmar(ev):
            nonlocal dialog
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para editar dados."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            db.atualizar_colaborador(self.colaborador_id, {
                'status': 'ATIVO',
                'motivo_inativacao': None,
                'submotivo_inativacao': None,
                'data_inativacao': None
            })
            db.registrar_alteracao(self.colaborador_id, 'status', 'INATIVO', 'ATIVO')
            if dialog:
                dialog.open = False
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Colaborador ativado com sucesso!"),
                bgcolor=COR_SUCESSO
            )
            self.page.snack_bar.open = True
            self.page.update()
            if self.on_voltar_callback:
                self.on_voltar_callback(visualizar_id=self.colaborador_id)

        def cancelar(ev):
            nonlocal dialog
            if dialog:
                dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Ativar Colaborador"),
            content=ft.Text(f"Deseja realmente ativar o colaborador {self.colaborador.get('nome_completo')}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Confirmar", on_click=confirmar, bgcolor=COR_SUCESSO, color="white"),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _mostrar_dialog_inativacao(self):
        """Mostra o diálogo de inativação com justificativas em cascata."""

        # Definições dos motivos e submotivos com descrições
        MOTIVOS_INATIVACAO = {
            'Suspensão do Contrato de Trabalho': {
                'descricao': 'Situação em que o contrato de trabalho fica temporariamente paralisado, sem pagamento de salário nem prestação de serviço.',
                'submotivos': {
                    'Afastamento por doença ou acidente de trabalho (após o 16º dia)': 'O empregado passa a receber o benefício previdenciário (auxílio-doença ou auxílio-acidente) pelo INSS. A empresa é responsável apenas pelos primeiros 15 dias de afastamento.',
                    'Aposentadoria por invalidez': 'Causa de suspensão que perdura enquanto durar a condição de invalidez.',
                    'Serviço militar obrigatório': 'Afastamento para cumprimento do dever militar.',
                    'Licença não remunerada (LSV)': 'Acordo mútuo entre empregador e empregado, formalizado por escrito, para um afastamento temporário sem pagamento de salário.',
                    'Suspensão disciplinar': 'Penalidade aplicada pelo empregador em caso de falta grave do funcionário, seguindo as regras de hierarquia de punições (advertência, suspensão e, em último caso, justa causa).',
                    'Participação em greve': 'A suspensão dos contratos ocorre durante a paralisação legítima, com as condições de pagamento dos dias parados geralmente negociadas em acordo ou dissídio coletivo.',
                }
            },
            'Interrupção do Contrato de Trabalho': {
                'descricao': 'Situação em que o empregado não trabalha, mas continua recebendo salário normalmente.',
                'submotivos': {
                    'Licença-maternidade e paternidade': 'Afastamentos legais remunerados.',
                    'Faltas justificadas pela CLT': 'Diversas situações previstas em lei, como licença óbito (até 2 dias), casamento (até 3 dias), doação de sangue (1 dia a cada 12 meses), alistamento eleitoral, entre outras.',
                    'Afastamento por doença ou acidente (até o 15º dia)': 'A empresa remunera o período.',
                }
            },
            'Rescisão (Desligamento)': {
                'descricao': 'Término definitivo do vínculo empregatício entre empresa e funcionário.',
                'submotivos': {
                    'Demissão sem justa causa': 'Iniciativa do empregador sem um motivo grave, exigindo aviso prévio e pagamento de todas as verbas rescisórias.',
                    'Demissão por justa causa': 'Iniciativa do empregador devido a uma falta grave do empregado (como desídia, insubordinação, abandono de emprego, etc., previstas no Art. 482 da CLT), resultando em menos direitos rescisórios.',
                    'Pedido de demissão': 'Iniciativa do empregado.',
                    'Rescisão indireta': 'Ocorre quando o empregador comete uma falta grave, e o funcionário "demite" a empresa judicialmente.',
                }
            },
        }

        dialog = None

        # Dropdown do motivo principal
        motivo_dropdown = ft.Dropdown(
            label="Motivo da Inativação *",
            width=400,
            options=[ft.dropdown.Option(m) for m in MOTIVOS_INATIVACAO.keys()],
        )

        # Dropdown do submotivo (inicialmente vazio)
        submotivo_dropdown = ft.Dropdown(
            label="Especificação do Motivo *",
            width=400,
            options=[],
            visible=False,
        )

        # Container para descrição do motivo
        descricao_motivo = ft.Container(
            content=ft.Text("", size=12, italic=True, color=ft.Colors.GREY_700),
            padding=ft.padding.symmetric(vertical=5),
            visible=False,
        )

        # Container para descrição do submotivo
        descricao_submotivo = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("", size=12, color=ft.Colors.BLUE_900),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=10,
                    border_radius=8,
                )
            ]),
            visible=False,
        )

        def on_motivo_change(ev):
            motivo_selecionado = ev.control.value
            if motivo_selecionado and motivo_selecionado in MOTIVOS_INATIVACAO:
                info_motivo = MOTIVOS_INATIVACAO[motivo_selecionado]

                # Atualizar descrição do motivo
                descricao_motivo.content.value = info_motivo['descricao']
                descricao_motivo.visible = True

                # Atualizar opções do submotivo
                submotivos = info_motivo['submotivos']
                submotivo_dropdown.options = [ft.dropdown.Option(s) for s in submotivos.keys()]
                submotivo_dropdown.value = None
                submotivo_dropdown.visible = True

                # Limpar descrição do submotivo
                descricao_submotivo.visible = False
            else:
                submotivo_dropdown.options = []
                submotivo_dropdown.visible = False
                descricao_motivo.visible = False
                descricao_submotivo.visible = False

            self.page.update()

        def on_submotivo_change(ev):
            motivo_selecionado = motivo_dropdown.value
            submotivo_selecionado = ev.control.value

            if motivo_selecionado and submotivo_selecionado:
                info_motivo = MOTIVOS_INATIVACAO.get(motivo_selecionado, {})
                submotivos = info_motivo.get('submotivos', {})
                descricao = submotivos.get(submotivo_selecionado, '')

                if descricao:
                    descricao_submotivo.content.controls[0].content.value = descricao
                    descricao_submotivo.visible = True
                else:
                    descricao_submotivo.visible = False
            else:
                descricao_submotivo.visible = False

            self.page.update()

        motivo_dropdown.on_change = on_motivo_change
        submotivo_dropdown.on_change = on_submotivo_change

        # Checkbox para adicionar à Block-List
        checkbox_blocklist = ft.Checkbox(
            label="Adicionar à Block-List",
            value=False,
        )

        # Campo de justificativa para Block-List (inicialmente invisível)
        justificativa_blocklist = ft.TextField(
            label="Justificativa para Block-List *",
            width=400,
            multiline=True,
            min_lines=2,
            max_lines=4,
            visible=False,
            hint_text="Descreva o motivo para adicionar este colaborador à Block-List...",
        )

        # Container para a seção de Block-List
        container_blocklist = ft.Container(
            content=ft.Column([
                ft.Divider(height=15),
                ft.Row([
                    ft.Icon(ft.Icons.BLOCK, size=18, color=COR_ERRO),
                    ft.Text("Opções de Block-List", weight=ft.FontWeight.BOLD, size=13),
                ], spacing=5),
                checkbox_blocklist,
                justificativa_blocklist,
            ], spacing=8),
            padding=ft.padding.only(top=5),
        )

        def on_checkbox_blocklist_change(ev):
            justificativa_blocklist.visible = ev.control.value
            self.page.update()

        checkbox_blocklist.on_change = on_checkbox_blocklist_change

        def confirmar_inativacao(ev):
            nonlocal dialog
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para editar dados."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            motivo = motivo_dropdown.value
            submotivo = submotivo_dropdown.value
            adicionar_blocklist = checkbox_blocklist.value
            justificativa = justificativa_blocklist.value

            if not motivo or not submotivo:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Selecione o motivo e a especificação!"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Validar justificativa se checkbox marcado
            if adicionar_blocklist and not justificativa:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Informe a justificativa para adicionar à Block-List!"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            try:
                from datetime import datetime
                data_hoje = datetime.now().strftime('%Y-%m-%d')

                # Atualizar colaborador
                dados_atualizacao = {
                    'status': 'INATIVO',
                    'motivo_inativacao': motivo,
                    'submotivo_inativacao': submotivo,
                    'data_inativacao': data_hoje,
                }

                # Se for rescisão, atualizar data de desligamento
                if motivo == 'Rescisão (Desligamento)':
                    dados_atualizacao['data_desligamento'] = data_hoje
                    dados_atualizacao['motivo_desligamento'] = submotivo

                # Adicionar à blocklist apenas se checkbox marcado
                if adicionar_blocklist:
                    db.adicionar_blocklist({
                        'cpf': self.colaborador.get('cpf'),
                        'nome': self.colaborador.get('nome_completo'),
                        'empresa_id': self.colaborador.get('empresa_id'),
                        'data_admissao': self.colaborador.get('data_admissao'),
                        'data_desligamento': data_hoje,
                        'motivo_desligamento': submotivo,
                        'observacoes': justificativa,  # Usar a justificativa escrita pelo usuário
                    })

                db.atualizar_colaborador(self.colaborador_id, dados_atualizacao)

                # Registrar no histórico
                db.registrar_alteracao(self.colaborador_id, 'status', 'ATIVO', 'INATIVO')
                db.registrar_alteracao(self.colaborador_id, 'motivo_inativacao', None, motivo)
                db.registrar_alteracao(self.colaborador_id, 'submotivo_inativacao', None, submotivo)

                if dialog:
                    dialog.open = False

                msg = "Colaborador inativado com sucesso!"
                if adicionar_blocklist:
                    msg += " Adicionado à Block-List."

                self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=COR_SUCESSO)
                self.page.snack_bar.open = True
                self.page.update()

                if self.on_voltar_callback:
                    self.on_voltar_callback(visualizar_id=self.colaborador_id)

            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {str(ex)}"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()

        def cancelar(ev):
            nonlocal dialog
            if dialog:
                dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON_OFF, color=COR_ALERTA, size=28),
                ft.Text("Inativar Colaborador"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Colaborador: {self.colaborador.get('nome_completo', '')}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"CPF: {formatar_cpf(self.colaborador.get('cpf', ''))}", size=13, color=ft.Colors.GREY_700),
                    ft.Divider(height=20),
                    ft.Text("Selecione o motivo da inativação:", size=14),
                    motivo_dropdown,
                    descricao_motivo,
                    submotivo_dropdown,
                    descricao_submotivo,
                    container_blocklist,
                ], spacing=8, scroll=ft.ScrollMode.AUTO),
                width=480,
                height=550,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Inativar", on_click=confirmar_inativacao, bgcolor=COR_ALERTA, color="white"),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _alterar_tipo_contrato(self, e):
        """Abre diálogo para alterar o tipo de contrato do colaborador."""
        from .constantes import TIPOS_CONTRATO

        tipo_atual = self.colaborador.get('tipo_contrato', '')

        # Criar dropdown com tipos de contrato
        tipo_contrato_dropdown = ft.Dropdown(
            label="Tipo de Contrato",
            width=300,
            value=tipo_atual,
            options=[ft.dropdown.Option(t) for t in TIPOS_CONTRATO],
        )

        # Container para campos de experiência (visível apenas se for contrato de experiência)
        prazo_exp = ft.TextField(
            label="Prazo Experiência (dias)",
            width=150,
            value=str(self.colaborador.get('prazo_experiencia', '')) if self.colaborador.get('prazo_experiencia') else '',
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        campos_experiencia = ft.Container(
            content=ft.Column([
                ft.Text("Dados do Contrato de Experiência:", weight=ft.FontWeight.BOLD, size=13),
                prazo_exp,
            ], spacing=10),
            visible=tipo_atual == 'Contrato de Experiência',
            padding=ft.padding.only(top=10),
        )

        def on_tipo_change(ev):
            campos_experiencia.visible = ev.control.value == 'Contrato de Experiência'
            self.page.update()

        tipo_contrato_dropdown.on_change = on_tipo_change

        dialog = None

        def salvar_tipo_contrato(ev):
            nonlocal dialog
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para editar dados."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            novo_tipo = tipo_contrato_dropdown.value

            if not novo_tipo:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um tipo de contrato!"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()
                return

            try:
                # Obter dados antigos para o histórico
                dados_antigos = dict(self.colaborador)

                # Preparar dados para atualização
                dados_atualizacao = {'tipo_contrato': novo_tipo}

                # Se está mudando DE contrato de experiência PARA outro tipo (ex: CLT)
                if tipo_atual == 'Contrato de Experiência' and novo_tipo != 'Contrato de Experiência':
                    # Finalizar o contrato de experiência
                    db.finalizar_contrato_experiencia(self.colaborador_id)
                    # Limpar campos de experiência
                    dados_atualizacao['prazo_experiencia'] = None
                    dados_atualizacao['prorrogacao'] = None

                # Se está mudando PARA contrato de experiência
                elif novo_tipo == 'Contrato de Experiência' and tipo_atual != 'Contrato de Experiência':
                    prazo = int(prazo_exp.value) if prazo_exp.value else 45
                    dados_atualizacao['prazo_experiencia'] = prazo

                    # Criar contrato de experiência se tiver data de admissão
                    data_admissao = self.colaborador.get('data_admissao')
                    if data_admissao:
                        db.criar_contrato_experiencia(self.colaborador_id, data_admissao, prazo)

                # Atualizar colaborador
                db.atualizar_colaborador(self.colaborador_id, dados_atualizacao)

                # Registrar alterações no histórico
                db.registrar_alteracoes_colaborador(self.colaborador_id, dados_atualizacao, dados_antigos)

                # Fechar dialog
                if dialog:
                    dialog.open = False

                # Mensagem de sucesso
                msg = f"Tipo de contrato alterado para: {novo_tipo}"
                if tipo_atual == 'Contrato de Experiência' and novo_tipo != 'Contrato de Experiência':
                    msg += " (Contrato de experiência finalizado)"

                self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=COR_SUCESSO)
                self.page.snack_bar.open = True
                self.page.update()

                # Recarregar a ficha
                if self.on_voltar_callback:
                    self.on_voltar_callback(visualizar_id=self.colaborador_id)

            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {str(ex)}"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()

        def cancelar(ev):
            nonlocal dialog
            if dialog:
                dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=COR_PRIMARIA),
                ft.Text("Alterar Tipo de Contrato"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Colaborador: {self.colaborador.get('nome_completo', '')}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Tipo atual: {tipo_atual or 'Não definido'}", size=13, color=ft.Colors.GREY_700),
                    ft.Divider(height=20),
                    tipo_contrato_dropdown,
                    campos_experiencia,
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text(
                            "Atenção: Ao mudar de 'Contrato de Experiência' para outro tipo, "
                            "o funcionário será removido da lista de contratos de experiência.",
                            size=12,
                            italic=True,
                            color=COR_ALERTA,
                        ),
                        visible=tipo_atual == 'Contrato de Experiência',
                    ),
                ], spacing=10),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Salvar", on_click=salvar_tipo_contrato, bgcolor=COR_SUCESSO, color="white"),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _abrir_localizacao(self, e):
        """Abre diálogo para gerenciar localização do colaborador."""
        from datetime import datetime

        # Obter localização atual e histórico
        localizacao_atual = db.obter_localizacao_atual(self.colaborador_id)
        historico_localizacoes = db.listar_localizacoes_colaborador(self.colaborador_id)
        locais_cadastrados = db.listar_locais_cadastrados()

        # Lista de UFs
        UFS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
               'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

        def fechar(ev):
            dialog.open = False
            self.page.update()

        def atribuir_nova(ev):
            """Abre sub-diálogo para atribuir nova localização."""
            local_nome = ft.TextField(label="Local/Empresa *", width=350, hint_text="Nome do local onde está alocado")
            cidade = ft.TextField(label="Cidade", width=200)
            uf = ft.Dropdown(
                label="UF",
                width=80,
                options=[ft.dropdown.Option(u) for u in UFS],
            )
            data_inicio = ft.TextField(
                label="Data Início *",
                width=120,
                hint_text="DD/MM/AAAA",
                value=datetime.now().strftime('%d/%m/%Y')
            )
            observacoes = ft.TextField(label="Observações", width=350, multiline=True, min_lines=1, max_lines=2)

            # Autocomplete para locais já cadastrados
            sugestoes_container = ft.Column([], spacing=2)

            def on_local_change(e):
                texto = local_nome.value.lower() if local_nome.value else ''
                sugestoes_container.controls.clear()
                if texto and len(texto) >= 2:
                    sugestoes = [l for l in locais_cadastrados if texto in l.lower()][:5]
                    for s in sugestoes:
                        sugestoes_container.controls.append(
                            ft.TextButton(
                                s,
                                on_click=lambda ev, nome=s: selecionar_sugestao(nome),
                                style=ft.ButtonStyle(padding=5),
                            )
                        )
                self.page.update()

            def selecionar_sugestao(nome):
                local_nome.value = nome
                sugestoes_container.controls.clear()
                self.page.update()

            local_nome.on_change = on_local_change

            def salvar_localizacao(ev2):
                if not local_nome.value or not data_inicio.value:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Preencha os campos obrigatórios!"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                try:
                    # Converter data para formato do banco
                    data_inicio_db = formatar_data_db(data_inicio.value)

                    db.atribuir_localizacao(
                        self.colaborador_id,
                        local_nome.value,
                        cidade.value,
                        uf.value,
                        data_inicio_db,
                        observacoes.value
                    )

                    # Registrar no histórico
                    loc_texto = f"{local_nome.value}"
                    if cidade.value or uf.value:
                        loc_texto += f" - {cidade.value or ''}/{uf.value or ''}"
                    db.registrar_alteracao(
                        self.colaborador_id,
                        'localizacao',
                        localizacao_atual.get('local_nome') if localizacao_atual else None,
                        loc_texto
                    )

                    sub_dialog.open = False
                    dialog.open = False
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Localização atribuída com sucesso!"),
                        bgcolor=COR_SUCESSO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

                    # Reabrir diálogo com dados atualizados
                    self._abrir_localizacao(None)

                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Erro: {str(ex)}"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

            def cancelar_sub(ev2):
                sub_dialog.open = False
                self.page.update()

            sub_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Atribuir Nova Localização"),
                content=ft.Container(
                    content=ft.Column([
                        local_nome,
                        sugestoes_container,
                        ft.Row([cidade, uf], spacing=10),
                        data_inicio,
                        observacoes,
                    ], spacing=10),
                    width=380,
                    height=280,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_sub),
                    ft.ElevatedButton("Salvar", on_click=salvar_localizacao, bgcolor=COR_SUCESSO, color="white"),
                ],
            )

            self.page.overlay.append(sub_dialog)
            sub_dialog.open = True
            self.page.update()

        # Construir exibição da localização atual
        if localizacao_atual:
            loc_atual_widget = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, color=COR_SUCESSO, size=24),
                        ft.Text("Localização Atual", weight=ft.FontWeight.BOLD, size=16),
                    ], spacing=10),
                    ft.Text(localizacao_atual.get('local_nome', ''), size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{localizacao_atual.get('cidade', '') or ''}/{localizacao_atual.get('uf', '') or ''}", size=13),
                    ft.Text(f"Desde: {formatar_data_br(localizacao_atual.get('data_inicio', ''))}", size=12, color=ft.Colors.GREY_700),
                    ft.Text(localizacao_atual.get('observacoes', '') or '', size=11, italic=True, color=ft.Colors.GREY_600) if localizacao_atual.get('observacoes') else ft.Container(),
                ], spacing=5),
                padding=15,
                bgcolor=ft.Colors.GREEN_50,
                border=ft.border.all(1, COR_SUCESSO),
                border_radius=8,
            )
        else:
            loc_atual_widget = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCATION_OFF, color=ft.Colors.GREY, size=40),
                    ft.Text("Nenhuma localização atribuída", italic=True, color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
                alignment=ft.alignment.center,
            )

        # Construir histórico de localizações
        historico_widgets = []
        for loc in historico_localizacoes:
            # Pular a localização atual no histórico
            if loc.get('data_fim') is None:
                continue

            historico_widgets.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(loc.get('local_nome', ''), weight=ft.FontWeight.BOLD, size=13),
                            ft.Text(f"{loc.get('cidade', '') or ''}/{loc.get('uf', '') or ''}", size=11),
                        ], expand=True, spacing=2),
                        ft.Column([
                            ft.Text(f"{formatar_data_br(loc.get('data_inicio', ''))} a {formatar_data_br(loc.get('data_fim', ''))}", size=11, color=ft.Colors.GREY_700),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END),
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=6,
                    margin=ft.margin.only(bottom=5),
                )
            )

        if not historico_widgets:
            historico_widgets.append(
                ft.Text("Nenhum histórico de localizações anteriores.", italic=True, color=ft.Colors.GREY, size=12)
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color="#e67e22", size=28),
                ft.Text(f"Localização - {self.colaborador.get('nome_completo', '')}"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    loc_atual_widget,
                    ft.Divider(height=20),
                    ft.Text("Histórico de Localizações", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(
                        content=ft.Column(historico_widgets, scroll=ft.ScrollMode.AUTO),
                        height=200,
                    ),
                ], spacing=10),
                width=500,
                height=450,
            ),
            actions=[
                ft.ElevatedButton("Atribuir Nova", icon=ft.Icons.ADD_LOCATION, on_click=atribuir_nova, bgcolor="#e67e22", color="white"),
                ft.TextButton("Fechar", on_click=fechar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _abrir_historico(self, e):
        """Abre diálogo com o histórico de alterações do colaborador."""
        historico = db.listar_historico_colaborador(self.colaborador_id)

        def fechar(ev):
            dialog.open = False
            self.page.update()

        # Construir lista de alterações
        lista_alteracoes = []

        if not historico:
            lista_alteracoes.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=40, color=ft.Colors.GREY),
                        ft.Text("Nenhuma alteração registrada.", italic=True, color=ft.Colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=30,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for h in historico:
                campo_legivel = db.obter_nome_campo_legivel(h.get('campo', ''))
                valor_anterior = h.get('valor_anterior') or '(vazio)'
                valor_novo = h.get('valor_novo') or '(vazio)'
                data_str = h.get('data_alteracao', '')

                # Formatar data
                try:
                    data_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                    data_formatada = data_obj.strftime('%d/%m/%Y às %H:%M:%S')
                except:
                    data_formatada = data_str

                lista_alteracoes.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.EDIT_NOTE, size=18, color=COR_SECUNDARIA),
                                ft.Text(campo_legivel, weight=ft.FontWeight.BOLD, size=14),
                            ], spacing=5),
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(valor_anterior, size=12),
                                    bgcolor=ft.Colors.RED_50,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=4,
                                ),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=ft.Colors.GREY),
                                ft.Container(
                                    content=ft.Text(valor_novo, size=12),
                                    bgcolor=ft.Colors.GREEN_50,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=4,
                                ),
                            ], spacing=10, wrap=True),
                            ft.Text(data_formatada, size=11, color=ft.Colors.GREY_600),
                        ], spacing=5),
                        padding=12,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                        margin=ft.margin.only(bottom=8),
                    )
                )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.HISTORY, color="#8e44ad", size=28),
                ft.Text("Histórico de Alterações"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Colaborador: {self.colaborador.get('nome_completo', '')}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"CPF: {formatar_cpf(self.colaborador.get('cpf', ''))}", size=13, color=ft.Colors.GREY_700),
                    ft.Divider(height=15),
                    ft.Container(
                        content=ft.Column(lista_alteracoes, scroll=ft.ScrollMode.AUTO),
                        height=550,
                    ),
                ], spacing=5),
                width=650,
            ),
            actions=[ft.ElevatedButton("Fechar", on_click=fechar, bgcolor=COR_SECUNDARIA, color="white")],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _abrir_analise(self, e):
        """Abre diálogo de análise individual do colaborador."""
        dialog = AnaliseColaboradorDialog(self.page, self.colaborador_id)
        dialog.mostrar()

    def _abrir_ferias(self, e):
        """Abre diálogo para gerenciar férias do colaborador."""
        # Limpar diálogos fechados do overlay para evitar acúmulo
        dialogos_fechados = [o for o in self.page.overlay if hasattr(o, 'open') and not o.open]
        for d in dialogos_fechados:
            self.page.overlay.remove(d)

        ferias_lista = db.listar_ferias_colaborador(self.colaborador_id)

        def fechar(ev):
            dialog.open = False
            self.page.update()

        def registrar_ferias(ev, ferias_id, periodo_aquisitivo_fim, periodo_concessivo_limite):
            """Abre sub-diálogo para registrar período de férias."""
            from datetime import datetime, timedelta

            # Calcular início do período concessivo (dia seguinte ao fim do aquisitivo)
            periodo_concessivo_inicio = datetime.strptime(periodo_aquisitivo_fim, '%Y-%m-%d') + timedelta(days=1)
            periodo_concessivo_fim = datetime.strptime(periodo_concessivo_limite, '%Y-%m-%d')

            data_inicio = ft.TextField(label="Data Início *", width=130, hint_text="DD/MM/AAAA")
            data_fim = ft.TextField(label="Data Fim *", width=130, hint_text="DD/MM/AAAA")
            dias = ft.TextField(label="Dias *", width=80, value="30", keyboard_type=ft.KeyboardType.NUMBER)
            abono = ft.Checkbox(label="Abono Pecuniário (venda de dias)", value=False)
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
                # Se tem data fim, calcular dias; senão, se tem dias, calcular data fim
                if data_fim.value:
                    calcular_dias_entre_datas()
                elif dias.value:
                    calcular_data_fim_por_dias()
                # Validar período concessivo
                validar_periodo_concessivo()

            def on_data_fim_change(e):
                calcular_dias_entre_datas()

            def on_dias_change(e):
                calcular_data_fim_por_dias()

            data_inicio.on_change = on_data_inicio_change
            data_fim.on_change = on_data_fim_change
            dias.on_change = on_dias_change

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

                if not data_inicio.value or not data_fim.value or not dias.value:
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
                    dias_int = int(dias.value)
                    data_inicio_db = formatar_data_db(data_inicio.value)
                    data_fim_db = formatar_data_db(data_fim.value)

                    # Montar observações com justificativa se houver
                    observacoes_final = obs.value or ""
                    if justificativa.visible and justificativa.value.strip():
                        observacoes_final = f"[FÉRIAS ANTECIPADAS] Justificativa: {justificativa.value.strip()}" + (f"\n{obs.value}" if obs.value else "")
                    elif aviso_atraso.visible:
                        observacoes_final = f"[FÉRIAS APÓS PERÍODO CONCESSIVO]" + (f"\n{obs.value}" if obs.value else "")

                    db.registrar_gozo_ferias(
                        ferias_id, data_inicio_db, data_fim_db,
                        dias_int, abono.value, observacoes_final
                    )

                    # Registrar no histórico
                    db.registrar_alteracao(
                        self.colaborador_id,
                        'ferias_registradas',
                        None,
                        f"{data_inicio.value} a {data_fim.value} ({dias_int} dias)"
                    )

                    sub_dialog.open = False
                    dialog.open = False
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Férias registradas com sucesso!"), bgcolor=COR_SUCESSO)
                    self.page.snack_bar.open = True
                    self.page.update()

                    # Reabrir o diálogo de férias com os dados atualizados
                    self._abrir_ferias(None)
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {str(ex)}"), bgcolor=COR_ERRO)
                    self.page.snack_bar.open = True
                    self.page.update()

            def cancelar_sub(ev2):
                sub_dialog.open = False
                self.page.update()

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
                        justificativa,
                        aviso_atraso,
                        obs,
                    ], spacing=10),
                    width=420,
                    height=220,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_sub),
                    ft.ElevatedButton("Salvar", on_click=salvar_periodo, bgcolor=COR_SUCESSO, color="white"),
                ],
            )

            self.page.overlay.append(sub_dialog)
            sub_dialog.open = True
            self.page.update()

        # Construir lista de períodos
        lista_periodos = []
        for f in ferias_lista:
            periodo_inicio = formatar_data_br(f.get('periodo_aquisitivo_inicio', ''))
            periodo_fim = formatar_data_br(f.get('periodo_aquisitivo_fim', ''))
            limite = formatar_data_br(f.get('periodo_concessivo_limite', ''))
            status_f = f.get('status', 'PENDENTE')
            dias_restantes = f.get('dias_direito', 30) - f.get('dias_gozados', 0) - f.get('dias_vendidos', 0)

            # Calcular início do período concessivo (dia seguinte ao fim do aquisitivo)
            try:
                from datetime import timedelta
                periodo_aquisitivo_fim_dt = datetime.strptime(f.get('periodo_aquisitivo_fim', ''), '%Y-%m-%d')
                periodo_concessivo_inicio_dt = periodo_aquisitivo_fim_dt + timedelta(days=1)
                periodo_concessivo_inicio = periodo_concessivo_inicio_dt.strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                periodo_concessivo_inicio = ''

            # Verificar se ainda está no período aquisitivo
            hoje = datetime.now().date()
            try:
                periodo_fim_dt = datetime.strptime(f.get('periodo_aquisitivo_fim', ''), '%Y-%m-%d').date()
                ainda_em_aquisicao = hoje <= periodo_fim_dt
            except (ValueError, TypeError):
                ainda_em_aquisicao = False

            # Determinar cor do status
            if status_f == 'CONCLUIDO':
                cor_status = COR_SUCESSO
            elif ainda_em_aquisicao:
                cor_status = COR_SECUNDARIA  # Azul para período aquisitivo
            elif dias_restantes > 0:
                cor_status = COR_ALERTA
            else:
                cor_status = COR_ERRO

            # Texto do status
            if ainda_em_aquisicao:
                status_texto = "EM AQUISIÇÃO"
            else:
                status_texto = status_f

            # Determinar se pode registrar férias
            pode_registrar = not ainda_em_aquisicao and status_f != 'CONCLUIDO'

            # Tooltip do botão
            if ainda_em_aquisicao:
                tooltip_btn = f"Período aquisitivo ainda não concluído (termina em {periodo_fim})"
            elif status_f == 'CONCLUIDO':
                tooltip_btn = "Férias já concluídas"
            else:
                tooltip_btn = "Registrar férias"

            # Listar períodos gozados
            periodos_gozados = db.listar_periodos_ferias_gozados(f['id'])
            gozados_widgets = []
            for pg in periodos_gozados:
                tipo = "Abono" if pg.get('abono_pecuniario') else "Gozo"
                obs_pg = pg.get('observacoes', '') or ''

                # Verificar se tem marcação especial
                cor_obs = None
                if '[FÉRIAS ANTECIPADAS]' in obs_pg:
                    cor_obs = COR_ALERTA
                elif '[FÉRIAS APÓS PERÍODO CONCESSIVO]' in obs_pg:
                    cor_obs = COR_ERRO

                gozados_widgets.append(
                    ft.Text(f"  • {formatar_data_br(pg.get('data_inicio'))} a {formatar_data_br(pg.get('data_fim'))} ({pg.get('dias')} dias - {tipo})", size=12)
                )

                # Mostrar observações/justificativa se houver
                if obs_pg:
                    gozados_widgets.append(
                        ft.Text(f"    {obs_pg}", size=11, italic=True, color=cor_obs if cor_obs else ft.Colors.GREY_700)
                    )

            # Mensagem informativa se ainda em aquisição
            info_aquisicao = []
            if ainda_em_aquisicao:
                dias_faltam = (periodo_fim_dt - hoje).days
                info_aquisicao.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=COR_SECUNDARIA),
                            ft.Text(f"Faltam {dias_faltam} dias para completar o período aquisitivo", size=11, color=COR_SECUNDARIA, italic=True),
                        ], spacing=5),
                        margin=ft.margin.only(top=5),
                    )
                )

            lista_periodos.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"Período Aquisitivo: {periodo_inicio} a {periodo_fim}", size=12),
                                ft.Text(f"Período Concessivo: {periodo_concessivo_inicio} a {limite}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"Dias: {f.get('dias_direito', 30)} | Gozados: {f.get('dias_gozados', 0)} | Vendidos: {f.get('dias_vendidos', 0)} | Restantes: {dias_restantes}", size=12),
                            ], expand=True),
                            ft.Container(
                                content=ft.Text(status_texto, color="white", size=11),
                                bgcolor=cor_status,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=4,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE,
                                icon_color=COR_SECUNDARIA if pode_registrar else ft.Colors.GREY_400,
                                tooltip=tooltip_btn,
                                on_click=lambda ev, fid=f['id'], paf=f.get('periodo_aquisitivo_fim'), pcl=f.get('periodo_concessivo_limite'): registrar_ferias(ev, fid, paf, pcl),
                                disabled=not pode_registrar,
                            ),
                        ]),
                        ft.Column(info_aquisicao) if info_aquisicao else ft.Container(),
                        ft.Column(gozados_widgets) if gozados_widgets else ft.Container(),
                    ], spacing=5),
                    padding=10,
                    border=ft.border.all(1, cor_status if ainda_em_aquisicao else ft.Colors.GREY_300),
                    border_radius=8,
                    margin=ft.margin.only(bottom=10),
                )
            )

        if not lista_periodos:
            lista_periodos.append(ft.Text("Nenhum período de férias registrado.", italic=True, color=ft.Colors.GREY))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Férias - {self.colaborador.get('nome_completo')}"),
            content=ft.Container(
                content=ft.Column(lista_periodos, scroll=ft.ScrollMode.AUTO),
                width=550,
                height=400,
            ),
            actions=[ft.TextButton("Fechar", on_click=fechar)],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _criar_abas(self):
        return ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Dados Pessoais", icon=ft.Icons.PERSON, content=self._aba_dados_pessoais()),
                ft.Tab(text="Documentos", icon=ft.Icons.BADGE, content=self._aba_documentos()),
                ft.Tab(text="Contrato", icon=ft.Icons.WORK, content=self._aba_contrato()),
                ft.Tab(text="Benefícios", icon=ft.Icons.CARD_GIFTCARD, content=self._aba_beneficios()),
                ft.Tab(text="Dependentes", icon=ft.Icons.FAMILY_RESTROOM, content=self._aba_dependentes()),
            ],
            expand=True,
        )
    
    def _aba_dados_pessoais(self):
        c = self.colaborador
        return ft.Container(
            content=ft.Column([
                criar_secao("Informações Básicas", [
                    ft.Row([
                        criar_campo_view("Nome Completo", c.get('nome_completo'), 300),
                        criar_campo_view("Data Nascimento", formatar_data_br(c.get('data_nascimento'))),
                        criar_campo_view("Sexo", c.get('sexo')),
                    ], wrap=True),
                ]),
                criar_secao("Endereço", [
                    ft.Row([
                        criar_campo_view("Endereço", c.get('endereco'), 300),
                        criar_campo_view("Cidade", c.get('cidade')),
                        criar_campo_view("UF", c.get('uf_endereco'), 60),
                    ], wrap=True),
                ]),
                criar_secao("Contato", [
                    ft.Row([
                        criar_campo_view("Telefone", c.get('telefone')),
                        criar_campo_view("Celular", c.get('celular')),
                        criar_campo_view("E-mail", c.get('email'), 250),
                    ], wrap=True),
                ]),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
            expand=True,
        )
    
    def _aba_documentos(self):
        c = self.colaborador
        return ft.Container(
            content=ft.Column([
                criar_secao("Documentos", [
                    ft.Row([
                        criar_campo_view("CPF", formatar_cpf(c.get('cpf', ''))),
                        criar_campo_view("RG", c.get('rg')),
                        criar_campo_view("CTPS", c.get('carteira_profissional')),
                    ], wrap=True),
                    ft.Row([
                        criar_campo_view("PIS", c.get('pis')),
                        criar_campo_view("CNH", c.get('habilitacao')),
                    ], wrap=True),
                ]),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
            expand=True,
        )
    
    def _aba_contrato(self):
        c = self.colaborador
        return ft.Container(
            content=ft.Column([
                criar_secao("Dados do Contrato", [
                    ft.Row([
                        criar_campo_view("Empresa", c.get('empresa_nome'), 300),
                        criar_campo_view("Admissão", formatar_data_br(c.get('data_admissao'))),
                    ], wrap=True),
                    ft.Row([
                        criar_campo_view("Função", c.get('funcao'), 200),
                        criar_campo_view("Salário", formatar_moeda(c.get('salario'))),
                        criar_campo_view("Tipo", c.get('tipo_contrato')),
                    ], wrap=True),
                ]),
                criar_secao("Dados Bancários", [
                    ft.Row([
                        criar_campo_view("Banco", c.get('banco')),
                        criar_campo_view("Agência", c.get('agencia')),
                        criar_campo_view("Conta", c.get('conta')),
                    ], wrap=True),
                ]),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
            expand=True,
        )
    
    def _aba_beneficios(self):
        c = self.colaborador
        sim_nao = lambda v: "Sim" if v else "Não"
        return ft.Container(
            content=ft.Column([
                criar_secao("Benefícios", [
                    ft.Row([
                        criar_campo_view("VT", sim_nao(c.get('vale_transporte'))),
                        criar_campo_view("VR", sim_nao(c.get('vale_refeicao'))),
                        criar_campo_view("VA", sim_nao(c.get('vale_alimentacao'))),
                    ], wrap=True),
                ]),
                criar_secao("Observações", [
                    ft.Text(c.get('observacoes_gerais', '-') or "-"),
                ]),
            ], scroll=ft.ScrollMode.AUTO),
            padding=10,
            expand=True,
        )
    
    def _aba_dependentes(self):
        lista = []
        if not self.dependentes:
            lista.append(ft.Text("Nenhum dependente", italic=True, color=ft.Colors.GREY))
        else:
            for dep in self.dependentes:
                lista.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(dep.get('nome', ''), weight=ft.FontWeight.BOLD),
                            ft.Text(f"{dep.get('parentesco', '')} - CPF: {formatar_cpf(dep.get('cpf', ''))}"),
                        ], spacing=2),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                    )
                )
        
        return ft.Container(
            content=ft.Column([criar_secao("Dependentes", lista)], scroll=ft.ScrollMode.AUTO),
            padding=10, expand=True,
        )
    
    def toggle_edicao(self, e):
        if self.on_voltar_callback:
            self.on_voltar_callback(editar_id=self.colaborador_id)
    
    def gerar_pdf(self, e):
        try:
            empresa = db.obter_empresa(self.colaborador.get('empresa_id')) if self.colaborador.get('empresa_id') else None
            output_path = gerar_ficha_registro_pdf(self.colaborador, self.dependentes, empresa)

            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"PDF gerado: {output_path}"), bgcolor=COR_SUCESSO)
            self.page.snack_bar.open = True
            self.page.update()

            # Abrir o PDF automaticamente
            import subprocess
            subprocess.Popen(['start', '', output_path], shell=True)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro ao gerar PDF: {str(ex)}"), bgcolor=COR_ERRO)
            self.page.snack_bar.open = True
            self.page.update()
    
    def voltar(self, e):
        if self.on_voltar_callback:
            self.on_voltar_callback()

    def _abrir_documentos(self, e):
        """Abre diálogo para gerenciar documentos do colaborador."""
        import subprocess

        # Obter status dos documentos
        status_docs = db.obter_status_documentos_colaborador(self.colaborador_id)
        documentos_existentes = db.listar_documentos_colaborador(self.colaborador_id)
        docs_por_tipo = {doc['tipo_documento']: doc for doc in documentos_existentes}

        # Variável para armazenar referência ao diálogo principal
        dialog = None

        # Container para a lista de documentos (será atualizado)
        lista_documentos_container = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8)

        def criar_card_documento(tipo, doc, is_extra=False, is_dependente=False):
            """Cria um card para um documento."""
            tem_documento = doc is not None
            is_nao_necessario = doc.get('nao_necessario', 0) == 1 if doc else False
            pode_editar = db.usuario_pode_editar()

            # Cor e ícone baseado no status
            if is_extra:
                cor_status = "#8e44ad"
                icone_status = ft.Icons.DESCRIPTION if tem_documento else ft.Icons.ADD_CIRCLE_OUTLINE
            elif is_dependente:
                if is_nao_necessario:
                    cor_status = "#95a5a6"
                    icone_status = ft.Icons.DO_NOT_DISTURB
                elif tem_documento:
                    cor_status = "#e67e22"  # Laranja para dependentes com documento
                    icone_status = ft.Icons.CHECK_CIRCLE
                else:
                    cor_status = "#e74c3c"  # Vermelho para dependentes sem documento
                    icone_status = ft.Icons.CANCEL
            elif is_nao_necessario:
                cor_status = "#95a5a6"  # Cinza para "Não Necessário"
                icone_status = ft.Icons.DO_NOT_DISTURB
            elif tem_documento:
                cor_status = COR_SUCESSO
                icone_status = ft.Icons.CHECK_CIRCLE
            else:
                cor_status = COR_ERRO
                icone_status = ft.Icons.CANCEL

            # Botões de ação
            botoes_acao = []

            if is_nao_necessario:
                # Documento marcado como não necessário - mostrar botão para desfazer (apenas se pode editar)
                if pode_editar:
                    botoes_acao.append(
                        ft.IconButton(
                            icon=ft.Icons.UNDO,
                            icon_color=COR_SECUNDARIA,
                            tooltip="Desfazer 'Não Necessário'",
                            on_click=lambda ev, t=tipo: desfazer_nao_necessario(t),
                            icon_size=18,
                        )
                    )
            elif tem_documento:
                # Botão visualizar sempre disponível
                botoes_acao.append(
                    ft.IconButton(
                        icon=ft.Icons.VISIBILITY,
                        icon_color=COR_SECUNDARIA,
                        tooltip="Visualizar",
                        on_click=lambda ev, d=doc: visualizar_documento(d),
                        icon_size=18,
                    )
                )
                # Botão substituir apenas se pode editar
                if pode_editar:
                    botoes_acao.append(
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=COR_ALERTA,
                            tooltip="Substituir",
                            on_click=lambda ev, t=tipo: anexar_documento(t),
                            icon_size=18,
                        )
                    )
            else:
                # Documento obrigatório sem anexo - mostrar Anexar e Não Necessário (apenas se pode editar)
                if pode_editar:
                    botoes_acao.append(
                        ft.IconButton(
                            icon=ft.Icons.ATTACH_FILE,
                            icon_color=COR_SECUNDARIA,
                            tooltip="Anexar",
                            on_click=lambda ev, t=tipo: anexar_documento(t),
                            icon_size=18,
                        )
                    )
                    # Botão "Não Necessário" apenas para documentos obrigatórios sem anexo
                    if not is_extra:
                        botoes_acao.append(
                            ft.IconButton(
                                icon=ft.Icons.DO_NOT_DISTURB,
                                icon_color="#95a5a6",
                                tooltip="Marcar como Não Necessário",
                                on_click=lambda ev, t=tipo: marcar_nao_necessario(t),
                                icon_size=18,
                            )
                        )

            # Botão de excluir área SEMPRE para documentos extras (com arquivo) - apenas se pode editar
            if is_extra and tem_documento and pode_editar:
                botoes_acao.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_FOREVER,
                        icon_color=COR_ERRO,
                        tooltip="Excluir área do documento",
                        on_click=lambda ev, d=doc: confirmar_exclusao(d),
                        icon_size=18,
                    )
                )

            # Texto do card
            texto_tipo = tipo
            if is_nao_necessario:
                texto_tipo = f"{tipo} (N/N)"

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icone_status, color=cor_status, size=18),
                        ft.Text(texto_tipo, size=11, weight=ft.FontWeight.W_500, expand=True, max_lines=2,
                               color="#95a5a6" if is_nao_necessario else None),
                    ], spacing=5),
                    ft.Row(botoes_acao, spacing=0, alignment=ft.MainAxisAlignment.END),
                ], spacing=5),
                padding=ft.padding.all(8),
                border=ft.border.all(1, cor_status),
                border_radius=6,
                bgcolor="#f5f5f5" if is_nao_necessario else ft.Colors.WHITE,
                expand=True,
            )

        def atualizar_lista_documentos():
            """Atualiza a lista de documentos no diálogo."""
            nonlocal docs_por_tipo
            documentos_existentes = db.listar_documentos_colaborador(self.colaborador_id)
            docs_por_tipo = {doc['tipo_documento']: doc for doc in documentos_existentes}
            status_docs = db.obter_status_documentos_colaborador(self.colaborador_id)

            # Obter documentos de dependentes
            docs_dependentes = db.obter_documentos_obrigatorios_dependentes(self.colaborador_id)
            todos_obrigatorios = status_docs.get('documentos_obrigatorios', db.DOCUMENTOS_OBRIGATORIOS)

            lista_documentos_container.controls.clear()

            # Atualizar barra de progresso
            if hasattr(self, '_progress_bar'):
                self._progress_bar.value = status_docs['percentual'] / 100
            if hasattr(self, '_progress_text'):
                self._progress_text.value = f"{status_docs['completos']}/{status_docs['total_obrigatorios']} obrigatórios ({status_docs['percentual']}%)"

            # Seção: Documentos do Colaborador
            lista_documentos_container.controls.append(
                ft.Container(
                    content=ft.Text("Documentos do Colaborador", weight=ft.FontWeight.BOLD, size=14, color=COR_PRIMARIA),
                    padding=ft.padding.only(bottom=5),
                )
            )

            # Criar matriz de 4 colunas para documentos obrigatórios do colaborador
            docs_obrigatorios_base = db.DOCUMENTOS_OBRIGATORIOS
            for i in range(0, len(docs_obrigatorios_base), 4):
                row_items = []

                for j in range(4):
                    if i + j < len(docs_obrigatorios_base):
                        tipo = docs_obrigatorios_base[i + j]
                        doc = docs_por_tipo.get(tipo)
                        row_items.append(criar_card_documento(tipo, doc))
                    else:
                        row_items.append(ft.Container(expand=True))

                lista_documentos_container.controls.append(
                    ft.Row(row_items, spacing=8)
                )

            # Seção: Documentos de Dependentes (se houver)
            if docs_dependentes:
                lista_documentos_container.controls.append(ft.Divider(height=15))
                lista_documentos_container.controls.append(
                    ft.Container(
                        content=ft.Text("Documentos de Dependentes", weight=ft.FontWeight.BOLD, size=14, color="#e67e22"),
                        padding=ft.padding.only(bottom=5),
                    )
                )

                # Criar matriz de 4 colunas para documentos de dependentes
                for i in range(0, len(docs_dependentes), 4):
                    row_items = []

                    for j in range(4):
                        if i + j < len(docs_dependentes):
                            tipo = docs_dependentes[i + j]
                            doc = docs_por_tipo.get(tipo)
                            row_items.append(criar_card_documento(tipo, doc, is_dependente=True))
                        else:
                            row_items.append(ft.Container(expand=True))

                    lista_documentos_container.controls.append(
                        ft.Row(row_items, spacing=8)
                    )

            # Seção: Documentos Extras
            extras = status_docs.get('extras', [])
            if extras:
                lista_documentos_container.controls.append(ft.Divider(height=15))
                lista_documentos_container.controls.append(
                    ft.Container(
                        content=ft.Text("Documentos Extras", weight=ft.FontWeight.BOLD, size=14, color="#8e44ad"),
                        padding=ft.padding.only(bottom=5),
                    )
                )

                # Criar matriz de 4 colunas para documentos extras
                for i in range(0, len(extras), 4):
                    row_items = []

                    for j in range(4):
                        if i + j < len(extras):
                            doc = extras[i + j]
                            row_items.append(criar_card_documento(doc['tipo_documento'], doc, is_extra=True))
                        else:
                            row_items.append(ft.Container(expand=True))

                    lista_documentos_container.controls.append(
                        ft.Row(row_items, spacing=8)
                    )

            self.page.update()

        def visualizar_documento(doc):
            """Abre o documento no visualizador padrão do sistema."""
            caminho = doc.get('caminho_arquivo', '')
            if caminho and os.path.exists(caminho):
                try:
                    subprocess.Popen(['start', '', caminho], shell=True)
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Erro ao abrir documento: {str(ex)}"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Arquivo não encontrado!"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()

        def anexar_documento(tipo_documento: str):
            """Abre o file picker para selecionar documento."""
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para anexar documentos."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            def on_file_selected(ev: ft.FilePickerResultEvent):
                if ev.files and len(ev.files) > 0:
                    arquivo_selecionado = ev.files[0]
                    caminho_origem = arquivo_selecionado.path

                    try:
                        cpf = self.colaborador.get('cpf', '')
                        db.salvar_documento(
                            self.colaborador_id,
                            tipo_documento,
                            caminho_origem,
                            cpf
                        )

                        # Registrar no histórico
                        db.registrar_alteracao(
                            self.colaborador_id,
                            'documento_anexado',
                            None,
                            tipo_documento
                        )

                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Documento '{tipo_documento}' anexado com sucesso!"),
                            bgcolor=COR_SUCESSO
                        )
                        self.page.snack_bar.open = True

                        # Atualizar lista
                        atualizar_lista_documentos()

                    except Exception as ex:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Erro ao anexar documento: {str(ex)}"),
                            bgcolor=COR_ERRO
                        )
                        self.page.snack_bar.open = True
                        self.page.update()

            # Criar e adicionar file picker
            file_picker = ft.FilePicker(on_result=on_file_selected)
            self.page.overlay.append(file_picker)
            self.page.update()

            # Abrir diálogo de seleção de arquivo
            file_picker.pick_files(
                dialog_title=f"Selecionar arquivo para: {tipo_documento}",
                allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"],
                allow_multiple=False
            )

        def marcar_nao_necessario(tipo_documento: str):
            """Marca um documento como não necessário para este colaborador."""
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para modificar documentos."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            db.marcar_documento_nao_necessario(self.colaborador_id, tipo_documento)

            # Registrar no histórico
            db.registrar_alteracao(
                self.colaborador_id,
                'documento_nao_necessario',
                None,
                tipo_documento
            )

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"'{tipo_documento}' marcado como Não Necessário"),
                bgcolor="#95a5a6"
            )
            self.page.snack_bar.open = True

            # Atualizar lista
            atualizar_lista_documentos()

        def desfazer_nao_necessario(tipo_documento: str):
            """Remove a marcação de não necessário de um documento."""
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para modificar documentos."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            db.desmarcar_documento_nao_necessario(self.colaborador_id, tipo_documento)

            # Registrar no histórico
            db.registrar_alteracao(
                self.colaborador_id,
                'documento_voltou_obrigatorio',
                tipo_documento,
                None
            )

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"'{tipo_documento}' voltou a ser obrigatório"),
                bgcolor=COR_SECUNDARIA
            )
            self.page.snack_bar.open = True

            # Atualizar lista
            atualizar_lista_documentos()

        def confirmar_exclusao(doc):
            """Mostra confirmação e exclui o documento."""
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para excluir documentos."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Criar container de confirmação que aparece no topo da lista
            container_confirmacao = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=COR_ALERTA, size=24),
                        ft.Text("Confirmar Exclusão", weight=ft.FontWeight.BOLD, size=14),
                    ], spacing=8),
                    ft.Text(
                        f"Deseja excluir o documento '{doc['tipo_documento']}'?\n"
                        "Esta ação não pode ser desfeita!",
                        size=12,
                        color=ft.Colors.RED_900,
                    ),
                    ft.Row([
                        ft.ElevatedButton(
                            "Cancelar",
                            on_click=lambda ev: fechar_confirmacao(),
                            bgcolor=ft.Colors.GREY_400,
                            color="white",
                        ),
                        ft.ElevatedButton(
                            "Excluir Permanentemente",
                            icon=ft.Icons.DELETE_FOREVER,
                            on_click=lambda ev: executar_exclusao(doc),
                            bgcolor=COR_ERRO,
                            color="white",
                        ),
                    ], spacing=10, alignment=ft.MainAxisAlignment.END),
                ], spacing=10),
                padding=15,
                bgcolor="#ffebee",
                border=ft.border.all(2, COR_ERRO),
                border_radius=8,
                margin=ft.margin.only(bottom=10),
            )

            def fechar_confirmacao():
                if container_confirmacao in lista_documentos_container.controls:
                    lista_documentos_container.controls.remove(container_confirmacao)
                    self.page.update()

            def executar_exclusao(documento):
                tipo_doc = documento['tipo_documento']
                db.excluir_documento(documento['id'])
                fechar_confirmacao()

                # Registrar no histórico
                db.registrar_alteracao(
                    self.colaborador_id,
                    'documento_excluido',
                    tipo_doc,
                    None
                )

                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Documento '{tipo_doc}' excluído!"),
                    bgcolor=COR_SUCESSO
                )
                self.page.snack_bar.open = True

                # Atualizar lista
                atualizar_lista_documentos()

            # Remover confirmação anterior se existir
            controles_para_remover = [c for c in lista_documentos_container.controls
                                       if isinstance(c, ft.Container) and hasattr(c, 'bgcolor') and c.bgcolor == "#ffebee"]
            for c in controles_para_remover:
                lista_documentos_container.controls.remove(c)

            # Inserir no topo da lista
            lista_documentos_container.controls.insert(0, container_confirmacao)
            self.page.update()

        def adicionar_tipo_documento(ev):
            """Abre diálogo para adicionar novo tipo de documento."""
            # Verificar permissão
            if not db.usuario_pode_editar():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Você não tem permissão para adicionar documentos."),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            campo_tipo = ft.TextField(
                label="Nome do novo tipo de documento",
                width=350,
                autofocus=True,
            )

            def salvar_novo_tipo(ev2):
                novo_tipo = campo_tipo.value.strip().upper()
                if not novo_tipo:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Informe o nome do tipo de documento!"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                # Verificar se já existe
                tipos_existentes = db.listar_tipos_documentos()
                if novo_tipo in tipos_existentes:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Este tipo de documento já existe!"),
                        bgcolor=COR_ALERTA
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                novo_tipo_dialog.open = False
                self.page.update()

                # Abrir file picker para o novo tipo
                anexar_documento(novo_tipo)

            def cancelar_novo_tipo(ev2):
                novo_tipo_dialog.open = False
                self.page.update()

            novo_tipo_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Adicionar Novo Tipo de Documento"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Informe o nome do novo tipo de documento:", size=13),
                        campo_tipo,
                        ft.Text("Ex: CERTIFICADO DE CURSO, LAUDO MÉDICO, etc.", size=11, italic=True, color=ft.Colors.GREY),
                    ], spacing=10),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_novo_tipo),
                    ft.ElevatedButton("Continuar", on_click=salvar_novo_tipo, bgcolor=COR_SUCESSO, color="white"),
                ],
            )

            self.page.overlay.append(novo_tipo_dialog)
            novo_tipo_dialog.open = True
            self.page.update()

        def fechar(ev):
            nonlocal dialog
            if dialog:
                dialog.open = False
            self.page.update()

        def abrir_pdf_lista_documentos(ev):
            """Abre o PDF da lista de documentos (RDA-RH-0001.pdf)."""
            caminho_pdf = os.path.join("RDA", "RDA-RH-0001.pdf")
            if os.path.exists(caminho_pdf):
                try:
                    subprocess.Popen(['start', '', caminho_pdf], shell=True)
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Erro ao abrir PDF: {str(ex)}"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Arquivo RDA-RH-0001.pdf não encontrado na pasta RDA!"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()

        # Barra de progresso dos documentos obrigatórios
        self._progress_bar = ft.ProgressBar(
            value=status_docs['percentual'] / 100,
            color=COR_SUCESSO if status_docs['percentual'] == 100 else COR_ALERTA,
            bgcolor=ft.Colors.GREY_300,
            width=1050,
        )
        self._progress_text = ft.Text(
            f"{status_docs['completos']}/{status_docs['total_obrigatorios']} obrigatórios ({status_docs['percentual']}%)",
            size=12,
            color=ft.Colors.GREY_700,
        )

        # Carregar lista inicial
        atualizar_lista_documentos()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, color="#16a085", size=28),
                ft.Column([
                    ft.Text("Documentos do Colaborador"),
                    ft.Text(self.colaborador.get('nome_completo', ''), size=12, color=ft.Colors.GREY_700),
                ], spacing=0),
            ]),
            content=ft.Container(
                content=ft.Column([
                    # Barra de progresso
                    ft.Container(
                        content=ft.Column([
                            self._progress_bar,
                            self._progress_text,
                        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.only(bottom=15),
                    ),
                    # Lista de documentos
                    ft.Container(
                        content=lista_documentos_container,
                        height=400,
                        expand=True,
                    ),
                ], spacing=5),
                width=1100,
            ),
            actions=[
                ft.ElevatedButton(
                    "PDF Lista de Documentos",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=abrir_pdf_lista_documentos,
                    bgcolor=COR_PRIMARIA,
                    color="white",
                ),
            ] + ([
                ft.ElevatedButton(
                    "Adicionar Tipo",
                    icon=ft.Icons.ADD,
                    on_click=adicionar_tipo_documento,
                    bgcolor="#8e44ad",
                    color="white",
                ),
            ] if db.usuario_pode_editar() else []) + [
                ft.ElevatedButton("Fechar", on_click=fechar, bgcolor=COR_SECUNDARIA, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
