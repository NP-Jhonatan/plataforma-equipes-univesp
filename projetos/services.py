"""Regras de negócio compartilhadas pelas telas e pela API."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Interesse, Projeto


def manifestar_interesse(projeto, estudante, mensagem=""):
    if projeto.autor_id == estudante.pk:
        raise ValidationError("Você é o autor deste projeto.")
    if not projeto.aceita_interesse:
        raise ValidationError("Este projeto não está recebendo novos interessados.")
    if Interesse.objects.filter(projeto=projeto, estudante=estudante).exists():
        raise ValidationError("Você já manifestou interesse neste projeto.")
    return Interesse.objects.create(projeto=projeto, estudante=estudante, mensagem=mensagem.strip())


def cancelar_interesse(interesse, estudante):
    if interesse.estudante_id != estudante.pk:
        raise PermissionDenied
    if interesse.status == Interesse.Status.ACEITO:
        raise ValidationError("Você já faz parte da equipe. Fale com o autor para sair.")
    interesse.delete()


@transaction.atomic
def responder_interesse(interesse, autor, aceitar):
    projeto = Projeto.objects.select_for_update().get(pk=interesse.projeto_id)
    if projeto.autor_id != autor.pk:
        raise PermissionDenied
    if interesse.status != Interesse.Status.PENDENTE:
        raise ValidationError("Este interesse já foi respondido.")
    if aceitar and projeto.vagas_restantes == 0:
        raise ValidationError("Não há vagas restantes neste projeto.")

    interesse.status = Interesse.Status.ACEITO if aceitar else Interesse.Status.RECUSADO
    interesse.respondido_em = timezone.now()
    interesse.save(update_fields=["status", "respondido_em"])

    # Quando todas as vagas são preenchidas, o projeto passa a "Equipe formada".
    if aceitar and projeto.vagas_restantes == 0 and projeto.status == Projeto.Status.ABERTO:
        projeto.status = Projeto.Status.EM_ANDAMENTO
        projeto.save(update_fields=["status", "atualizado_em"])
    return interesse


def pode_ver_contato(visitante, dono):
    """Contato só aparece entre autor e membros aceitos de um mesmo projeto."""
    if not visitante.is_authenticated:
        return False
    if visitante.pk == dono.pk:
        return True
    aceito = Interesse.Status.ACEITO
    return (
        Interesse.objects.filter(projeto__autor=visitante, estudante=dono, status=aceito).exists()
        or Interesse.objects.filter(projeto__autor=dono, estudante=visitante, status=aceito).exists()
        or Interesse.objects.filter(
            estudante=visitante, status=aceito,
            projeto__interesses__estudante=dono, projeto__interesses__status=aceito,
        ).exists()
    )
