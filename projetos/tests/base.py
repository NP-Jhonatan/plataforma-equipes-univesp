from django.contrib.auth.models import User
from django.test import TestCase

from contas.models import Competencia
from projetos.models import Projeto


class DadosBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = User.objects.create_user("autor", password="SenhaForte123", first_name="Ana")
        cls.aluno = User.objects.create_user("aluno", password="SenhaForte123", first_name="Bruno")
        cls.outro = User.objects.create_user("outro", password="SenhaForte123", first_name="Carla")
        cls.python = Competencia.objects.create(nome="Python")
        cls.redacao = Competencia.objects.create(nome="Redação")
        cls.projeto = Projeto.objects.create(
            autor=cls.autor, titulo="Painel de dados", resumo="Analisar dados abertos",
            descricao="Descrição", objetivo="Objetivo", vagas=2,
        )
        cls.projeto.competencias_desejadas.add(cls.python)
