"""
Models Django - Modulo RH (Sistema de Gestao de Recursos Humanos)
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
        FERIAS = "FERIAS", "Ferias"
        AFASTADO = "AFASTADO", "Afastado"
        DESLIGADO = "DESLIGADO", "Desligado"

    class Sexo(models.TextChoices):
        MASCULINO = "MASCULINO", "Masculino"
        FEMININO = "FEMININO", "Feminino"

    class EstadoCivil(models.TextChoices):
        SOLTEIRO = "SOLTEIRO", "Solteiro"
        CASADO = "CASADO", "Casado"
        DIVORCIADO = "DIVORCIADO", "Divorciado"
        VIUVO = "VIUVO", "Viuvo"
        UNIAO_ESTAVEL = "UNIAO_ESTAVEL", "Uniao Estavel"

    foto = models.ImageField(upload_to="colaboradores/fotos/", blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="colaboradores")
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "colaboradores"
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


class Ferias(models.Model):
    class StatusFerias(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PROGRAMADA = "PROGRAMADA", "Programada"
        EM_GOZO = "EM_GOZO", "Em Gozo"
        CONCLUIDA = "CONCLUIDA", "Concluida"
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


class Configuracao(models.Model):
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configuracoes"


class HistoricoAlteracao(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name="historico_alteracoes")
    campo = models.CharField(max_length=100)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_novo = models.TextField(blank=True, null=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "historico_alteracoes"
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
