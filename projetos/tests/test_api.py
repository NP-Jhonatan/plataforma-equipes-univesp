from rest_framework.test import APITestCase

from projetos.models import Interesse, Projeto

from .base import DadosBase


class ApiProjetosTests(DadosBase, APITestCase):
    def test_listar_projetos_sem_login(self):
        resp = self.client.get("/api/projetos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["titulo"], "Painel de dados")
        self.assertEqual(resp.data["results"][0]["competencias_desejadas"][0]["nome"], "Python")

    def test_filtro_por_competencia(self):
        self.assertEqual(self.client.get("/api/projetos/?competencia=redacao").data["count"], 0)
        self.assertEqual(self.client.get("/api/projetos/?competencia=python").data["count"], 1)

    def test_criar_exige_autenticacao(self):
        resp = self.client.post("/api/projetos/", {"titulo": "x"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_criar_projeto(self):
        self.client.force_authenticate(self.aluno)
        resp = self.client.post("/api/projetos/", {
            "titulo": "Novo", "resumo": "r", "descricao": "d", "objetivo": "o",
            "tipo": "extracurricular", "vagas": 2, "competencias_ids": [self.redacao.pk],
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["autor"]["username"], "aluno")
        self.assertEqual(Projeto.objects.get(titulo="Novo").competencias_desejadas.get(), self.redacao)

    def test_nao_autor_nao_altera(self):
        self.client.force_authenticate(self.aluno)
        resp = self.client.patch(f"/api/projetos/{self.projeto.pk}/", {"titulo": "Hack"}, format="json")
        self.assertEqual(resp.status_code, 403)


class ApiInteresseTests(DadosBase, APITestCase):
    def test_manifestar_e_responder_interesse(self):
        self.client.force_authenticate(self.aluno)
        resp = self.client.post(f"/api/projetos/{self.projeto.pk}/interesse/", {"mensagem": "Oi"}, format="json")
        self.assertEqual(resp.status_code, 201)
        interesse_id = resp.data["id"]

        # duplicado retorna 400 com mensagem
        resp = self.client.post(f"/api/projetos/{self.projeto.pk}/interesse/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("já manifestou", resp.data["detail"])

        # aluno não pode responder o próprio pedido
        resp = self.client.post(f"/api/interesses/{interesse_id}/responder/", {"acao": "aceitar"}, format="json")
        self.assertEqual(resp.status_code, 403)

        self.client.force_authenticate(self.autor)
        resp = self.client.post(f"/api/interesses/{interesse_id}/responder/", {"acao": "aceitar"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "aceito")

    def test_lista_interesses_mostra_apenas_os_relacionados(self):
        Interesse.objects.create(projeto=self.projeto, estudante=self.aluno)
        self.client.force_authenticate(self.outro)
        self.assertEqual(self.client.get("/api/interesses/").data["count"], 0)
        self.client.force_authenticate(self.autor)
        self.assertEqual(self.client.get("/api/interesses/").data["count"], 1)

    def test_perfil_oculta_contato_de_quem_nao_e_da_equipe(self):
        self.autor.perfil.contato = "ana@exemplo.com"
        self.autor.perfil.save()
        self.client.force_authenticate(self.outro)
        self.assertIsNone(self.client.get("/api/perfis/autor/").data["contato"])
        self.client.force_authenticate(self.autor)
        self.assertEqual(self.client.get("/api/perfis/autor/").data["contato"], "ana@exemplo.com")
