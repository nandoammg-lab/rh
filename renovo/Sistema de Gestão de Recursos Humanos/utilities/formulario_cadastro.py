"""
Formulário de Cadastro de Colaborador - Sistema de Gestão de RH
"""

import flet as ft
from datetime import datetime
import os
import shutil
import re

from .constantes import (
    criar_campo_texto, criar_dropdown, criar_data_picker, criar_secao,
    formatar_cpf, validar_cpf, formatar_data_br, formatar_data_db, formatar_moeda,
    COR_PRIMARIA, COR_SECUNDARIA, COR_SUCESSO, COR_ALERTA, COR_ERRO,
    ESTADOS_BR, GRAUS_INSTRUCAO, ESTADOS_CIVIS, TIPOS_CONTA, FORMAS_PAGAMENTO,
    TIPOS_CONTRATO, TIPOS_CNH, PARENTESCOS, TIPOS_DEFICIENCIA, DIAS_SEMANA
)
from . import database as db


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


class FormularioCadastro:
    """Formulário completo de cadastro de colaborador."""

    def __init__(self, page: ft.Page, on_salvar=None, on_cancelar=None, colaborador_id: int = None,
                 on_salvar_temp=None, on_limpar=None, dados_temp=None, dependentes_temp=None, foto_path_temp=None):
        self.page = page
        self.on_salvar_callback = on_salvar
        self.on_cancelar_callback = on_cancelar
        self.colaborador_id = colaborador_id
        self.colaborador = None
        self.foto_path = None
        self.campos = {}
        self.dependentes_lista = []
        self.dependentes_container = None
        self.foto_widget = None
        self.file_picker = None

        # Callbacks e dados para persistência temporária
        self.on_salvar_temp = on_salvar_temp
        self.on_limpar_callback = on_limpar
        self.dados_temp = dados_temp or {}
        self.dependentes_temp = dependentes_temp or []
        self.foto_path_temp = foto_path_temp

        if colaborador_id:
            self.colaborador = db.obter_colaborador(colaborador_id)
            self.dependentes_lista = list(db.listar_dependentes(colaborador_id))
            if self.colaborador:
                self.foto_path = self.colaborador.get('foto_path')
        elif self.dados_temp:
            # Carregar dados temporários para novo colaborador
            self.dependentes_lista = list(self.dependentes_temp) if self.dependentes_temp else []
            self.foto_path = self.foto_path_temp

    def build(self) -> ft.Container:
        # Usar dados temporários se disponíveis (para novo colaborador), senão usar colaborador existente
        c = self.dados_temp if self.dados_temp else (self.colaborador or {})
        self._criar_campos(c)

        # File picker para foto
        self.file_picker = ft.FilePicker(on_result=self._on_foto_selecionada)
        self.page.overlay.append(self.file_picker)

        # Widget da foto
        self._criar_foto_widget()

        # Container de dependentes
        self.dependentes_container = ft.Column(spacing=10)
        self._atualizar_lista_dependentes()

        # Criar conteúdo das abas
        aba_dados_pessoais = self._criar_aba_dados_pessoais()
        aba_documentos = self._criar_aba_documentos()
        aba_contrato = self._criar_aba_contrato()
        aba_beneficios = self._criar_aba_beneficios()

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
            self._criar_botoes_acao(),
        ], spacing=10, expand=1)

    def _criar_aba_dados_pessoais(self):
        """Cria o conteúdo da aba Dados Pessoais."""
        return ft.Column([
            # Foto e Empresa lado a lado
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        self.foto_widget,
                        ft.ElevatedButton(
                            "Selecionar Foto",
                            icon=ft.Icons.PHOTO_CAMERA,
                            on_click=lambda e: self.file_picker.pick_files(
                                allowed_extensions=["jpg", "jpeg", "png"],
                                dialog_title="Selecionar foto do colaborador"
                            ),
                            bgcolor=COR_SECUNDARIA,
                            color="white",
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=10,
                ),
                ft.Column([
                    criar_secao("Empresa", [self.campos['empresa']]),
                ], expand=True),
            ], spacing=20),

            criar_secao("Informações Básicas", [
                ft.Row([self.campos['nome_completo']], wrap=True),
                ft.Row([self.campos['data_nascimento'], self.campos['sexo'],
                       self.campos['naturalidade'], self.campos['uf_naturalidade']], wrap=True),
                ft.Row([self.campos['estado_civil'], self.campos['grau_instrucao'],
                       self.campos['curso_formacao']], wrap=True),
                ft.Row([self.campos['deficiencia_tipo'], self.campos['deficiencia_outros']], wrap=True),
            ]),

            criar_secao("Filiação", [
                ft.Row([self.campos['nome_mae'], self.campos['cpf_mae']], wrap=True),
                ft.Row([self.campos['nome_pai'], self.campos['cpf_pai']], wrap=True),
            ]),

            criar_secao("Endereço", [
                ft.Row([self.campos['endereco'], self.campos['numero'], self.campos['complemento']], wrap=True),
                ft.Row([self.campos['bairro'], self.campos['cep'],
                       self.campos['cidade'], self.campos['uf_endereco']], wrap=True),
            ]),

            criar_secao("Contato", [
                ft.Row([self.campos['telefone'], self.campos['celular'], self.campos['email']], wrap=True),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_documentos(self):
        """Cria o conteúdo da aba Documentos."""
        return ft.Column([
            criar_secao("Documentos Principais", [
                ft.Row([self.campos['cpf']], wrap=True),
                ft.Row([self.campos['rg'], self.campos['orgao_emissor_rg'],
                       self.campos['uf_rg']], wrap=True),
                ft.Row([self.campos['carteira_profissional'], self.campos['pis'],
                       self.campos['serie_carteira'], self.campos['uf_carteira']], wrap=True),
            ]),

            criar_secao("Título de Eleitor", [
                ft.Row([self.campos['titulo_eleitor'], self.campos['zona_eleitor'],
                       self.campos['secao_eleitor']], wrap=True),
            ]),

            criar_secao("CNH e Reservista", [
                ft.Row([self.campos['habilitacao'], self.campos['tipo_cnh'],
                       self.campos['validade_cnh']], wrap=True),
                ft.Row([self.campos['reservista']], wrap=True),
            ]),

            criar_secao("Dados do Último Registro (Emprego Anterior)", [
                ft.Row([self.campos['empresa_ultimo_emprego'],
                       self.campos['cnpj_ultimo_emprego']], wrap=True),
                ft.Row([self.campos['data_admissao_ultimo'], self.campos['data_saida_ultimo']], wrap=True),
                ft.Row([self.campos['primeiro_registro'],
                       self.campos['data_ultima_contribuicao_sindical']], wrap=True),
            ]),

            criar_secao("Exame Médico (ASO)", [
                ft.Row([self.campos['data_exame_medico'], self.campos['tipo_exames']], wrap=True),
                ft.Row([self.campos['nome_medico'], self.campos['crm'],
                       self.campos['uf_crm']], wrap=True),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_contrato(self):
        """Cria o conteúdo da aba Contrato."""
        return ft.Column([
            criar_secao("Dados do Contrato", [
                ft.Row([self.campos['data_admissao'], self.campos['funcao'],
                       self.campos['departamento']], wrap=True),
                ft.Row([self.campos['salario'], self.campos['forma_pagamento'],
                       self.campos['tipo_contrato']], wrap=True),
                self.container_experiencia,
            ]),

            criar_secao("Horário de Trabalho", [
                ft.Row([self.campos['horario_chegada'], self.campos['horario_saida'],
                       self.campos['intervalo_inicio'], self.campos['intervalo_fim']], wrap=True),
                ft.Row([self.campos['dia_trabalho_inicio'], self.campos['dia_trabalho_fim']], wrap=True),
            ]),

            criar_secao("Dados Bancários", [
                ft.Row([self.campos['tipo_conta'], self.campos['banco']], wrap=True),
                ft.Row([self.campos['agencia'], self.campos['conta']], wrap=True),
            ]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_aba_beneficios(self):
        """Cria o conteúdo da aba Benefícios e Outros."""
        return ft.Column([
            criar_secao("Benefícios", [
                ft.Row([self.campos['vale_transporte'], self.campos['vale_alimentacao']], wrap=True),
                ft.Row([self.campos['assistencia_medica'], self.campos['assistencia_odontologica'],
                       self.campos['seguro_vida']], wrap=True),
            ]),

            criar_secao("Dependentes (IR e Salário Família)", [
                self.dependentes_container,
                ft.ElevatedButton(
                    "Adicionar Dependente",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self._adicionar_dependente,
                    bgcolor=COR_SECUNDARIA,
                    color="white",
                ),
            ]),

            criar_secao("Observações", [self.campos['observacoes_gerais']]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _criar_foto_widget(self):
        """Cria o widget da foto do colaborador."""
        if self.foto_path and os.path.exists(self.foto_path):
            self.foto_widget = ft.Image(src=self.foto_path, width=120, height=150, fit=ft.ImageFit.COVER, border_radius=8)
        else:
            self.foto_widget = ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=60, color=ft.Colors.GREY),
                width=120,
                height=150,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
            )

    def _on_foto_selecionada(self, e: ft.FilePickerResultEvent):
        """Callback quando uma foto é selecionada."""
        if e.files and len(e.files) > 0:
            arquivo = e.files[0]

            # Validar tamanho do arquivo (máximo 5MB)
            TAMANHO_MAXIMO_MB = 5
            try:
                tamanho_arquivo = os.path.getsize(arquivo.path)
                tamanho_mb = tamanho_arquivo / (1024 * 1024)
                if tamanho_mb > TAMANHO_MAXIMO_MB:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Arquivo muito grande ({tamanho_mb:.1f}MB). Máximo permitido: {TAMANHO_MAXIMO_MB}MB"),
                        bgcolor=COR_ERRO
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return
            except Exception:
                pass  # Se não conseguir verificar o tamanho, continua

            # Validar extensão do arquivo
            extensoes_permitidas = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(arquivo.name)[1].lower()
            if ext not in extensoes_permitidas:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Tipo de arquivo não permitido. Use: JPG, JPEG ou PNG"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Validar se é uma imagem válida (verificar header do arquivo)
            try:
                with open(arquivo.path, 'rb') as f:
                    header = f.read(16)
                    # Verificar assinaturas de arquivos de imagem
                    is_jpeg = header[:2] == b'\xff\xd8'
                    is_png = header[:8] == b'\x89PNG\r\n\x1a\n'
                    if not (is_jpeg or is_png):
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("O arquivo não é uma imagem válida."),
                            bgcolor=COR_ERRO
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
            except Exception:
                pass  # Se não conseguir verificar, continua

            # Obter CPF - primeiro do campo, ou do colaborador existente se estiver editando
            cpf_valor = self.campos['cpf'].value if self.campos.get('cpf') else None
            cpf_limpo = re.sub(r'\D', '', cpf_valor or '') if cpf_valor else None

            # Se não tem CPF no campo mas está editando, usar CPF do colaborador existente
            if (not cpf_limpo or len(cpf_limpo) != 11) and self.colaborador:
                cpf_limpo = re.sub(r'\D', '', self.colaborador.get('cpf', '') or '')

            if not cpf_limpo or len(cpf_limpo) != 11:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Preencha o CPF antes de selecionar a foto!"),
                    bgcolor=COR_ERRO
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Criar pasta de fotos se não existir (caminho relativo)
            fotos_dir = "fotos_colaboradores"
            if not os.path.exists(fotos_dir):
                os.makedirs(fotos_dir)

            # Remover foto antiga com extensão diferente se existir
            for ext_antiga in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                foto_antiga = f"{fotos_dir}/{cpf_limpo}{ext_antiga}"
                if os.path.exists(foto_antiga):
                    try:
                        os.remove(foto_antiga)
                    except (FileNotFoundError, PermissionError):
                        pass

            # Copiar foto para pasta com nome do CPF (caminho relativo)
            novo_nome = f"{cpf_limpo}{ext}"
            destino = f"{fotos_dir}/{novo_nome}"

            # Copiar nova foto (substitui se já existir)
            shutil.copy2(arquivo.path, destino)
            self.foto_path = destino

            # Atualizar widget da foto visualmente
            if hasattr(self.foto_widget, 'src'):
                # É uma Image, atualizar src
                self.foto_widget.src = destino
            else:
                # É um Container placeholder, substituir por Image
                self.foto_widget.content = ft.Image(src=destino, width=120, height=150, fit=ft.ImageFit.COVER, border_radius=8)

            self.page.snack_bar = ft.SnackBar(content=ft.Text("Foto selecionada com sucesso!"), bgcolor=COR_SUCESSO)
            self.page.snack_bar.open = True
            self.page.update()

    def _criar_header(self):
        titulo = "Editar Colaborador" if self.colaborador_id else "Novo Colaborador"
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON_ADD if not self.colaborador_id else ft.Icons.EDIT,
                           size=30, color=COR_PRIMARIA),
                    ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ], spacing=10),
                ft.ElevatedButton(
                    "Voltar",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=self._cancelar,
                    bgcolor=COR_SECUNDARIA,
                    color="white",
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20,
            bgcolor="white",
            border_radius=8,
            margin=ft.margin.only(bottom=10),
        )

    def _criar_campos(self, c: dict):
        # Empresa
        empresas = db.listar_empresas()
        opcoes_empresas = [e['razao_social'] for e in empresas]
        empresa_atual = None
        if c.get('empresa_id'):
            emp = db.obter_empresa(c['empresa_id'])
            empresa_atual = emp['razao_social'] if emp else None
        elif c.get('empresa_nome'):
            # Dados temporários guardam o nome da empresa diretamente
            empresa_atual = c.get('empresa_nome')

        self.campos['empresa'] = criar_dropdown("Empresa Contratante", opcoes_empresas, empresa_atual, 600)

        # Dados Pessoais
        self.campos['nome_completo'] = criar_campo_texto("Nome Completo *", c.get('nome_completo', ''), 720)
        self.campos['nome_completo'].autofocus = True  # Primeiro campo recebe foco automaticamente
        self.campos['endereco'] = criar_campo_texto("Endereço", c.get('endereco', ''), 540)
        self.campos['numero'] = criar_campo_texto("Número", c.get('numero', ''), 120)
        self.campos['complemento'] = criar_campo_texto("Complemento", c.get('complemento', ''), 240)
        self.campos['bairro'] = criar_campo_texto("Bairro", c.get('bairro', ''), 340)
        cep_formatado = self._formatar_cep_valor(c.get('cep', ''))
        self.campos['cep'] = criar_campo_texto("CEP", cep_formatado, 180, on_change=self._on_cep_change, hint_text="00000-000")
        self.campos['cidade'] = criar_campo_texto("Cidade", c.get('cidade', ''), 340)
        self.campos['uf_endereco'] = criar_dropdown("UF", ESTADOS_BR, c.get('uf_endereco'), 145)
        self.campos['telefone'] = criar_campo_texto("Telefone", c.get('telefone', ''), 240)
        celular_formatado = self._formatar_celular_valor(c.get('celular', ''))
        self.campos['celular'] = criar_campo_texto("Celular", celular_formatado, 240, on_change=self._on_celular_change, hint_text="(00) 9 0000-0000")
        self.campos['email'] = criar_campo_texto("E-mail", c.get('email', ''), 420)
        self.campos['data_nascimento'] = criar_data_picker("Data Nascimento", formatar_data_br(c.get('data_nascimento')), on_change=self._on_data_change)
        self.campos['naturalidade'] = criar_campo_texto("Naturalidade", c.get('naturalidade', ''), 340)
        self.campos['uf_naturalidade'] = criar_dropdown("UF", ESTADOS_BR, c.get('uf_naturalidade'), 145)
        self.campos['sexo'] = criar_dropdown("Sexo", ["Masculino", "Feminino", "Outro"], c.get('sexo'), 215)
        self.campos['grau_instrucao'] = criar_dropdown("Grau de Instrução", GRAUS_INSTRUCAO, c.get('grau_instrucao'), 240, on_change=self._on_grau_instrucao_change)
        self.campos['curso_formacao'] = criar_campo_texto("Curso/Formação", c.get('curso_formacao', ''), 360)
        # Mostrar curso_formacao apenas se grau_instrucao for de Superior Incompleto em diante
        graus_com_curso = ["Superior Incompleto", "Superior Completo", "Pós-Graduação", "Mestrado", "Doutorado"]
        self.campos['curso_formacao'].visible = c.get('grau_instrucao') in graus_com_curso
        self.campos['estado_civil'] = criar_dropdown("Estado Civil", ESTADOS_CIVIS, c.get('estado_civil'), 240)

        # Deficiência - detectar valor existente para compatibilidade
        # Dados temporários guardam deficiencia_tipo e deficiencia_outros separadamente
        if c.get('deficiencia_tipo'):
            deficiencia_tipo = c.get('deficiencia_tipo')
            deficiencia_outros = c.get('deficiencia_outros', '')
        else:
            deficiencia_atual = c.get('deficiencia', '')
            deficiencia_tipo = "Nenhuma"
            deficiencia_outros = ""
            if deficiencia_atual:
                if deficiencia_atual in TIPOS_DEFICIENCIA:
                    deficiencia_tipo = deficiencia_atual
                else:
                    deficiencia_tipo = "Outros"
                    deficiencia_outros = deficiencia_atual

        self.campos['deficiencia_tipo'] = criar_dropdown("Tipo de Deficiência", TIPOS_DEFICIENCIA, deficiencia_tipo, 240, on_change=self._on_deficiencia_change)
        self.campos['deficiencia_outros'] = criar_campo_texto("Especifique a Deficiência", deficiencia_outros, 340)
        self.campos['deficiencia_outros'].visible = deficiencia_tipo == "Outros"

        # Filiação
        self.campos['nome_mae'] = criar_campo_texto("Nome da Mãe", c.get('nome_mae', ''), 540)
        cpf_mae_inicial = formatar_cpf(c.get('cpf_mae', '')) if c.get('cpf_mae') else ''
        self.campos['cpf_mae'] = criar_campo_texto("CPF da Mãe", cpf_mae_inicial, 240, on_change=self._formatar_cpf_generico, hint_text="000.000.000-00")
        self.campos['nome_pai'] = criar_campo_texto("Nome do Pai", c.get('nome_pai', ''), 540)
        cpf_pai_inicial = formatar_cpf(c.get('cpf_pai', '')) if c.get('cpf_pai') else ''
        self.campos['cpf_pai'] = criar_campo_texto("CPF do Pai", cpf_pai_inicial, 240, on_change=self._formatar_cpf_generico, hint_text="000.000.000-00")

        # Documentos
        cpf_inicial = formatar_cpf(c.get('cpf', '')) if c.get('cpf') else ''
        self.campos['cpf'] = criar_campo_texto("CPF *", cpf_inicial, 240, on_change=self._on_cpf_change, hint_text="000.000.000-00")
        self.campos['rg'] = criar_campo_texto("RG", c.get('rg', ''), 240)
        self.campos['orgao_emissor_rg'] = criar_campo_texto("Órgão Emissor", c.get('orgao_emissor_rg', ''), 180)
        self.campos['uf_rg'] = criar_dropdown("UF RG", ESTADOS_BR, c.get('uf_rg'), 145)
        self.campos['carteira_profissional'] = criar_campo_texto("CTPS", c.get('carteira_profissional', ''), 240)
        self.campos['serie_carteira'] = criar_campo_texto("Série", c.get('serie_carteira', ''), 145)
        self.campos['uf_carteira'] = criar_dropdown("UF CTPS", ESTADOS_BR, c.get('uf_carteira'), 145)
        self.campos['pis'] = criar_campo_texto("PIS", c.get('pis', ''), 240)
        self.campos['titulo_eleitor'] = criar_campo_texto("Título Eleitor", c.get('titulo_eleitor', ''), 240)
        self.campos['zona_eleitor'] = criar_campo_texto("Zona", c.get('zona_eleitor', ''), 145)
        self.campos['secao_eleitor'] = criar_campo_texto("Seção", c.get('secao_eleitor', ''), 145)
        self.campos['habilitacao'] = criar_campo_texto("CNH", c.get('habilitacao', ''), 240)
        self.campos['tipo_cnh'] = criar_dropdown("Tipo CNH", TIPOS_CNH, c.get('tipo_cnh'), 145)
        self.campos['validade_cnh'] = criar_data_picker("Validade CNH", formatar_data_br(c.get('validade_cnh')), on_change=self._on_data_change)
        self.campos['reservista'] = criar_campo_texto("Reservista", c.get('reservista', ''), 240)

        # Dados do Último Registro (emprego anterior)
        self.campos['empresa_ultimo_emprego'] = criar_campo_texto("Empresa Anterior", c.get('empresa_ultimo_emprego', ''), 360)
        self.campos['cnpj_ultimo_emprego'] = criar_campo_texto("CNPJ", c.get('cnpj_ultimo_emprego', ''), 240, hint_text="00.000.000/0000-00")
        self.campos['data_admissao_ultimo'] = criar_data_picker("Admissão", formatar_data_br(c.get('data_admissao_ultimo')), on_change=self._on_data_change)
        self.campos['data_saida_ultimo'] = criar_data_picker("Saída", formatar_data_br(c.get('data_saida_ultimo')), on_change=self._on_data_change)
        self.campos['primeiro_registro'] = criar_campo_texto("Primeiro Registro", c.get('primeiro_registro', ''), 180)
        self.campos['data_ultima_contribuicao_sindical'] = criar_data_picker("Últ. Contrib. Sindical", formatar_data_br(c.get('data_ultima_contribuicao_sindical')), on_change=self._on_data_change, width=200)

        # Exame Médico (ASO)
        self.campos['data_exame_medico'] = criar_data_picker("Data do Exame", formatar_data_br(c.get('data_exame_medico')), on_change=self._on_data_change)
        self.campos['tipo_exames'] = criar_campo_texto("Tipo de Exames", c.get('tipo_exames', ''), 360, hint_text="Ex: Admissional, Periódico, Demissional")
        self.campos['nome_medico'] = criar_campo_texto("Nome do Médico", c.get('nome_medico', ''), 360)
        self.campos['crm'] = criar_campo_texto("CRM", c.get('crm', ''), 180)
        self.campos['uf_crm'] = criar_dropdown("UF CRM", ESTADOS_BR, c.get('uf_crm'), 145)

        # Contrato
        self.campos['data_admissao'] = criar_data_picker("Data Admissão *", formatar_data_br(c.get('data_admissao')), on_change=self._on_data_change)
        self.campos['funcao'] = criar_campo_texto("Função *", c.get('funcao', ''), 360)
        self.campos['departamento'] = criar_campo_texto("Departamento", c.get('departamento', ''), 360)
        salario_formatado = self._formatar_salario_valor(c.get('salario', ''))
        self.campos['salario'] = criar_campo_texto("Salário", salario_formatado, 240, on_change=self._on_salario_change, hint_text="R$ 0,00")
        self.campos['forma_pagamento'] = criar_dropdown("Forma Pagamento", FORMAS_PAGAMENTO, c.get('forma_pagamento'), 265)
        # Em modo edição, tipo_contrato é desabilitado (usar botão "Tipo Contrato" na ficha)
        is_edicao = self.colaborador_id is not None
        self.campos['tipo_contrato'] = criar_dropdown("Tipo Contrato", TIPOS_CONTRATO, c.get('tipo_contrato'), 265, on_change=self._on_tipo_contrato_change)
        if is_edicao:
            self.campos['tipo_contrato'].disabled = True
            self.campos['tipo_contrato'].hint_text = "Use o botão 'Tipo Contrato' na ficha"

        # Campos de experiência - só visíveis para Contrato de Experiência
        self.campos['prazo_experiencia'] = criar_campo_texto("Experiência (dias)", str(c.get('prazo_experiencia', '')) if c.get('prazo_experiencia') else '', 215)
        self.campos['prorrogacao'] = criar_campo_texto("Prorrogação (dias)", str(c.get('prorrogacao', '')) if c.get('prorrogacao') else '', 215)
        is_experiencia = c.get('tipo_contrato') == "Contrato de Experiência"
        self.campos['prazo_experiencia'].visible = is_experiencia
        self.campos['prorrogacao'].visible = is_experiencia
        # Em modo edição, campos de experiência são desabilitados (usar botão "Renovar Contrato")
        if is_edicao and is_experiencia:
            self.campos['prazo_experiencia'].disabled = True
            self.campos['prorrogacao'].disabled = True
            self.campos['prazo_experiencia'].hint_text = "Use 'Renovar Contrato'"
            self.campos['prorrogacao'].hint_text = "Use 'Renovar Contrato'"

        # Container para campos de experiência
        self.container_experiencia = ft.Row([self.campos['prazo_experiencia'], self.campos['prorrogacao']], wrap=True)
        self.container_experiencia.visible = is_experiencia

        # Horário de trabalho - dois campos (chegada e saída)
        # Dados temporários guardam campos separados (horario_chegada, horario_saida)
        if c.get('horario_chegada') or c.get('horario_saida'):
            horario_chegada = c.get('horario_chegada', '')
            horario_saida = c.get('horario_saida', '')
        else:
            horario_antigo = c.get('horario_trabalho', '')
            horario_chegada = ""
            horario_saida = ""
            if horario_antigo:
                # Tentar separar horário existente
                partes = horario_antigo.replace(" às ", " - ").replace(" a ", " - ").split(" - ")
                if len(partes) >= 2:
                    horario_chegada = partes[0].strip()
                    horario_saida = partes[1].strip()
                else:
                    horario_chegada = horario_antigo

        self.campos['horario_chegada'] = criar_campo_texto("Horário Chegada", horario_chegada, 180, hint_text="Ex: 07:00")
        self.campos['horario_saida'] = criar_campo_texto("Horário Saída", horario_saida, 180, hint_text="Ex: 17:00")

        # Dias de trabalho - dois dropdowns para início e fim
        # Dados temporários guardam campos separados (dia_trabalho_inicio, dia_trabalho_fim)
        if c.get('dia_trabalho_inicio') or c.get('dia_trabalho_fim'):
            dia_inicio = c.get('dia_trabalho_inicio', '')
            dia_fim = c.get('dia_trabalho_fim', '')
        else:
            dias_antigo = c.get('dias_trabalho', '')
            dia_inicio = ""
            dia_fim = ""
            if dias_antigo:
                partes = dias_antigo.replace(" a ", " - ").replace(" à ", " - ").split(" - ")
                if len(partes) >= 2:
                    dia_inicio = partes[0].strip()
                    dia_fim = partes[1].strip()
                elif dias_antigo in DIAS_SEMANA:
                    dia_inicio = dias_antigo

        self.campos['dia_trabalho_inicio'] = criar_dropdown("Dia Inicial", DIAS_SEMANA, dia_inicio if dia_inicio in DIAS_SEMANA else None, 215)
        self.campos['dia_trabalho_fim'] = criar_dropdown("Dia Final", DIAS_SEMANA, dia_fim if dia_fim in DIAS_SEMANA else None, 215)

        # Intervalo - dois campos (início e fim)
        # Dados temporários guardam campos separados (intervalo_inicio, intervalo_fim)
        if c.get('intervalo_inicio') or c.get('intervalo_fim'):
            intervalo_inicio = c.get('intervalo_inicio', '')
            intervalo_fim = c.get('intervalo_fim', '')
        else:
            intervalo_antigo = c.get('intervalo', '')
            intervalo_inicio = ""
            intervalo_fim = ""
            if intervalo_antigo:
                partes = intervalo_antigo.replace(" às ", " - ").replace(" a ", " - ").split(" - ")
                if len(partes) >= 2:
                    intervalo_inicio = partes[0].strip()
                    intervalo_fim = partes[1].strip()
                else:
                    intervalo_inicio = intervalo_antigo

        self.campos['intervalo_inicio'] = criar_campo_texto("Intervalo Início", intervalo_inicio, 180, hint_text="Ex: 12:00")
        self.campos['intervalo_fim'] = criar_campo_texto("Intervalo Fim", intervalo_fim, 180, hint_text="Ex: 13:00")

        # Benefícios (removido vale_refeicao)
        self.campos['vale_transporte'] = ft.Checkbox(label="Vale Transporte", value=bool(c.get('vale_transporte')))
        self.campos['vale_alimentacao'] = ft.Checkbox(label="Vale Alimentação", value=bool(c.get('vale_alimentacao')))
        self.campos['assistencia_medica'] = ft.Checkbox(label="Assist. Médica", value=bool(c.get('assistencia_medica')))
        self.campos['assistencia_odontologica'] = ft.Checkbox(label="Assist. Odontológica", value=bool(c.get('assistencia_odontologica')))
        self.campos['seguro_vida'] = ft.Checkbox(label="Seguro de Vida", value=bool(c.get('seguro_vida')))

        # Bancários
        self.campos['tipo_conta'] = criar_dropdown("Tipo Conta", TIPOS_CONTA, c.get('tipo_conta'), 240)
        self.campos['banco'] = criar_campo_texto("Banco", c.get('banco', ''), 360)
        self.campos['agencia'] = criar_campo_texto("Agência", c.get('agencia', ''), 215)
        self.campos['conta'] = criar_campo_texto("Conta", c.get('conta', ''), 240)

        # Observações
        self.campos['observacoes_gerais'] = criar_campo_texto("Observações Gerais", c.get('observacoes_gerais', ''), 960, multiline=True)

    def _on_deficiencia_change(self, e):
        """Callback quando tipo de deficiência muda."""
        self.campos['deficiencia_outros'].visible = e.control.value == "Outros"
        self.page.update()

    def _on_grau_instrucao_change(self, e):
        """Callback quando grau de instrução muda - mostra/esconde campo curso_formacao."""
        graus_com_curso = ["Superior Incompleto", "Superior Completo", "Pós-Graduação", "Mestrado", "Doutorado"]
        self.campos['curso_formacao'].visible = e.control.value in graus_com_curso
        self.page.update()

    def _on_tipo_contrato_change(self, e):
        """Callback quando tipo de contrato muda."""
        is_experiencia = e.control.value == "Contrato de Experiência"
        self.campos['prazo_experiencia'].visible = is_experiencia
        self.campos['prorrogacao'].visible = is_experiencia
        self.container_experiencia.visible = is_experiencia
        self.page.update()

    def _atualizar_lista_dependentes(self):
        """Atualiza a lista visual de dependentes."""
        self.dependentes_container.controls.clear()

        if not self.dependentes_lista:
            self.dependentes_container.controls.append(
                ft.Text("Nenhum dependente cadastrado", italic=True, color=ft.Colors.GREY)
            )
        else:
            for i, dep in enumerate(self.dependentes_lista):
                dep_dict = dict(dep) if hasattr(dep, 'keys') else dep
                self.dependentes_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(dep_dict.get('nome', ''), weight=ft.FontWeight.BOLD),
                                ft.Text(f"{dep_dict.get('parentesco', '')} - CPF: {formatar_cpf(dep_dict.get('cpf', ''))} - Nasc: {formatar_data_br(dep_dict.get('data_nascimento', ''))}", size=12),
                            ], expand=True, spacing=2),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color=COR_SECUNDARIA,
                                tooltip="Editar dependente",
                                on_click=lambda e, idx=i: self._editar_dependente(idx),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=COR_ERRO,
                                tooltip="Remover dependente",
                                on_click=lambda e, idx=i: self._remover_dependente(idx),
                            ),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                    )
                )

    def _adicionar_dependente(self, e):
        """Abre diálogo para adicionar dependente."""
        nome_dep = ft.TextField(label="Nome do Dependente *", width=300)
        parentesco_dep = criar_dropdown("Parentesco *", PARENTESCOS, None, 200)
        cpf_dep = ft.TextField(label="CPF", width=150)
        data_nasc_dep = ft.TextField(label="Data Nascimento", width=150, hint_text="DD/MM/AAAA")

        def salvar_dependente(ev):
            if not nome_dep.value or not parentesco_dep.value:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Nome e Parentesco são obrigatórios!"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()
                return

            novo_dep = {
                'nome': nome_dep.value,
                'parentesco': parentesco_dep.value,
                'cpf': re.sub(r'\D', '', cpf_dep.value or ''),
                'data_nascimento': formatar_data_db(data_nasc_dep.value),
            }
            self.dependentes_lista.append(novo_dep)
            self._atualizar_lista_dependentes()
            dialog.open = False
            self.page.update()

        def cancelar(ev):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Adicionar Dependente"),
            content=ft.Container(
                content=ft.Column([
                    nome_dep,
                    ft.Row([parentesco_dep, data_nasc_dep], wrap=True),
                    cpf_dep,
                ], spacing=15),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Salvar", on_click=salvar_dependente, bgcolor=COR_SUCESSO, color="white"),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _editar_dependente(self, index: int):
        """Abre diálogo para editar dependente."""
        if index < 0 or index >= len(self.dependentes_lista):
            return

        dep = self.dependentes_lista[index]
        dep_dict = dict(dep) if hasattr(dep, 'keys') else dep

        nome_dep = ft.TextField(label="Nome do Dependente *", width=300, value=dep_dict.get('nome', ''))
        parentesco_dep = criar_dropdown("Parentesco *", PARENTESCOS, dep_dict.get('parentesco'), 200)
        cpf_dep = ft.TextField(label="CPF", width=150, value=dep_dict.get('cpf', ''))
        data_nasc_dep = ft.TextField(label="Data Nascimento", width=150, hint_text="DD/MM/AAAA",
                                     value=formatar_data_br(dep_dict.get('data_nascimento', '')))

        def salvar_dependente(ev):
            if not nome_dep.value or not parentesco_dep.value:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Nome e Parentesco são obrigatórios!"), bgcolor=COR_ERRO)
                self.page.snack_bar.open = True
                self.page.update()
                return

            self.dependentes_lista[index] = {
                'id': dep_dict.get('id'),  # Manter ID se existir
                'nome': nome_dep.value,
                'parentesco': parentesco_dep.value,
                'cpf': re.sub(r'\D', '', cpf_dep.value or ''),
                'data_nascimento': formatar_data_db(data_nasc_dep.value),
            }
            self._atualizar_lista_dependentes()
            dialog.open = False
            self.page.update()

        def cancelar(ev):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Dependente"),
            content=ft.Container(
                content=ft.Column([
                    nome_dep,
                    ft.Row([parentesco_dep, data_nasc_dep], wrap=True),
                    cpf_dep,
                ], spacing=15),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Salvar", on_click=salvar_dependente, bgcolor=COR_SUCESSO, color="white"),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _remover_dependente(self, index: int):
        """Remove um dependente da lista."""
        if 0 <= index < len(self.dependentes_lista):
            self.dependentes_lista.pop(index)
            self._atualizar_lista_dependentes()
            self.page.update()

    def _criar_botoes_acao(self):
        botoes = [
            ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=self._salvar,
                             bgcolor=COR_SUCESSO, color="white", height=45),
            ft.OutlinedButton("Cancelar", icon=ft.Icons.CANCEL, on_click=self._cancelar, height=45),
        ]

        # Adicionar botão Limpar apenas para novo colaborador (não em edição)
        if not self.colaborador_id:
            botoes.insert(1, ft.ElevatedButton(
                "Limpar",
                icon=ft.Icons.CLEAR_ALL,
                on_click=self._limpar_formulario,
                bgcolor=COR_ALERTA,
                color="white",
                height=45,
            ))

        return ft.Container(
            content=ft.Row(botoes, spacing=10, alignment=ft.MainAxisAlignment.END),
            padding=15, bgcolor="white", border_radius=8,
        )

    def _formatar_cpf_campo(self, campo):
        """Formata o valor de um campo de CPF no formato 000.000.000-00."""
        valor = campo.value or ''

        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)

        # Limitar a 11 dígitos
        apenas_numeros = apenas_numeros[:11]

        # Formatar como CPF: 000.000.000-00
        cpf_formatado = ''
        for i, digito in enumerate(apenas_numeros):
            if i == 3 or i == 6:
                cpf_formatado += '.'
            elif i == 9:
                cpf_formatado += '-'
            cpf_formatado += digito

        # Atualizar o campo apenas se o valor mudou (evitar loop infinito)
        if campo.value != cpf_formatado:
            campo.value = cpf_formatado
            self.page.update()

        return apenas_numeros

    def _formatar_cpf_generico(self, e):
        """Formata CPF automaticamente (para campos de CPF da mãe/pai)."""
        self._formatar_cpf_campo(e.control)

    def _formatar_cep_valor(self, valor: str) -> str:
        """Formata um valor de CEP no formato 00000-000."""
        if not valor:
            return ""
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        # Limitar a 8 dígitos
        apenas_numeros = apenas_numeros[:8]
        # Formatar como CEP: 00000-000
        if len(apenas_numeros) > 5:
            return f"{apenas_numeros[:5]}-{apenas_numeros[5:]}"
        return apenas_numeros

    def _on_cep_change(self, e):
        """Formata o CEP automaticamente no formato 00000-000."""
        campo = e.control
        valor = campo.value or ''
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        # Limitar a 8 dígitos
        apenas_numeros = apenas_numeros[:8]
        # Formatar como CEP: 00000-000
        cep_formatado = ''
        for i, digito in enumerate(apenas_numeros):
            if i == 5:
                cep_formatado += '-'
            cep_formatado += digito
        # Atualizar o campo apenas se o valor mudou (evitar loop infinito)
        if campo.value != cep_formatado:
            campo.value = cep_formatado
            self.page.update()

    def _formatar_celular_valor(self, valor: str) -> str:
        """Formata um valor de celular no formato (00) 9 0000-0000."""
        if not valor:
            return ""
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        # Limitar a 11 dígitos
        apenas_numeros = apenas_numeros[:11]
        # Formatar como celular: (00) 9 0000-0000
        if len(apenas_numeros) == 0:
            return ""
        elif len(apenas_numeros) <= 2:
            return f"({apenas_numeros}"
        elif len(apenas_numeros) <= 3:
            return f"({apenas_numeros[:2]}) {apenas_numeros[2:]}"
        elif len(apenas_numeros) <= 7:
            return f"({apenas_numeros[:2]}) {apenas_numeros[2]} {apenas_numeros[3:]}"
        else:
            return f"({apenas_numeros[:2]}) {apenas_numeros[2]} {apenas_numeros[3:7]}-{apenas_numeros[7:]}"

    def _on_celular_change(self, e):
        """Formata o celular automaticamente no formato (00) 9 0000-0000."""
        campo = e.control
        valor = campo.value or ''
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        # Limitar a 11 dígitos
        apenas_numeros = apenas_numeros[:11]
        # Formatar como celular: (00) 9 0000-0000
        celular_formatado = ''
        for i, digito in enumerate(apenas_numeros):
            if i == 0:
                celular_formatado += '('
            if i == 2:
                celular_formatado += ') '
            if i == 3:
                celular_formatado += ' '
            if i == 7:
                celular_formatado += '-'
            celular_formatado += digito
        # Atualizar o campo apenas se o valor mudou (evitar loop infinito)
        if campo.value != celular_formatado:
            campo.value = celular_formatado
            self.page.update()

    def _on_data_change(self, e):
        """Formata a data automaticamente no formato DD/MM/AAAA."""
        campo = e.control
        valor = campo.value or ''
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        # Limitar a 8 dígitos
        apenas_numeros = apenas_numeros[:8]
        # Formatar como data: DD/MM/AAAA
        data_formatada = ''
        for i, digito in enumerate(apenas_numeros):
            if i == 2 or i == 4:
                data_formatada += '/'
            data_formatada += digito
        # Atualizar o campo apenas se o valor mudou (evitar loop infinito)
        if campo.value != data_formatada:
            campo.value = data_formatada
            self.page.update()

    def _formatar_salario_valor(self, valor) -> str:
        """Formata um valor de salário no formato R$ 0.000,00."""
        if not valor:
            return ""
        # Se for número, converter para string
        if isinstance(valor, (int, float)):
            # Formatar como moeda brasileira
            valor_str = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {valor_str}"
        # Se for string, tentar extrair o valor numérico
        valor_str = str(valor)
        # Remover tudo exceto números e vírgula/ponto
        apenas_numeros = re.sub(r'[^\d]', '', valor_str)
        if not apenas_numeros:
            return ""
        # Converter para centavos e formatar
        centavos = int(apenas_numeros)
        reais = centavos / 100
        valor_formatado = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado}"

    def _on_salario_change(self, e):
        """Formata o salário automaticamente no formato R$ 0.000,00."""
        campo = e.control
        valor = campo.value or ''
        # Remover tudo que não é número
        apenas_numeros = re.sub(r'\D', '', valor)
        if not apenas_numeros:
            if campo.value != '':
                campo.value = ''
                self.page.update()
            return
        # Converter para centavos e depois para reais
        centavos = int(apenas_numeros)
        reais = centavos / 100
        # Formatar como moeda brasileira: R$ 0.000,00
        valor_formatado = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        salario_formatado = f"R$ {valor_formatado}"
        # Atualizar o campo apenas se o valor mudou (evitar loop infinito)
        if campo.value != salario_formatado:
            campo.value = salario_formatado
            self.page.update()

    def _on_cpf_change(self, e):
        """Formata o CPF automaticamente e verifica blocklist/duplicidade."""
        apenas_numeros = self._formatar_cpf_campo(e.control)

        # Verificar blocklist e duplicidade quando CPF estiver completo
        if len(apenas_numeros) == 11:
            # Verificar na blocklist
            BlocklistChecker.verificar(apenas_numeros, self.page)

            # Verificar se CPF já existe
            colaborador_existente = db.verificar_cpf_existente(apenas_numeros, self.colaborador_id)
            if colaborador_existente:
                self._mostrar_alerta_cpf_duplicado(colaborador_existente)

    def _mostrar_alerta_cpf_duplicado(self, colaborador_existente):
        """Mostra alerta quando o CPF já existe no sistema."""
        def fechar(ev):
            dialog.open = False
            self.page.update()

        status = colaborador_existente.get('status', 'ATIVO')
        cor_status = COR_SUCESSO if status == 'ATIVO' else COR_ERRO

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=COR_ERRO, size=30),
                ft.Text("CPF já cadastrado!", color=COR_ERRO),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Este CPF já está cadastrado no sistema:"),
                    ft.Divider(height=15),
                    ft.Text(colaborador_existente.get('nome_completo', ''), weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"CPF: {formatar_cpf(colaborador_existente.get('cpf', ''))}", size=14),
                    ft.Container(
                        content=ft.Text(f"Status: {status}", color="white", size=12),
                        bgcolor=cor_status,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=4,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Não é possível cadastrar dois colaboradores com o mesmo CPF.",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_700,
                    ),
                ], spacing=8),
                width=350,
            ),
            actions=[ft.ElevatedButton("Entendido", on_click=fechar, bgcolor=COR_PRIMARIA, color="white")],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _mostrar_alerta_blocklist(self, registros_blocklist):
        """Mostra alerta quando o CPF está na blocklist, impedindo o cadastro."""
        def fechar(ev):
            dialog.open = False
            self.page.update()

        # Pegar o registro mais recente
        registro = registros_blocklist[0]

        # Formatar informações do histórico
        historico_items = []
        for reg in registros_blocklist:
            empresa = reg.get('empresa_nome', 'Não informada')
            data_deslig = formatar_data_br(reg.get('data_desligamento', '')) if reg.get('data_desligamento') else 'Não informada'
            observacoes = reg.get('observacoes', '') or 'Sem observações'

            historico_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BUSINESS, size=16, color=COR_PRIMARIA),
                            ft.Text(empresa, weight=ft.FontWeight.W_500, size=13),
                        ], spacing=5),
                        ft.Text(f"Desligamento: {data_deslig}", size=12, color=ft.Colors.GREY_700),
                        ft.Text(f"Motivo: {observacoes}", size=12, italic=True, color=ft.Colors.RED_700),
                    ], spacing=3),
                    padding=ft.padding.all(8),
                    bgcolor="#ffebee",
                    border_radius=6,
                    margin=ft.margin.only(bottom=5),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.BLOCK, color=COR_ERRO, size=30),
                ft.Text("CPF na Blocklist!", color=COR_ERRO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Este CPF está na lista de bloqueio do sistema.",
                        size=14,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "NÃO É PERMITIDO cadastrar este colaborador.",
                            color="white",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=COR_ERRO,
                        padding=ft.padding.all(10),
                        border_radius=6,
                    ),
                    ft.Divider(height=15),
                    ft.Text("Histórico na Blocklist:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Container(
                        content=ft.Column(historico_items, spacing=5, scroll=ft.ScrollMode.AUTO),
                        height=150 if len(registros_blocklist) > 2 else None,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Entre em contato com o RH para mais informações.",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_700,
                    ),
                ], spacing=8),
                width=400,
            ),
            actions=[ft.ElevatedButton("Entendido", on_click=fechar, bgcolor=COR_ERRO, color="white")],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _obter_empresa_id(self, nome_empresa: str):
        empresas = db.listar_empresas()
        for emp in empresas:
            if emp['razao_social'] == nome_empresa:
                return emp['id']
        return None

    def _coletar_dados(self) -> dict:
        def get_valor(campo):
            if isinstance(campo, ft.Checkbox):
                return 1 if campo.value else 0
            return campo.value if hasattr(campo, 'value') and campo.value else None

        def get_float(campo):
            val = get_valor(campo)
            if val:
                try:
                    # Remover "R$ " e formatar número brasileiro para float
                    val_str = str(val).replace('R$', '').replace(' ', '').strip()
                    # Remover pontos de milhar e trocar vírgula por ponto
                    val_str = val_str.replace('.', '').replace(',', '.')
                    return float(val_str)
                except:
                    return None
            return None

        def get_int(campo):
            val = get_valor(campo)
            if val:
                try: return int(val)
                except: return None
            return None

        dados = {
            'empresa_id': self._obter_empresa_id(get_valor(self.campos['empresa'])),
            'foto_path': self.foto_path,
            'nome_completo': get_valor(self.campos['nome_completo']),
            'endereco': get_valor(self.campos['endereco']),
            'numero': get_valor(self.campos['numero']),
            'complemento': get_valor(self.campos['complemento']),
            'bairro': get_valor(self.campos['bairro']),
            'cep': get_valor(self.campos['cep']),
            'cidade': get_valor(self.campos['cidade']),
            'uf_endereco': get_valor(self.campos['uf_endereco']),
            'telefone': get_valor(self.campos['telefone']),
            'celular': get_valor(self.campos['celular']),
            'email': get_valor(self.campos['email']),
            'data_nascimento': formatar_data_db(get_valor(self.campos['data_nascimento'])),
            'naturalidade': get_valor(self.campos['naturalidade']),
            'uf_naturalidade': get_valor(self.campos['uf_naturalidade']),
            'sexo': get_valor(self.campos['sexo']),
            'grau_instrucao': get_valor(self.campos['grau_instrucao']),
            'curso_formacao': get_valor(self.campos['curso_formacao']),
            'estado_civil': get_valor(self.campos['estado_civil']),
            'deficiencia': get_valor(self.campos['deficiencia_outros']) if get_valor(self.campos['deficiencia_tipo']) == "Outros" else get_valor(self.campos['deficiencia_tipo']),
            'nome_mae': get_valor(self.campos['nome_mae']),
            'cpf_mae': re.sub(r'\D', '', get_valor(self.campos['cpf_mae']) or '') or None,
            'nome_pai': get_valor(self.campos['nome_pai']),
            'cpf_pai': re.sub(r'\D', '', get_valor(self.campos['cpf_pai']) or '') or None,
            'cpf': re.sub(r'\D', '', get_valor(self.campos['cpf']) or ''),
            'rg': get_valor(self.campos['rg']),
            'orgao_emissor_rg': get_valor(self.campos['orgao_emissor_rg']),
            'uf_rg': get_valor(self.campos['uf_rg']),
            'carteira_profissional': get_valor(self.campos['carteira_profissional']),
            'serie_carteira': get_valor(self.campos['serie_carteira']),
            'uf_carteira': get_valor(self.campos['uf_carteira']),
            'pis': get_valor(self.campos['pis']),
            'titulo_eleitor': get_valor(self.campos['titulo_eleitor']),
            'zona_eleitor': get_valor(self.campos['zona_eleitor']),
            'secao_eleitor': get_valor(self.campos['secao_eleitor']),
            'habilitacao': get_valor(self.campos['habilitacao']),
            'tipo_cnh': get_valor(self.campos['tipo_cnh']),
            'validade_cnh': formatar_data_db(get_valor(self.campos['validade_cnh'])),
            'reservista': get_valor(self.campos['reservista']),
            # Dados do Último Registro
            'empresa_ultimo_emprego': get_valor(self.campos['empresa_ultimo_emprego']),
            'cnpj_ultimo_emprego': get_valor(self.campos['cnpj_ultimo_emprego']),
            'data_admissao_ultimo': formatar_data_db(get_valor(self.campos['data_admissao_ultimo'])),
            'data_saida_ultimo': formatar_data_db(get_valor(self.campos['data_saida_ultimo'])),
            'primeiro_registro': get_valor(self.campos['primeiro_registro']),
            'data_ultima_contribuicao_sindical': formatar_data_db(get_valor(self.campos['data_ultima_contribuicao_sindical'])),
            # Exame Médico (ASO)
            'data_exame_medico': formatar_data_db(get_valor(self.campos['data_exame_medico'])),
            'tipo_exames': get_valor(self.campos['tipo_exames']),
            'nome_medico': get_valor(self.campos['nome_medico']),
            'crm': get_valor(self.campos['crm']),
            'uf_crm': get_valor(self.campos['uf_crm']),
            'data_admissao': formatar_data_db(get_valor(self.campos['data_admissao'])),
            'funcao': get_valor(self.campos['funcao']),
            'departamento': get_valor(self.campos['departamento']),
            'salario': get_float(self.campos['salario']),
            'forma_pagamento': get_valor(self.campos['forma_pagamento']),
            'prazo_experiencia': get_int(self.campos['prazo_experiencia']) if get_valor(self.campos['tipo_contrato']) == "Contrato de Experiência" else None,
            'prorrogacao': get_int(self.campos['prorrogacao']) if get_valor(self.campos['tipo_contrato']) == "Contrato de Experiência" else None,
            'tipo_contrato': get_valor(self.campos['tipo_contrato']),
            'horario_trabalho': f"{get_valor(self.campos['horario_chegada']) or ''} às {get_valor(self.campos['horario_saida']) or ''}".strip() if get_valor(self.campos['horario_chegada']) or get_valor(self.campos['horario_saida']) else None,
            'dias_trabalho': f"{get_valor(self.campos['dia_trabalho_inicio']) or ''} a {get_valor(self.campos['dia_trabalho_fim']) or ''}".strip() if get_valor(self.campos['dia_trabalho_inicio']) or get_valor(self.campos['dia_trabalho_fim']) else None,
            'intervalo': f"{get_valor(self.campos['intervalo_inicio']) or ''} às {get_valor(self.campos['intervalo_fim']) or ''}".strip() if get_valor(self.campos['intervalo_inicio']) or get_valor(self.campos['intervalo_fim']) else None,
            'vale_transporte': get_valor(self.campos['vale_transporte']),
            'vale_alimentacao': get_valor(self.campos['vale_alimentacao']),
            'assistencia_medica': get_valor(self.campos['assistencia_medica']),
            'assistencia_odontologica': get_valor(self.campos['assistencia_odontologica']),
            'seguro_vida': get_valor(self.campos['seguro_vida']),
            'tipo_conta': get_valor(self.campos['tipo_conta']),
            'banco': get_valor(self.campos['banco']),
            'agencia': get_valor(self.campos['agencia']),
            'conta': get_valor(self.campos['conta']),
            'observacoes_gerais': get_valor(self.campos['observacoes_gerais']),
        }
        return {k: v for k, v in dados.items() if v is not None}

    def _salvar(self, e):
        # Verificar permissão
        if not db.usuario_pode_editar():
            self._mostrar_erro_salvamento("Você não tem permissão para salvar dados. Verifique se está logado corretamente.")
            return

        try:
            dados = self._coletar_dados()
        except Exception as ex:
            self._mostrar_erro_salvamento(f"Erro ao coletar dados: {str(ex)}")
            return

        # Validar campos obrigatórios e identificar quais estão faltando
        campos_faltando = []
        if not dados.get('nome_completo'):
            campos_faltando.append("Nome Completo")
        if not dados.get('cpf'):
            campos_faltando.append("CPF")
        if not dados.get('data_admissao'):
            campos_faltando.append("Data de Admissão")
        if not dados.get('funcao'):
            campos_faltando.append("Função")

        if campos_faltando:
            self._mostrar_erro_salvamento(f"Campos obrigatórios não preenchidos:\n- " + "\n- ".join(campos_faltando))
            return

        # Validar CPF: verificar dígitos verificadores
        cpf_limpo = dados.get('cpf', '')
        cpf_valido, erro_cpf = validar_cpf(cpf_limpo)
        if not cpf_valido:
            self._mostrar_erro_salvamento(f"CPF inválido: {erro_cpf}")
            return

        # Verificar se CPF já existe (bloquear salvamento)
        colaborador_existente = db.verificar_cpf_existente(cpf_limpo, self.colaborador_id)
        if colaborador_existente:
            self._mostrar_alerta_cpf_duplicado(colaborador_existente)
            return

        # Verificar se CPF está na blocklist (bloquear salvamento para novos cadastros)
        if not self.colaborador_id:  # Apenas para novos cadastros
            registros_blocklist = db.verificar_blocklist(cpf_limpo)
            if registros_blocklist:
                self._mostrar_alerta_blocklist(registros_blocklist)
                return

        try:
            if self.colaborador_id:
                # Obter dados antigos para registrar histórico
                dados_antigos = dict(self.colaborador) if self.colaborador else {}

                # Verificar se a data de admissão mudou
                data_admissao_antiga = self.colaborador.get('data_admissao') if self.colaborador else None
                data_admissao_nova = dados.get('data_admissao')
                tipo_contrato_antigo = self.colaborador.get('tipo_contrato') if self.colaborador else None
                tipo_contrato_novo = dados.get('tipo_contrato')

                db.atualizar_colaborador(self.colaborador_id, dados)

                # Registrar alterações no histórico
                db.registrar_alteracoes_colaborador(self.colaborador_id, dados, dados_antigos)

                # Se mudou de Contrato de Experiência para outro tipo, finalizar contrato
                if tipo_contrato_antigo == 'Contrato de Experiência' and tipo_contrato_novo != 'Contrato de Experiência':
                    db.finalizar_contrato_experiencia(self.colaborador_id)
                colaborador_id = self.colaborador_id

                # Se a data de admissão mudou, atualizar as férias
                if data_admissao_nova and data_admissao_antiga != data_admissao_nova:
                    db.atualizar_ferias_por_admissao(colaborador_id, data_admissao_nova)

                # Verificar se mudou para contrato de experiência ou se os dados mudaram
                if tipo_contrato_novo == "Contrato de Experiência" and dados.get('data_admissao') and dados.get('prazo_experiencia'):
                    # Verificar se já existe contrato vigente
                    contrato_existente = db.obter_contrato_colaborador(colaborador_id)
                    if not contrato_existente:
                        # Criar novo contrato
                        db.criar_contrato_experiencia(colaborador_id, dados['data_admissao'], dados['prazo_experiencia'], dados.get('prorrogacao'))
                    else:
                        # Atualizar contrato existente se os dados mudaram
                        from datetime import datetime, timedelta
                        inicio = datetime.strptime(dados['data_admissao'], '%Y-%m-%d')
                        # O dia de início conta como dia 1, então o fim é início + prazo - 1
                        fim_inicial = inicio + timedelta(days=dados['prazo_experiencia'] - 1)
                        fim_prorrogacao = None
                        if dados.get('prorrogacao'):
                            # A prorrogação começa no dia seguinte ao fim do período inicial
                            fim_prorrogacao = fim_inicial + timedelta(days=dados['prorrogacao'])

                        db.atualizar_contrato(contrato_existente['id'], {
                            'data_inicio': dados['data_admissao'],
                            'prazo_inicial': dados['prazo_experiencia'],
                            'data_fim_inicial': fim_inicial.strftime('%Y-%m-%d'),
                            'prorrogacao': dados.get('prorrogacao'),
                            'data_fim_prorrogacao': fim_prorrogacao.strftime('%Y-%m-%d') if fim_prorrogacao else None,
                        })

                msg = "Colaborador atualizado!"
            else:
                colaborador_id = db.criar_colaborador(dados)
                if dados.get('tipo_contrato') == "Contrato de Experiência" and dados.get('prazo_experiencia') and dados.get('data_admissao'):
                    db.criar_contrato_experiencia(colaborador_id, dados['data_admissao'], dados['prazo_experiencia'], dados.get('prorrogacao'))
                if dados.get('data_admissao'):
                    db.criar_periodo_ferias(colaborador_id, dados['data_admissao'])
                msg = "Colaborador cadastrado!"

            # Salvar dependentes
            # Primeiro remove os existentes (para edição)
            if self.colaborador_id:
                deps_existentes = db.listar_dependentes(self.colaborador_id)
                for dep_existente in deps_existentes:
                    db.excluir_dependente(dep_existente['id'])

            # Adiciona os novos/atualizados
            for dep in self.dependentes_lista:
                dep_dict = dict(dep) if hasattr(dep, 'keys') else dep
                db.adicionar_dependente(colaborador_id, dep_dict)

            self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=COR_SUCESSO)
            self.page.snack_bar.open = True
            self.page.update()

            if self.on_salvar_callback:
                self.on_salvar_callback()
        except Exception as ex:
            self._mostrar_erro_salvamento(f"Erro ao salvar: {str(ex)}")

    def _mostrar_erro_salvamento(self, mensagem: str):
        """Mostra um diálogo com o motivo do erro ao salvar."""
        def fechar(ev):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=COR_ERRO, size=30),
                ft.Text("Não foi possível salvar", color=COR_ERRO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(mensagem, size=14),
                ], spacing=10),
                width=400,
                padding=10,
            ),
            actions=[ft.ElevatedButton("OK", on_click=fechar, bgcolor=COR_PRIMARIA, color="white")],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _cancelar(self, e=None):
        # Salvar dados temporários antes de sair (apenas para novo colaborador)
        if not self.colaborador_id and self.on_salvar_temp:
            dados_temp = self._coletar_dados_temp()
            self.on_salvar_temp(dados_temp, self.dependentes_lista, self.foto_path)

        if self.on_cancelar_callback:
            self.on_cancelar_callback()
        else:
            self.page.go("/")

    def _coletar_dados_temp(self) -> dict:
        """Coleta dados do formulário para armazenamento temporário."""
        def get_valor(campo):
            if isinstance(campo, ft.Checkbox):
                return 1 if campo.value else 0
            return campo.value if hasattr(campo, 'value') and campo.value else None

        # Obter nome da empresa para restaurar depois
        empresa_nome = get_valor(self.campos['empresa'])

        # Coletar valores brutos dos campos para dados temporários
        dados = {
            'empresa_nome': empresa_nome,  # Guardar nome da empresa para restauração
            'nome_completo': get_valor(self.campos['nome_completo']),
            'endereco': get_valor(self.campos['endereco']),
            'numero': get_valor(self.campos['numero']),
            'complemento': get_valor(self.campos['complemento']),
            'bairro': get_valor(self.campos['bairro']),
            'cep': get_valor(self.campos['cep']),
            'cidade': get_valor(self.campos['cidade']),
            'uf_endereco': get_valor(self.campos['uf_endereco']),
            'telefone': get_valor(self.campos['telefone']),
            'celular': get_valor(self.campos['celular']),
            'email': get_valor(self.campos['email']),
            'data_nascimento': get_valor(self.campos['data_nascimento']),
            'naturalidade': get_valor(self.campos['naturalidade']),
            'uf_naturalidade': get_valor(self.campos['uf_naturalidade']),
            'sexo': get_valor(self.campos['sexo']),
            'grau_instrucao': get_valor(self.campos['grau_instrucao']),
            'curso_formacao': get_valor(self.campos['curso_formacao']),
            'estado_civil': get_valor(self.campos['estado_civil']),
            'deficiencia_tipo': get_valor(self.campos['deficiencia_tipo']),
            'deficiencia_outros': get_valor(self.campos['deficiencia_outros']),
            'nome_mae': get_valor(self.campos['nome_mae']),
            'cpf_mae': get_valor(self.campos['cpf_mae']),
            'nome_pai': get_valor(self.campos['nome_pai']),
            'cpf_pai': get_valor(self.campos['cpf_pai']),
            'cpf': get_valor(self.campos['cpf']),
            'rg': get_valor(self.campos['rg']),
            'orgao_emissor_rg': get_valor(self.campos['orgao_emissor_rg']),
            'uf_rg': get_valor(self.campos['uf_rg']),
            'carteira_profissional': get_valor(self.campos['carteira_profissional']),
            'serie_carteira': get_valor(self.campos['serie_carteira']),
            'uf_carteira': get_valor(self.campos['uf_carteira']),
            'pis': get_valor(self.campos['pis']),
            'titulo_eleitor': get_valor(self.campos['titulo_eleitor']),
            'zona_eleitor': get_valor(self.campos['zona_eleitor']),
            'secao_eleitor': get_valor(self.campos['secao_eleitor']),
            'habilitacao': get_valor(self.campos['habilitacao']),
            'tipo_cnh': get_valor(self.campos['tipo_cnh']),
            'validade_cnh': get_valor(self.campos['validade_cnh']),
            'reservista': get_valor(self.campos['reservista']),
            # Dados do Último Registro
            'empresa_ultimo_emprego': get_valor(self.campos['empresa_ultimo_emprego']),
            'cnpj_ultimo_emprego': get_valor(self.campos['cnpj_ultimo_emprego']),
            'data_admissao_ultimo': get_valor(self.campos['data_admissao_ultimo']),
            'data_saida_ultimo': get_valor(self.campos['data_saida_ultimo']),
            'primeiro_registro': get_valor(self.campos['primeiro_registro']),
            'data_ultima_contribuicao_sindical': get_valor(self.campos['data_ultima_contribuicao_sindical']),
            # Exame Médico (ASO)
            'data_exame_medico': get_valor(self.campos['data_exame_medico']),
            'tipo_exames': get_valor(self.campos['tipo_exames']),
            'nome_medico': get_valor(self.campos['nome_medico']),
            'crm': get_valor(self.campos['crm']),
            'uf_crm': get_valor(self.campos['uf_crm']),
            'data_admissao': get_valor(self.campos['data_admissao']),
            'funcao': get_valor(self.campos['funcao']),
            'departamento': get_valor(self.campos['departamento']),
            'salario': get_valor(self.campos['salario']),
            'forma_pagamento': get_valor(self.campos['forma_pagamento']),
            'tipo_contrato': get_valor(self.campos['tipo_contrato']),
            'prazo_experiencia': get_valor(self.campos['prazo_experiencia']),
            'prorrogacao': get_valor(self.campos['prorrogacao']),
            'horario_chegada': get_valor(self.campos['horario_chegada']),
            'horario_saida': get_valor(self.campos['horario_saida']),
            'intervalo_inicio': get_valor(self.campos['intervalo_inicio']),
            'intervalo_fim': get_valor(self.campos['intervalo_fim']),
            'dia_trabalho_inicio': get_valor(self.campos['dia_trabalho_inicio']),
            'dia_trabalho_fim': get_valor(self.campos['dia_trabalho_fim']),
            'vale_transporte': get_valor(self.campos['vale_transporte']),
            'vale_alimentacao': get_valor(self.campos['vale_alimentacao']),
            'assistencia_medica': get_valor(self.campos['assistencia_medica']),
            'assistencia_odontologica': get_valor(self.campos['assistencia_odontologica']),
            'seguro_vida': get_valor(self.campos['seguro_vida']),
            'tipo_conta': get_valor(self.campos['tipo_conta']),
            'banco': get_valor(self.campos['banco']),
            'agencia': get_valor(self.campos['agencia']),
            'conta': get_valor(self.campos['conta']),
            'observacoes_gerais': get_valor(self.campos['observacoes_gerais']),
        }
        # Remover valores None para não poluir
        return {k: v for k, v in dados.items() if v is not None}

    def _limpar_formulario(self, e=None):
        """Limpa todos os campos do formulário e os dados temporários."""
        # Limpar campos de texto e dropdowns
        for nome, campo in self.campos.items():
            if isinstance(campo, ft.Checkbox):
                campo.value = False
            elif hasattr(campo, 'value'):
                campo.value = None if isinstance(campo, ft.Dropdown) else ''

        # Limpar dependentes
        self.dependentes_lista = []
        self._atualizar_lista_dependentes()

        # Limpar foto
        self.foto_path = None
        self._criar_foto_widget()

        # Limpar dados temporários no app
        if self.on_limpar_callback:
            self.on_limpar_callback()

        # Resetar visibilidade dos campos condicionais
        self.campos['prazo_experiencia'].visible = False
        self.campos['prorrogacao'].visible = False
        self.container_experiencia.visible = False
        self.campos['deficiencia_outros'].visible = False
        self.campos['curso_formacao'].visible = False

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Formulário limpo!"),
            bgcolor=COR_SECUNDARIA
        )
        self.page.snack_bar.open = True
        self.page.update()
