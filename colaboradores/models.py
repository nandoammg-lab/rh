"""
Models Django - Módulo RH (Sistema de Gestão de Recursos Humanos)
Migrado de SQLAlchemy para Django ORM
"""

from django.db import models
from django.contrib.auth.models import User


class Empresa(models.Model):
    razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=20, unique=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to="empresas/logos/", blank=True, null=True)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empresas"
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["razao_social"]

    def __str__(self):
        return self.razao_social


class Colaborador(models.Model):
    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        INATIVO = "INATIVO", "Inativo"
        FERIAS = "FERIAS", "Férias"
        AFASTADO = "AFASTADO", "Afastado"
        DESLIGADO = "DESLIGADO", "Desligado"

    class Sexo(models.TextChoices):
        MASCULINO = "MASCULINO", "Masculino"
        FEMININO = "FEMININO", "Feminino"

    class EstadoCivil(models.TextChoices):
        SOLTEIRO = "SOLTEIRO", "Solteiro(a)"
        CASADO = "CASADO", "Casado(a)"
        DIVORCIADO = "DIVORCIADO", "Divorciado(a)"
        VIUVO = "VIUVO", "Viúvo(a)"
        UNIAO_ESTAVEL = "UNIAO_ESTAVEL", "União Estável"

    # Foto
    foto = models.ImageField(upload_to="colaboradores/fotos/", blank=True, null=True)

    # Empresa Contratante
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="colaboradores")

    # Dados Pessoais
    nome_completo = models.CharField(max_length=255)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf_endereco = models.CharField(max_length=2, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    naturalidade = models.CharField(max_length=100, blank=True, null=True)
    uf_naturalidade = models.CharField(max_length=2, blank=True, null=True)
    sexo = models.CharField(max_length=20, choices=Sexo.choices, blank=True, null=True)
    grau_instrucao = models.CharField(max_length=100, blank=True, null=True)
    curso_formacao = models.CharField(max_length=255, blank=True, null=True)
    estado_civil = models.CharField(max_length=50, choices=EstadoCivil.choices, blank=True, null=True)
    data_casamento = models.DateField(blank=True, null=True)
    nome_conjuge = models.CharField(max_length=255, blank=True, null=True)
    deficiencia = models.CharField(max_length=255, blank=True, null=True)
    nome_mae = models.CharField(max_length=255, blank=True, null=True)
    cpf_mae = models.CharField(max_length=14, blank=True, null=True)
    nome_pai = models.CharField(max_length=255, blank=True, null=True)
    cpf_pai = models.CharField(max_length=14, blank=True, null=True)
    data_conclusao = models.DateField(blank=True, null=True)

    # Documentos
    carteira_profissional = models.CharField(max_length=50, blank=True, null=True)
    serie_carteira = models.CharField(max_length=20, blank=True, null=True)
    uf_carteira = models.CharField(max_length=2, blank=True, null=True)
    data_emissao_carteira = models.DateField(blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    data_emissao_rg = models.DateField(blank=True, null=True)
    orgao_emissor_rg = models.CharField(max_length=50, blank=True, null=True)
    uf_rg = models.CharField(max_length=2, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True)
    titulo_eleitor = models.CharField(max_length=20, blank=True, null=True)
    zona_eleitor = models.CharField(max_length=10, blank=True, null=True)
    secao_eleitor = models.CharField(max_length=10, blank=True, null=True)
    habilitacao = models.CharField(max_length=20, blank=True, null=True)
    data_expedicao_cnh = models.DateField(blank=True, null=True)
    tipo_cnh = models.CharField(max_length=10, blank=True, null=True)
    validade_cnh = models.DateField(blank=True, null=True)
    pis = models.CharField(max_length=20, blank=True, null=True)
    data_cadastramento_pis = models.DateField(blank=True, null=True)
    reservista = models.CharField(max_length=50, blank=True, null=True)

    # Conselho Regional
    conselho_regional = models.CharField(max_length=100, blank=True, null=True)
    sigla_conselho = models.CharField(max_length=20, blank=True, null=True)
    numero_conselho = models.CharField(max_length=50, blank=True, null=True)
    regiao_conselho = models.CharField(max_length=50, blank=True, null=True)

    # Exame Médico
    data_exame_medico = models.DateField(blank=True, null=True)
    tipo_exames = models.CharField(max_length=255, blank=True, null=True)
    nome_medico = models.CharField(max_length=255, blank=True, null=True)
    crm = models.CharField(max_length=20, blank=True, null=True)
    uf_crm = models.CharField(max_length=2, blank=True, null=True)

    # Último Emprego
    cnpj_ultimo_emprego = models.CharField(max_length=20, blank=True, null=True)
    empresa_ultimo_emprego = models.CharField(max_length=255, blank=True, null=True)
    data_admissao_ultimo = models.DateField(blank=True, null=True)
    data_saida_ultimo = models.DateField(blank=True, null=True)
    matricula_ultimo = models.CharField(max_length=50, blank=True, null=True)
    primeiro_registro = models.CharField(max_length=50, blank=True, null=True)
    data_ultima_contribuicao_sindical = models.DateField(blank=True, null=True)

    # Dados da Empresa Atual
    data_admissao = models.DateField(blank=True, null=True)
    funcao = models.CharField(max_length=100, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    forma_pagamento = models.CharField(max_length=50, blank=True, null=True)
    prazo_experiencia = models.IntegerField(blank=True, null=True)
    prorrogacao = models.IntegerField(blank=True, null=True)
    dias_trabalho = models.CharField(max_length=100, blank=True, null=True)
    horario_trabalho = models.CharField(max_length=50, blank=True, null=True)
    intervalo = models.CharField(max_length=50, blank=True, null=True)
    dias_folga = models.CharField(max_length=100, blank=True, null=True)
    observacoes_contrato = models.TextField(blank=True, null=True)
    tipo_contrato = models.CharField(max_length=50, blank=True, null=True)

    # Beneficios
    vale_transporte = models.BooleanField(default=False)
    vt_valor_diario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vt_percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    vale_refeicao = models.BooleanField(default=False)
    vr_valor_diario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vr_percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    vale_alimentacao = models.BooleanField(default=False)
    va_valor_diario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    va_percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    assistencia_medica = models.BooleanField(default=False)
    am_valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    assistencia_odontologica = models.BooleanField(default=False)
    ao_valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    seguro_vida = models.BooleanField(default=False)
    sv_valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    adiantamento = models.BooleanField(default=False)
    percentual_adiantamento = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    data_pagamento_adiantamento = models.IntegerField(blank=True, null=True)

    # Dados Bancarios
    tipo_conta = models.CharField(max_length=50, blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    observacoes_banco = models.TextField(blank=True, null=True)

    # Observacoes
    observacoes_gerais = models.TextField(blank=True, null=True)

    # Status e Controle
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)
    data_desligamento = models.DateField(blank=True, null=True)
    motivo_desligamento = models.TextField(blank=True, null=True)
    observacoes_desligamento = models.TextField(blank=True, null=True)
    motivo_inativacao = models.CharField(max_length=255, blank=True, null=True)
    submotivo_inativacao = models.CharField(max_length=255, blank=True, null=True)
    data_inativacao = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "colaboradores"
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo


class Dependente(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="dependentes")
    nome = models.CharField(max_length=255)
    parentesco = models.CharField(max_length=50, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dependentes"
        verbose_name = "Dependente"
        verbose_name_plural = "Dependentes"


class Localizacao(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="localizacoes")
    local_nome = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "localizacoes"
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"


class Ferias(models.Model):
    class StatusFerias(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PROGRAMADA = "PROGRAMADA", "Programada"
        EM_GOZO = "EM_GOZO", "Em Gozo"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        VENCIDA = "VENCIDA", "Vencida"

    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="ferias")
    periodo_aquisitivo_inicio = models.DateField()
    periodo_aquisitivo_fim = models.DateField()
    periodo_concessivo_limite = models.DateField()
    dias_direito = models.IntegerField(default=30)
    dias_gozados = models.IntegerField(default=0)
    dias_vendidos = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=StatusFerias.choices, default=StatusFerias.PENDENTE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ferias"
        verbose_name = "Férias"
        verbose_name_plural = "Férias"


class PeriodoFerias(models.Model):
    ferias = models.ForeignKey(Ferias, on_delete=models.CASCADE, related_name="periodos")
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias = models.IntegerField()
    abono_pecuniario = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "periodos_ferias"
        verbose_name = "Período de Férias"
        verbose_name_plural = "Períodos de Férias"


class ContratoExperiencia(models.Model):
    class StatusContrato(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        PRORROGADO = "PRORROGADO", "Prorrogado"
        EFETIVADO = "EFETIVADO", "Efetivado"
        ENCERRADO = "ENCERRADO", "Encerrado"

    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="contratos_experiencia")
    data_inicio = models.DateField()
    prazo_inicial = models.IntegerField()
    data_fim_inicial = models.DateField()
    prorrogacao = models.IntegerField(blank=True, null=True)
    data_fim_prorrogacao = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=StatusContrato.choices, default=StatusContrato.VIGENTE)
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contratos_experiencia"
        verbose_name = "Contrato de Experiência"
        verbose_name_plural = "Contratos de Experiência"


class Blocklist(models.Model):
    cpf = models.CharField(max_length=14)
    nome = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="blocklist")
    data_admissao = models.DateField(blank=True, null=True)
    data_desligamento = models.DateField(blank=True, null=True)
    motivo_desligamento = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    pode_recontratar = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blocklist"
        verbose_name = "Block-List"
        verbose_name_plural = "Block-List"


class Configuracao(models.Model):
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configuracoes"
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"


class HistoricoAlteracao(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="historico_alteracoes")
    campo = models.CharField(max_length=100)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_novo = models.TextField(blank=True, null=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "historico_alteracoes"
        verbose_name = "Histórico de Alteração"
        verbose_name_plural = "Histórico de Alterações"
        ordering = ["-data_alteracao"]


class DocumentoColaborador(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.CharField(max_length=100)
    nome_arquivo_original = models.CharField(max_length=255, blank=True, null=True)
    arquivo = models.FileField(upload_to="colaboradores/documentos/")
    obrigatorio = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documentos_colaborador"
        verbose_name = "Documento do Colaborador"
        verbose_name_plural = "Documentos do Colaborador"


class LogSistema(models.Model):
    tipo_acao = models.CharField(max_length=50)
    categoria = models.CharField(max_length=50)
    descricao = models.TextField()
    entidade_tipo = models.CharField(max_length=50, blank=True, null=True)
    entidade_id = models.IntegerField(blank=True, null=True)
    entidade_nome = models.CharField(max_length=255, blank=True, null=True)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_novo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "logs_sistema"
        verbose_name = "Log do Sistema"
        verbose_name_plural = "Logs do Sistema"
        ordering = ["-data_hora"]


class PerfilUsuario(models.Model):
    class NivelAcesso(models.TextChoices):
        ADMIN = "admin", "Administrador"
        GERENTE = "gerente", "Gerente"
        OPERADOR = "operador", "Operador"
        VISUALIZADOR = "visualizador", "Visualizador"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    cargo = models.CharField(max_length=100, blank=True, null=True)
    nivel_acesso = models.CharField(max_length=20, choices=NivelAcesso.choices, default=NivelAcesso.OPERADOR)
    pergunta_seguranca = models.CharField(max_length=255, blank=True, null=True)
    resposta_seguranca = models.CharField(max_length=255, blank=True, null=True)
    ultimo_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "perfis_usuario"
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuário"
