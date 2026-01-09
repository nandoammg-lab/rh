"""
Módulo de Geração de PDF - Sistema de Gestão de RH
RENOVO Montagens Industriais
Código do documento: FREG-RH-0001
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, Frame, PageTemplate, BaseDocTemplate,
    Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class TopAlignedFrame(Frame):
    """Frame customizado que alinha conteúdo ao topo."""
    def add(self, flowable, canv, trySplit=0):
        # Chamar método pai
        result = Frame.add(self, flowable, canv, trySplit)
        return result


class FrameFiller(Flowable):
    """Flowable que preenche o espaço restante do frame, empurrando conteúdo para o topo."""
    def __init__(self):
        Flowable.__init__(self)
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        # Ocupar todo o espaço disponível restante
        self.width = availWidth
        self.height = availHeight
        return (self.width, self.height)

    def draw(self):
        # Não desenha nada, apenas ocupa espaço
        pass
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import sys


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


# Cores padrão RENOVO
COR_AZUL_ESCURO = colors.HexColor('#1a5276')
COR_AZUL_CLARO = colors.HexColor('#3498db')
COR_CINZA_CLARO = colors.HexColor('#f2f3f4')
COR_CINZA = colors.HexColor('#bdc3c7')

class PDFGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.width, self.height = A4
        self.margin = 15 * mm
        # Largura útil disponível no frame do documento
        self.content_width = self.width - 2 * self.margin
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.total_pages = 0  # Será calculado depois

    def _get_valor(self, dicionario: dict, chave: str, padrao: str = "-") -> str:
        """Retorna o valor do dicionário ou o padrão, garantindo que nunca seja None."""
        valor = dicionario.get(chave)
        if valor is None or valor == "":
            return padrao
        return str(valor)
        
    def _setup_styles(self):
        """Configura estilos personalizados."""
        self.styles.add(ParagraphStyle(
            name='TituloSecao',
            parent=self.styles['Heading2'],
            fontSize=10,
            textColor=colors.white,
            backColor=COR_AZUL_ESCURO,
            spaceAfter=0,
            spaceBefore=6,
            leftIndent=3,
            rightIndent=3,
            leading=14,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CampoLabel',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=COR_AZUL_ESCURO,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CampoValor',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Cabecalho',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='Rodape',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.gray
        ))
    
    def _criar_cabecalho(self, canvas_obj, doc):
        """Desenha o cabeçalho em cada página."""
        canvas_obj.saveState()

        # Logo da empresa
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'imagens', 'Logomarca Renovo.png')
        if os.path.exists(logo_path):
            canvas_obj.drawImage(logo_path, self.margin, self.height - 28*mm,
                                width=55*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
        else:
            # Texto como placeholder se não houver logo
            canvas_obj.setFont('Helvetica-Bold', 14)
            canvas_obj.setFillColor(COR_AZUL_ESCURO)
            canvas_obj.drawString(self.margin, self.height - 20*mm, "RENOVO")
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.drawString(self.margin, self.height - 25*mm, "MONTAGENS INDUSTRIAIS")

        # Código do documento - em itálico, duas linhas
        canvas_obj.setFont('Helvetica-Oblique', 8)
        canvas_obj.setFillColor(colors.gray)
        canvas_obj.drawRightString(self.width - self.margin, self.height - 15*mm, "FREG-RH-0001")
        canvas_obj.drawRightString(self.width - self.margin, self.height - 19*mm, "Criação: 29/11/2025")

        # Linha separadora
        canvas_obj.setStrokeColor(COR_AZUL_CLARO)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(self.margin, self.height - 30*mm,
                       self.width - self.margin, self.height - 30*mm)

        canvas_obj.restoreState()
    
    def _criar_rodape(self, canvas_obj, doc):
        """Desenha o rodapé em cada página."""
        canvas_obj.saveState()

        # Linha separadora
        canvas_obj.setStrokeColor(COR_AZUL_ESCURO)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(self.margin, 28*mm, self.width - self.margin, 28*mm)

        # Informações da empresa - cada informação em sua linha, cor azul escuro
        canvas_obj.setFillColor(COR_AZUL_ESCURO)

        # Nome da empresa em negrito
        canvas_obj.setFont('Helvetica-Bold', 7)
        canvas_obj.drawString(self.margin, 24*mm, "RENOVO MONTAGENS INDUSTRIAIS LTDA")

        # Demais informações sem negrito
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.drawString(self.margin, 20*mm, "Avenida Nunes Machado, 199, Goiana/PE")
        canvas_obj.drawString(self.margin, 16*mm, "contato@renovomontagens.com.br")
        canvas_obj.drawString(self.margin, 12*mm, "www.renovomontagens.com.br")
        canvas_obj.drawString(self.margin, 8*mm, "+55 11 93733-5522")

        # Número da página no formato "Página X/Y"
        canvas_obj.drawRightString(self.width - self.margin, 24*mm,
                                   f"Página {doc.page}/{self.total_pages}")

        canvas_obj.restoreState()
    
    def _criar_secao(self, titulo: str) -> Table:
        """Cria um cabeçalho de seção estilizado."""
        data = [[Paragraph(titulo, self.styles['TituloSecao'])]]
        # Usar 180mm como largura fixa para garantir que cabe no frame
        table = Table(data, colWidths=[180*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COR_AZUL_ESCURO),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return table
    
    def _criar_campo(self, label: str, valor: str) -> list:
        """Cria um par label/valor para a tabela."""
        return [
            Paragraph(f"<b>{label}</b>", self.styles['CampoLabel']),
            Paragraph(str(valor) if valor else "-", self.styles['CampoValor'])
        ]
    
    def _criar_tabela_campos(self, campos: list, col_widths: list = None) -> Table:
        """Cria uma tabela de campos formatada."""
        if col_widths is None:
            col_widths = [35*mm, 45*mm, 35*mm, 45*mm]
        
        table = Table(campos, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        return table
    
    def _formatar_data(self, data_str: str) -> str:
        """Formata uma data para exibição."""
        if not data_str:
            return "-"
        try:
            data = datetime.strptime(str(data_str), '%Y-%m-%d')
            return data.strftime('%d/%m/%Y')
        except:
            return str(data_str)
    
    def _formatar_moeda(self, valor) -> str:
        """Formata um valor monetário."""
        if valor is None:
            return "-"
        try:
            return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(valor)
    
    def _sim_nao(self, valor) -> str:
        """Converte 0/1 para Sim/Não. Trata também strings '0' e '1'."""
        if valor is None or valor == "" or valor == "-":
            return "Não"
        # Tratar strings "0" e "1"
        if isinstance(valor, str):
            return "Sim" if valor.strip() not in ("0", "false", "False", "não", "Não", "nao", "Nao", "") else "Não"
        return "Sim" if valor else "Não"

    def _formatar_cpf(self, cpf: str) -> str:
        """Formata um CPF para exibição (XXX.XXX.XXX-XX)."""
        if not cpf or cpf == "-":
            return "-"
        # Remove caracteres não numéricos
        cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
        if not cpf_limpo:
            return "-"
        # Normaliza para 11 dígitos
        cpf_limpo = cpf_limpo.zfill(11) if len(cpf_limpo) < 11 else cpf_limpo[:11]
        # Formata
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

    def _formatar_telefone(self, telefone: str) -> str:
        """Formata um telefone para exibição."""
        if not telefone or telefone == "-":
            return "-"
        # Remove caracteres não numéricos
        tel_limpo = ''.join(filter(str.isdigit, str(telefone)))
        if not tel_limpo:
            return "-"
        # Formata conforme quantidade de dígitos
        if len(tel_limpo) == 11:  # Celular com DDD
            return f"({tel_limpo[:2]}) {tel_limpo[2:7]}-{tel_limpo[7:]}"
        elif len(tel_limpo) == 10:  # Fixo com DDD
            return f"({tel_limpo[:2]}) {tel_limpo[2:6]}-{tel_limpo[6:]}"
        elif len(tel_limpo) == 9:  # Celular sem DDD
            return f"{tel_limpo[:5]}-{tel_limpo[5:]}"
        elif len(tel_limpo) == 8:  # Fixo sem DDD
            return f"{tel_limpo[:4]}-{tel_limpo[4:]}"
        else:
            return str(telefone)

    def _formatar_cep(self, cep: str) -> str:
        """Formata um CEP para exibição (XXXXX-XXX)."""
        if not cep or cep == "-":
            return "-"
        # Remove caracteres não numéricos
        cep_limpo = ''.join(filter(str.isdigit, str(cep)))
        if not cep_limpo or len(cep_limpo) < 8:
            return str(cep)
        return f"{cep_limpo[:5]}-{cep_limpo[5:8]}"

    def _formatar_cnpj(self, cnpj: str) -> str:
        """Formata um CNPJ para exibição (XX.XXX.XXX/XXXX-XX)."""
        if not cnpj or cnpj == "-":
            return "-"
        # Se já tem formatação, retorna como está
        if '.' in str(cnpj) or '/' in str(cnpj):
            return str(cnpj)
        # Remove caracteres não numéricos
        cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
        if not cnpj_limpo or len(cnpj_limpo) < 14:
            return str(cnpj)
        return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
    
    def gerar_ficha_registro(self, colaborador: dict, dependentes: list = None,
                             empresa: dict = None) -> str:
        """Gera o PDF da Ficha Registro do colaborador."""

        # Garantir que nenhum valor seja None (reportlab não aceita None em Paragraph)
        def safe_str(valor):
            if valor is None or valor == "":
                return "-"
            return str(valor)

        # Processar colaborador para garantir valores seguros
        c = {k: safe_str(v) for k, v in colaborador.items()}

        # Processar empresa se existir
        if empresa:
            empresa = {k: safe_str(v) for k, v in empresa.items()}

        # Criar documento com Frame alinhado ao topo
        # O Frame do ReportLab posiciona flowables do topo para baixo
        # bottomPadding grande garante que o conteúdo fique alinhado ao topo
        frame = Frame(
            self.margin,  # x1
            32*mm,  # y1 (bottomMargin)
            self.width - 2*self.margin,  # width
            self.height - 35*mm - 32*mm,  # height (altura disponível)
            id='normal',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            showBoundary=0  # Sem borda visível
        )

        doc = BaseDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=35*mm,
            bottomMargin=32*mm
        )

        # Template de página com frame alinhado ao topo
        def on_page(canvas_obj, doc_obj):
            self._criar_cabecalho(canvas_obj, doc_obj)
            self._criar_rodape(canvas_obj, doc_obj)

        template = PageTemplate(id='AllPages', frames=[frame], onPage=on_page)
        doc.addPageTemplates([template])
        
        story = []
        
        # =====================================================================
        # TÍTULO PRINCIPAL
        # =====================================================================
        titulo_data = [
            [Paragraph("<b>FICHA DE REGISTRO DO EMPREGADO</b>",
                      ParagraphStyle(name='Titulo', fontSize=14, alignment=TA_CENTER,
                                    textColor=COR_AZUL_ESCURO, fontName='Helvetica-Bold'))]
        ]
        titulo_table = Table(titulo_data, colWidths=[180*mm])
        titulo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COR_CINZA_CLARO),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, COR_AZUL_ESCURO),
        ]))
        story.append(titulo_table)
        story.append(Spacer(1, 5*mm))
        
        # =====================================================================
        # DADOS DA EMPRESA CONTRATANTE
        # =====================================================================
        empresa_nome = c.get('empresa_nome', '-') if c.get('empresa_nome', '-') != '-' else (empresa.get('razao_social', '-') if empresa else '-')
        empresa_cnpj = c.get('empresa_cnpj', '-') if c.get('empresa_cnpj', '-') != '-' else (empresa.get('cnpj', '-') if empresa else '-')

        empresa_data = [
            [Paragraph(f"<b>EMPRESA CONTRATANTE:</b> {empresa_nome}", self.styles['CampoValor']),
             Paragraph(f"<b>CNPJ:</b> {empresa_cnpj}", self.styles['CampoValor'])]
        ]

        empresa_table = Table(empresa_data, colWidths=[120*mm, 60*mm])
        empresa_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA),
            ('BACKGROUND', (0, 0), (-1, -1), COR_CINZA_CLARO),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(empresa_table)
        story.append(Spacer(1, 3*mm))

        # =====================================================================
        # FOTO E IDENTIFICAÇÃO DO COLABORADOR
        # =====================================================================
        foto_path = c.get('foto_path', '')

        # Criar célula da foto
        if foto_path and foto_path != '-' and os.path.exists(foto_path):
            foto = Image(foto_path, width=30*mm, height=40*mm)
        else:
            # Placeholder de foto com borda
            foto = Paragraph("<br/><br/><br/>FOTO<br/>3x4", ParagraphStyle(
                name='FotoPlaceholder',
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.gray
            ))

        # Dados principais do colaborador ao lado da foto
        dados_identificacao = [
            [Paragraph(f"<b>Nome Completo:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_completo', '-'), self.styles['CampoValor'])],
            [Paragraph(f"<b>CPF:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cpf(c.get('cpf', '-')), self.styles['CampoValor'])],
            [Paragraph(f"<b>RG:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('rg', '-'), self.styles['CampoValor'])],
            [Paragraph(f"<b>Data Nascimento:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_nascimento')), self.styles['CampoValor'])],
            [Paragraph(f"<b>Função:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('funcao', '-'), self.styles['CampoValor'])],
            [Paragraph(f"<b>Admissão:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_admissao')), self.styles['CampoValor'])],
        ]

        dados_table = Table(dados_identificacao, colWidths=[35*mm, 70*mm])
        dados_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ]))

        # Tabela principal com foto à esquerda e dados à direita
        header_data = [
            [foto, dados_table]
        ]

        header_table = Table(header_data, colWidths=[35*mm, 110*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BOX', (0, 0), (0, 0), 0.5, COR_CINZA),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, 0), 3),
            ('RIGHTPADDING', (0, 0), (0, 0), 3),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 3*mm))
        
        # =====================================================================
        # DADOS PESSOAIS
        # =====================================================================
        story.append(self._criar_secao("DADOS PESSOAIS"))
        
        col_w = [30*mm, 50*mm, 30*mm, 50*mm]
        
        dados_pessoais = [
            [Paragraph("<b>Nome Completo:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_completo', '-'), self.styles['CampoValor']),
             Paragraph("<b>CPF:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cpf(c.get('cpf', '-')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Data Nasc.:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_nascimento')), self.styles['CampoValor']),
             Paragraph("<b>Sexo:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('sexo', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Naturalidade:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('naturalidade', '-'), self.styles['CampoValor']),
             Paragraph("<b>UF:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('uf_naturalidade', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Estado Civil:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('estado_civil', '-'), self.styles['CampoValor']),
             Paragraph("<b>Data Casamento:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_casamento')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Cônjuge:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_conjuge', '-'), self.styles['CampoValor']),
             Paragraph("<b>Deficiência:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('deficiencia', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Nome da Mãe:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_mae', '-'), self.styles['CampoValor']),
             Paragraph("<b>CPF Mãe:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cpf(c.get('cpf_mae', '-')), self.styles['CampoValor'])],

            [Paragraph("<b>Nome do Pai:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_pai', '-'), self.styles['CampoValor']),
             Paragraph("<b>CPF Pai:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cpf(c.get('cpf_pai', '-')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Grau Instrução:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('grau_instrucao', '-'), self.styles['CampoValor']),
             Paragraph("<b>Curso:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('curso_formacao', '-'), self.styles['CampoValor'])],
        ]
        
        story.append(self._criar_tabela_campos(dados_pessoais, col_w))
        story.append(Spacer(1, 3*mm))

        # =====================================================================
        # ENDEREÇO (KeepTogether para não dividir a seção)
        # =====================================================================
        secao_endereco = []
        secao_endereco.append(self._criar_secao("ENDEREÇO"))
        
        endereco = [
            [Paragraph("<b>Endereço:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('endereco', '-'), self.styles['CampoValor']),
             Paragraph("<b>Número:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('numero', '-'), self.styles['CampoValor'])],

            [Paragraph("<b>Complemento:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('complemento', '-'), self.styles['CampoValor']),
             Paragraph("<b>Bairro:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('bairro', '-'), self.styles['CampoValor'])],

            [Paragraph("<b>CEP:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cep(c.get('cep', '-')), self.styles['CampoValor']),
             Paragraph("<b>Cidade:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('cidade', '-'), self.styles['CampoValor'])],

            [Paragraph("<b>UF:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('uf_endereco', '-'), self.styles['CampoValor']),
             Paragraph("<b>Telefone:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_telefone(c.get('telefone', '-')), self.styles['CampoValor'])],

            [Paragraph("<b>Celular:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_telefone(c.get('celular', '-')), self.styles['CampoValor']),
             Paragraph("<b>E-mail:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('email', '-'), self.styles['CampoValor'])],
        ]

        secao_endereco.append(self._criar_tabela_campos(endereco, col_w))
        story.append(KeepTogether(secao_endereco))

        # Preencher espaço restante para alinhar ao topo
        story.append(FrameFiller())

        # =====================================================================
        # PÁGINA 2: Inicia após ENDEREÇO
        # Conteúdo: DOCUMENTOS, EXAME MÉDICO, ÚLTIMO REGISTRO, DEPENDENTES, CONTRATO
        # =====================================================================
        story.append(PageBreak())

        # =====================================================================
        # DOCUMENTOS (KeepTogether para não dividir a seção)
        # =====================================================================
        secao_documentos = []
        secao_documentos.append(self._criar_secao("DOCUMENTOS"))
        
        documentos = [
            [Paragraph("<b>RG:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('rg', '-'), self.styles['CampoValor']),
             Paragraph("<b>Emissão:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_emissao_rg')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Órgão Emissor:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('orgao_emissor_rg', '-'), self.styles['CampoValor']),
             Paragraph("<b>UF:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('uf_rg', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>CTPS:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('carteira_profissional', '-'), self.styles['CampoValor']),
             Paragraph("<b>Série:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('serie_carteira', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>UF CTPS:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('uf_carteira', '-'), self.styles['CampoValor']),
             Paragraph("<b>Emissão:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_emissao_carteira')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Título Eleitor:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('titulo_eleitor', '-'), self.styles['CampoValor']),
             Paragraph("<b>Zona/Seção:</b>", self.styles['CampoLabel']),
             Paragraph(f"{c.get('zona_eleitor', '-')}/{c.get('secao_eleitor', '-')}", 
                      self.styles['CampoValor'])],
            
            [Paragraph("<b>CNH:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('habilitacao', '-'), self.styles['CampoValor']),
             Paragraph("<b>Tipo:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('tipo_cnh', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Expedição CNH:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_expedicao_cnh')), self.styles['CampoValor']),
             Paragraph("<b>Validade:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('validade_cnh')), self.styles['CampoValor'])],
            
            [Paragraph("<b>PIS:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('pis', '-'), self.styles['CampoValor']),
             Paragraph("<b>Cadastramento:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_cadastramento_pis')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Reservista:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('reservista', '-'), self.styles['CampoValor']),
             Paragraph("", self.styles['CampoLabel']),
             Paragraph("", self.styles['CampoValor'])],
        ]
        
        # Conselho Regional se houver
        if c.get('conselho_regional'):
            documentos.append([
                Paragraph("<b>Conselho:</b>", self.styles['CampoLabel']),
                Paragraph(f"{c.get('sigla_conselho', '')} {c.get('numero_conselho', '')}",
                         self.styles['CampoValor']),
                Paragraph("<b>Região:</b>", self.styles['CampoLabel']),
                Paragraph(c.get('regiao_conselho', '-'), self.styles['CampoValor'])
            ])

        secao_documentos.append(self._criar_tabela_campos(documentos, col_w))
        story.append(KeepTogether(secao_documentos))
        story.append(Spacer(1, 3*mm))

        # =====================================================================
        # EXAME MÉDICO (KeepTogether para não dividir a seção)
        # =====================================================================
        secao_exame = []
        secao_exame.append(self._criar_secao("EXAME MÉDICO (ASO)"))
        
        exame = [
            [Paragraph("<b>Data Exame:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_exame_medico')), self.styles['CampoValor']),
             Paragraph("<b>Tipo Exames:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('tipo_exames', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Médico:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('nome_medico', '-'), self.styles['CampoValor']),
             Paragraph("<b>CRM:</b>", self.styles['CampoLabel']),
             Paragraph(f"{c.get('crm', '-')}/{c.get('uf_crm', '')}",
                      self.styles['CampoValor'])],
        ]

        secao_exame.append(self._criar_tabela_campos(exame, col_w))
        story.append(KeepTogether(secao_exame))
        story.append(Spacer(1, 3*mm))

        # =====================================================================
        # DADOS DO ÚLTIMO REGISTRO (KeepTogether para não dividir a seção)
        # =====================================================================
        secao_ultimo_reg = []
        secao_ultimo_reg.append(self._criar_secao("DADOS DO ÚLTIMO REGISTRO"))
        
        ultimo_reg = [
            [Paragraph("<b>Empresa:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('empresa_ultimo_emprego', '-'), self.styles['CampoValor']),
             Paragraph("<b>CNPJ:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_cnpj(c.get('cnpj_ultimo_emprego', '-')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Admissão:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_admissao_ultimo')), self.styles['CampoValor']),
             Paragraph("<b>Saída:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_saida_ultimo')), self.styles['CampoValor'])],

            [Paragraph("<b>Primeiro Reg.:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('primeiro_registro', '-'), self.styles['CampoValor']),
             Paragraph("<b>Últ. Contrib. Sindical:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_ultima_contribuicao_sindical')),
                      self.styles['CampoValor'])],
        ]

        secao_ultimo_reg.append(self._criar_tabela_campos(ultimo_reg, col_w))
        story.append(KeepTogether(secao_ultimo_reg))
        story.append(Spacer(1, 3*mm))

        # =====================================================================
        # DEPENDENTES (KeepTogether para não dividir a seção)
        # =====================================================================
        secao_dependentes = []
        secao_dependentes.append(self._criar_secao("RELAÇÃO DE DEPENDENTES (IR E SALÁRIO FAMÍLIA)"))

        if dependentes and len(dependentes) > 0:
            dep_data = [[
                Paragraph("<b>Nome</b>", self.styles['CampoLabel']),
                Paragraph("<b>Parentesco</b>", self.styles['CampoLabel']),
                Paragraph("<b>Data Nasc.</b>", self.styles['CampoLabel']),
                Paragraph("<b>CPF</b>", self.styles['CampoLabel']),
            ]]

            for dep in dependentes:
                dep_data.append([
                    Paragraph(dep.get('nome', '-'), self.styles['CampoValor']),
                    Paragraph(dep.get('parentesco', '-'), self.styles['CampoValor']),
                    Paragraph(self._formatar_data(dep.get('data_nascimento')), self.styles['CampoValor']),
                    Paragraph(self._formatar_cpf(dep.get('cpf', '-')), self.styles['CampoValor']),
                ])

            dep_table = Table(dep_data, colWidths=[60*mm, 35*mm, 30*mm, 35*mm])
            dep_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COR_CINZA_CLARO),
                ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            secao_dependentes.append(dep_table)
        else:
            secao_dependentes.append(Paragraph("Nenhum dependente cadastrado.", self.styles['CampoValor']))

        story.append(KeepTogether(secao_dependentes))
        story.append(Spacer(1, 3*mm))
        
        # =====================================================================
        # DADOS DA EMPRESA (CONTRATO) - KeepTogether para não dividir a seção
        # =====================================================================
        secao_contrato = []
        secao_contrato.append(self._criar_secao("PARA PREENCHIMENTO DA EMPRESA"))

        contrato = [
            [Paragraph("<b>Data Admissão:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_data(c.get('data_admissao')), self.styles['CampoValor']),
             Paragraph("<b>Função:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('funcao', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Departamento:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('departamento', '-'), self.styles['CampoValor']),
             Paragraph("<b>Salário:</b>", self.styles['CampoLabel']),
             Paragraph(self._formatar_moeda(c.get('salario')), self.styles['CampoValor'])],
            
            [Paragraph("<b>Forma Pagamento:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('forma_pagamento', '-'), self.styles['CampoValor']),
             Paragraph("<b>Tipo Contrato:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('tipo_contrato', '-'), self.styles['CampoValor'])],

            [Paragraph("<b>Dias Trabalho:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('dias_trabalho', '-'), self.styles['CampoValor']),
             Paragraph("<b>Horário:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('horario_trabalho', '-'), self.styles['CampoValor'])],
            
            [Paragraph("<b>Intervalo:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('intervalo', '-'), self.styles['CampoValor']),
             Paragraph("<b>Dias Folga:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('dias_folga', '-'), self.styles['CampoValor'])],
        ]

        # Adicionar linha de experiência/prorrogação apenas se for contrato de experiência
        if c.get('tipo_contrato') == 'Contrato de Experiência':
            contrato.insert(3, [
                Paragraph("<b>Experiência:</b>", self.styles['CampoLabel']),
                Paragraph(f"{c.get('prazo_experiencia', '-')} dias", self.styles['CampoValor']),
                Paragraph("<b>Prorrogação:</b>", self.styles['CampoLabel']),
                Paragraph(f"{c.get('prorrogacao', '-')} dias" if c.get('prorrogacao') else '-',
                         self.styles['CampoValor'])
            ])

        secao_contrato.append(self._criar_tabela_campos(contrato, col_w))

        if c.get('observacoes_contrato'):
            secao_contrato.append(Spacer(1, 2*mm))
            secao_contrato.append(Paragraph(f"<b>Observações:</b> {c.get('observacoes_contrato')}",
                                  self.styles['CampoValor']))

        story.append(KeepTogether(secao_contrato))
        story.append(Spacer(1, 3*mm))
        
        # =====================================================================
        # BENEFÍCIOS - KeepTogether para não dividir a seção
        # =====================================================================
        secao_beneficios = []
        secao_beneficios.append(self._criar_secao("BENEFÍCIOS"))
        
        beneficios = [
            [Paragraph("<b>Benefício</b>", self.styles['CampoLabel']),
             Paragraph("<b>Possui?</b>", self.styles['CampoLabel']),
             Paragraph("<b>Valor Diário/Mensal</b>", self.styles['CampoLabel']),
             Paragraph("<b>% Desconto</b>", self.styles['CampoLabel'])],
            
            [Paragraph("Vale Transporte", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('vale_transporte')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('vt_valor_diario')), self.styles['CampoValor']),
             Paragraph(f"{c.get('vt_percentual_desconto', '-')}%" if c.get('vt_percentual_desconto') else '-', 
                      self.styles['CampoValor'])],
            
            [Paragraph("Vale Refeição", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('vale_refeicao')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('vr_valor_diario')), self.styles['CampoValor']),
             Paragraph(f"{c.get('vr_percentual_desconto', '-')}%" if c.get('vr_percentual_desconto') else '-', 
                      self.styles['CampoValor'])],
            
            [Paragraph("Vale Alimentação", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('vale_alimentacao')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('va_valor_diario')), self.styles['CampoValor']),
             Paragraph(f"{c.get('va_percentual_desconto', '-')}%" if c.get('va_percentual_desconto') else '-', 
                      self.styles['CampoValor'])],
            
            [Paragraph("Assistência Médica", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('assistencia_medica')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('am_valor_desconto')), self.styles['CampoValor']),
             Paragraph("-", self.styles['CampoValor'])],
            
            [Paragraph("Assist. Odontológica", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('assistencia_odontologica')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('ao_valor_desconto')), self.styles['CampoValor']),
             Paragraph("-", self.styles['CampoValor'])],
            
            [Paragraph("Seguro de Vida", self.styles['CampoValor']),
             Paragraph(self._sim_nao(c.get('seguro_vida')), self.styles['CampoValor']),
             Paragraph(self._formatar_moeda(c.get('sv_valor_desconto')), self.styles['CampoValor']),
             Paragraph("-", self.styles['CampoValor'])],
        ]
        
        ben_table = Table(beneficios, colWidths=[50*mm, 25*mm, 45*mm, 40*mm])
        ben_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COR_CINZA_CLARO),
            ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        secao_beneficios.append(ben_table)

        # Adiantamento
        secao_beneficios.append(Spacer(1, 2*mm))
        adiant = [
            [Paragraph("<b>Adiantamento:</b>", self.styles['CampoLabel']),
             Paragraph(self._sim_nao(c.get('adiantamento')), self.styles['CampoValor']),
             Paragraph("<b>Percentual:</b>", self.styles['CampoLabel']),
             Paragraph(f"{c.get('percentual_adiantamento', '-')}%" if c.get('percentual_adiantamento') else '-',
                      self.styles['CampoValor'])],
            [Paragraph("<b>Dia Pagamento:</b>", self.styles['CampoLabel']),
             Paragraph(str(c.get('data_pagamento_adiantamento', '-')), self.styles['CampoValor']),
             Paragraph("", self.styles['CampoLabel']),
             Paragraph("", self.styles['CampoValor'])],
        ]
        secao_beneficios.append(self._criar_tabela_campos(adiant, col_w))
        story.append(KeepTogether(secao_beneficios))
        story.append(Spacer(1, 3*mm))
        
        # =====================================================================
        # DADOS BANCÁRIOS - KeepTogether para não dividir a seção
        # =====================================================================
        secao_banco = []
        secao_banco.append(self._criar_secao("PAGAMENTO DE SALÁRIO EM CONTA"))

        banco = [
            [Paragraph("<b>Tipo Conta:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('tipo_conta', '-'), self.styles['CampoValor']),
             Paragraph("<b>Banco:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('banco', '-'), self.styles['CampoValor'])],

            [Paragraph("<b>Agência:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('agencia', '-'), self.styles['CampoValor']),
             Paragraph("<b>Conta:</b>", self.styles['CampoLabel']),
             Paragraph(c.get('conta', '-'), self.styles['CampoValor'])],
        ]

        secao_banco.append(self._criar_tabela_campos(banco, col_w))

        if c.get('observacoes_banco'):
            secao_banco.append(Spacer(1, 2*mm))
            secao_banco.append(Paragraph(f"<b>Observações:</b> {c.get('observacoes_banco')}",
                                  self.styles['CampoValor']))

        story.append(KeepTogether(secao_banco))
        story.append(Spacer(1, 3*mm))
        
        # =====================================================================
        # OBSERVAÇÕES GERAIS - KeepTogether para não dividir a seção
        # =====================================================================
        secao_obs = []
        secao_obs.append(self._criar_secao("OBSERVAÇÕES GERAIS"))

        obs_text = c.get('observacoes_gerais', 'Nenhuma observação registrada.')
        secao_obs.append(Spacer(1, 2*mm))
        secao_obs.append(Paragraph(obs_text, self.styles['CampoValor']))
        story.append(KeepTogether(secao_obs))
        story.append(Spacer(1, 5*mm))

        # =====================================================================
        # ASSINATURAS - KeepTogether para NUNCA dividir esta seção
        # =====================================================================
        secao_assinaturas = []
        secao_assinaturas.append(self._criar_secao("DECLARAÇÃO E ASSINATURAS"))
        secao_assinaturas.append(Spacer(1, 3*mm))

        declaracao = """Declaro que as informações prestadas são verdadeiras e autorizo a empresa a
        realizar as verificações que julgar necessárias. Comprometo-me a comunicar qualquer
        alteração nos dados acima informados."""
        secao_assinaturas.append(Paragraph(declaracao, self.styles['CampoValor']))
        secao_assinaturas.append(Spacer(1, 12*mm))

        # Linhas de assinatura - underlines menores
        ass_data = [
            [Paragraph("_" * 35, self.styles['CampoValor']),
             Paragraph("_" * 35, self.styles['CampoValor'])],
            [Paragraph("<b>Assinatura do Empregado</b>",
                      ParagraphStyle(name='AssCentro', alignment=TA_CENTER, fontSize=8)),
             Paragraph("<b>Assinatura do Empregador</b>",
                      ParagraphStyle(name='AssCentro2', alignment=TA_CENTER, fontSize=8))],
            [Paragraph("Data: ____/____/______",
                      ParagraphStyle(name='AssData1', alignment=TA_CENTER, fontSize=8)),
             Paragraph("Data: ____/____/______",
                      ParagraphStyle(name='AssData2', alignment=TA_CENTER, fontSize=8))],
        ]

        ass_table = Table(ass_data, colWidths=[75*mm, 75*mm])
        ass_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        secao_assinaturas.append(ass_table)

        # Usar KeepTogether para garantir que assinaturas fiquem juntas
        story.append(KeepTogether(secao_assinaturas))

        # Preencher espaço restante para alinhar ao topo
        story.append(FrameFiller())

        # Construir PDF - primeiro contamos as páginas, depois geramos
        # Primeira passada para contar páginas
        from io import BytesIO
        import copy

        temp_buffer = BytesIO()

        # Frame temporário para contagem
        temp_frame = Frame(
            self.margin,
            32*mm,
            self.width - 2*self.margin,
            self.height - 35*mm - 32*mm,
            id='temp_normal',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0
        )

        temp_doc = BaseDocTemplate(
            temp_buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=35*mm,
            bottomMargin=32*mm
        )
        temp_template = PageTemplate(id='TempPage', frames=[temp_frame])
        temp_doc.addPageTemplates([temp_template])

        # Usar deepcopy para não consumir os elementos do story original
        story_copy = copy.deepcopy(story)
        temp_doc.build(story_copy)
        self.total_pages = temp_doc.page

        # Segunda passada para gerar o PDF final
        doc.build(story)

        return self.output_path


def gerar_ficha_registro_pdf(colaborador: dict, dependentes: list = None,
                              empresa: dict = None, output_dir: str = None) -> str:
    """Função helper para gerar PDF da ficha de registro."""
    import re

    # Usa pasta exports no mesmo diretório do executável/script
    if output_dir is None:
        output_dir = os.path.join(get_base_path(), "exports")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extrair primeiro nome e CPF
    nome_completo = colaborador.get('nome_completo', 'COLABORADOR') or 'COLABORADOR'
    primeiro_nome = nome_completo.split()[0].upper()
    # Remover caracteres especiais do nome
    primeiro_nome = "".join(char for char in primeiro_nome if char.isalnum())

    # Limpar CPF (remover pontos e traços)
    cpf = colaborador.get('cpf', '00000000000') or '00000000000'
    cpf_limpo = re.sub(r'\D', '', cpf)

    # Nome do arquivo: FREG-NOME-CPF.pdf
    filename = f"FREG-{primeiro_nome}-{cpf_limpo}.pdf"
    output_path = os.path.join(output_dir, filename)

    # Se já existir, será substituído automaticamente
    generator = PDFGenerator(output_path)
    return generator.gerar_ficha_registro(colaborador, dependentes, empresa)
