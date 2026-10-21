from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify


class Competencia(models.Model):
    """Habilidade ou área de conhecimento (ex.: Python, Redação, Design)."""

    nome = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "competência"
        verbose_name_plural = "competências"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Perfil(models.Model):
    """Informações acadêmicas e competências de um estudante."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    curso = models.CharField(max_length=100, blank=True)
    polo = models.CharField(max_length=100, blank=True)
    bio = models.TextField(
        "sobre mim", max_length=600, blank=True,
        help_text="Conte brevemente seus interesses e o que gostaria de desenvolver.",
    )
    interesses = models.CharField(
        max_length=200, blank=True,
        help_text="Temas que interessam a você, separados por vírgula.",
    )
    competencias = models.ManyToManyField(Competencia, blank=True, related_name="perfis")
    contato = models.CharField(
        "forma de contato", max_length=120, blank=True,
        help_text="E-mail, WhatsApp ou outro canal. Só é exibido para quem forma equipe com você.",
    )

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    @property
    def nome_exibicao(self):
        return self.usuario.get_full_name() or self.usuario.username

    def lista_interesses(self):
        return [i.strip() for i in self.interesses.split(",") if i.strip()]

    def get_absolute_url(self):
        return reverse("contas:perfil", args=[self.usuario.username])


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(usuario=instance)
