from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from contas.models import Competencia, Perfil


class PerfilTests(TestCase):
    def test_perfil_criado_automaticamente_com_usuario(self):
        user = User.objects.create_user("maria", password="SenhaForte123")
        self.assertTrue(Perfil.objects.filter(usuario=user).exists())

    def test_slug_da_competencia_gerado_automaticamente(self):
        c = Competencia.objects.create(nome="Análise de dados")
        self.assertEqual(c.slug, "analise-de-dados")

    def test_lista_interesses_separa_por_virgula(self):
        user = User.objects.create_user("joao", password="SenhaForte123")
        user.perfil.interesses = "robótica, educação ,  , IA"
        self.assertEqual(user.perfil.lista_interesses(), ["robótica", "educação", "IA"])


class CadastroTests(TestCase):
    def test_cadastro_cria_usuario_e_faz_login(self):
        resp = self.client.post(reverse("contas:cadastro"), {
            "first_name": "Maria", "last_name": "Souza", "email": "maria@aluno.univesp.br",
            "username": "maria", "password1": "SenhaForte123!", "password2": "SenhaForte123!",
        })
        self.assertRedirects(resp, reverse("contas:editar_perfil"))
        self.assertTrue(User.objects.filter(username="maria", email="maria@aluno.univesp.br").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="maria").pk)

    def test_cadastro_rejeita_email_duplicado(self):
        User.objects.create_user("outra", email="maria@aluno.univesp.br", password="x")
        resp = self.client.post(reverse("contas:cadastro"), {
            "first_name": "Maria", "email": "MARIA@aluno.univesp.br",
            "username": "maria", "password1": "SenhaForte123!", "password2": "SenhaForte123!",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Já existe uma conta com este e-mail.")


class EditarPerfilTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", password="SenhaForte123")
        self.python = Competencia.objects.create(nome="Python")

    def test_exige_login(self):
        resp = self.client.get(reverse("contas:editar_perfil"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)

    def test_atualiza_perfil_e_cria_novas_competencias(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("contas:editar_perfil"), {
            "u-first_name": "Ana", "u-last_name": "Silva", "u-email": "ana@exemplo.com",
            "p-curso": "Engenharia de Computação", "p-polo": "Itapevi",
            "p-competencias": [self.python.pk], "p-novas_competencias": "Docker, python",
        })
        self.assertEqual(resp.status_code, 302)
        perfil = Perfil.objects.get(usuario=self.user)
        self.assertEqual(perfil.polo, "Itapevi")
        nomes = set(perfil.competencias.values_list("nome", flat=True))
        self.assertEqual(nomes, {"Python", "Docker"})  # "python" reaproveita a existente
        self.assertEqual(Competencia.objects.filter(nome__iexact="python").count(), 1)
