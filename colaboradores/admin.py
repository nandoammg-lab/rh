from django.contrib import admin
from .models import (
    Empresa, Colaborador, Dependente, Localizacao, Ferias,
    PeriodoFerias, ContratoExperiencia, Blocklist, Configuracao,
    HistoricoAlteracao, DocumentoColaborador, LogSistema, PerfilUsuario
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ["razao_social", "cnpj", "cidade", "uf", "ativa"]
    list_filter = ["ativa", "uf"]
    search_fields = ["razao_social", "cnpj"]


class DependenteInline(admin.TabularInline):
    model = Dependente
    extra = 0


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "cpf", "empresa", "status", "created_at"]
    list_filter = ["status", "empresa"]
    search_fields = ["nome_completo", "cpf"]
    inlines = [DependenteInline]


@admin.register(Dependente)
class DependenteAdmin(admin.ModelAdmin):
    list_display = ["nome", "colaborador", "parentesco", "data_nascimento"]
    search_fields = ["nome", "colaborador__nome_completo"]


@admin.register(Localizacao)
class LocalizacaoAdmin(admin.ModelAdmin):
    list_display = ["colaborador", "local_nome", "cidade", "uf", "data_inicio"]
    list_filter = ["uf"]
    search_fields = ["local_nome", "colaborador__nome_completo"]


@admin.register(Ferias)
class FeriasAdmin(admin.ModelAdmin):
    list_display = ["colaborador", "periodo_aquisitivo_inicio", "status"]
    list_filter = ["status"]
    search_fields = ["colaborador__nome_completo"]


@admin.register(PeriodoFerias)
class PeriodoFeriasAdmin(admin.ModelAdmin):
    list_display = ["ferias", "data_inicio", "data_fim", "dias"]


@admin.register(ContratoExperiencia)
class ContratoExperienciaAdmin(admin.ModelAdmin):
    list_display = ["colaborador", "data_inicio", "data_fim_inicial", "status"]
    list_filter = ["status"]
    search_fields = ["colaborador__nome_completo"]


@admin.register(Blocklist)
class BlocklistAdmin(admin.ModelAdmin):
    list_display = ["nome", "cpf", "empresa", "pode_recontratar"]
    list_filter = ["pode_recontratar"]
    search_fields = ["nome", "cpf"]


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ["chave", "valor", "updated_at"]
    search_fields = ["chave"]


@admin.register(HistoricoAlteracao)
class HistoricoAlteracaoAdmin(admin.ModelAdmin):
    list_display = ["colaborador", "campo", "data_alteracao", "usuario"]
    list_filter = ["campo"]


@admin.register(DocumentoColaborador)
class DocumentoColaboradorAdmin(admin.ModelAdmin):
    list_display = ["colaborador", "tipo_documento", "obrigatorio"]
    list_filter = ["tipo_documento", "obrigatorio"]


@admin.register(LogSistema)
class LogSistemaAdmin(admin.ModelAdmin):
    list_display = ["tipo_acao", "categoria", "entidade_nome", "data_hora"]
    list_filter = ["tipo_acao", "categoria"]


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ["user", "cargo", "nivel_acesso"]
    list_filter = ["nivel_acesso"]
