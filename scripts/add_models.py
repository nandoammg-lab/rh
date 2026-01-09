additional = """

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
"""

with open("colaboradores/models.py", "a", encoding="utf-8") as f:
    f.write(additional)
print("Done")
