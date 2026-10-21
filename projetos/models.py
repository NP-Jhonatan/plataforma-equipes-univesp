from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from contas.models import Competencia


class Projeto(models.Model):
    """Ideia de projeto divulgada por um estudante em busca de equipe."""

    class Tipo(models.TextChoices):
        ACADEMICO = "academico", "Acadêmico"
        EXTRACURRICULAR = "extracurricular", "Extracurricular"

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto a participantes"
        EM_ANDAMENTO = "andamento", "Equipe formada"
        ENCERRADO = "encerrado", "Encerrado"

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projetos"
    )
    titulo = models.CharField("título", max_length=120)
    resumo = models.CharField(
        max_length=200, help_text="Uma frase que explique a ideia (até 200 caracteres)."
    )
    descricao = models.TextField("descrição", help_text="Detalhe a proposta, o contexto e o que já existe.")
    objetivo = models.TextField(help_text="O que o projeto pretende alcançar.")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ACADEMICO)
    competencias_desejadas = models.ManyToManyField(
        Competencia, blank=True, related_name="projetos",
        verbose_name="competências desejadas",
    )
    vagas = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Quantas pessoas você procura, além de você.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("projetos:detalhe", args=[self.pk])

    @property
    def membros(self):
        """Estudantes com interesse aceito."""
        return [i.estudante for i in self.interesses.filter(status=Interesse.Status.ACEITO).select_related("estudante")]

    @property
    def vagas_restantes(self):
        aceitos = self.interesses.filter(status=Interesse.Status.ACEITO).count()
        return max(self.vagas - aceitos, 0)

    @property
    def aceita_interesse(self):
        return self.status == self.Status.ABERTO and self.vagas_restantes > 0


class Interesse(models.Model):
    """Manifestação de interesse de um estudante em participar de um projeto."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Aguardando resposta"
        ACEITO = "aceito", "Aceito na equipe"
        RECUSADO = "recusado", "Não selecionado"

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name="interesses")
    estudante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interesses"
    )
    mensagem = models.TextField(
        max_length=500, blank=True,
        help_text="Conte por que quer participar e como pode contribuir.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    respondido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(fields=["projeto", "estudante"], name="interesse_unico_por_projeto"),
        ]

    def __str__(self):
        return f"{self.estudante} → {self.projeto}"
