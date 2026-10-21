from django.urls import reverse

from projetos.models import Interesse, Projeto

from .base import DadosBase


class ListagemTests(DadosBase):
    def test_lista_publica(self):
        resp = self.client.get(reverse("projetos:lista"))
        self.assertContains(resp, "Painel de dados")

    def test_busca_por_texto_e_competencia(self):
        Projeto.objects.create(autor=self.outro, titulo="Revista literária", resumo="Contos",
                               descricao="d", objetivo="o")
        resp = self.client.get(reverse("projetos:lista"), {"q": "literária"})
        self.assertContains(resp, "Revista literária")
        self.assertNotContains(resp, "Painel de dados")

        resp = self.client.get(reverse("projetos:lista"), {"competencia": "python"})
        self.assertContains(resp, "Painel de dados")
        self.assertNotContains(resp, "Revista literária")

    def test_filtro_somente_abertos(self):
        Projeto.objects.create(autor=self.outro, titulo="Projeto antigo", resumo="r", descricao="d",
                               objetivo="o", status=Projeto.Status.ENCERRADO)
        resp = self.client.get(reverse("projetos:lista"), {"abertos": "on"})
        self.assertNotContains(resp, "Projeto antigo")


class CrudProjetoTests(DadosBase):
    def test_criar_exige_login(self):
        resp = self.client.get(reverse("projetos:criar"))
        self.assertEqual(resp.status_code, 302)

    def test_criar_projeto_define_autor(self):
        self.client.force_login(self.aluno)
        resp = self.client.post(reverse("projetos:criar"), {
            "titulo": "Grupo de estudos", "resumo": "Estudar Cálculo", "descricao": "d", "objetivo": "o",
            "tipo": "academico", "vagas": 4, "status": "aberto",
            "competencias_desejadas": [self.python.pk], "novas_competencias": "Matemática",
        })
        projeto = Projeto.objects.get(titulo="Grupo de estudos")
        self.assertRedirects(resp, projeto.get_absolute_url())
        self.assertEqual(projeto.autor, self.aluno)
        self.assertEqual(projeto.competencias_desejadas.count(), 2)

    def test_somente_autor_edita_e_exclui(self):
        self.client.force_login(self.aluno)
        self.assertEqual(self.client.get(reverse("projetos:editar", args=[self.projeto.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("projetos:excluir", args=[self.projeto.pk])).status_code, 403)
        self.client.force_login(self.autor)
        self.assertEqual(self.client.get(reverse("projetos:editar", args=[self.projeto.pk])).status_code, 200)


class FluxoInteresseTests(DadosBase):
    def test_fluxo_completo_pelas_telas(self):
        # Aluno manifesta interesse
        self.client.force_login(self.aluno)
        self.client.post(reverse("projetos:manifestar_interesse", args=[self.projeto.pk]), {"mensagem": "Sei Python"})
        interesse = Interesse.objects.get(projeto=self.projeto, estudante=self.aluno)

        # Autor vê o pedido e aceita
        self.client.force_login(self.autor)
        resp = self.client.get(self.projeto.get_absolute_url())
        self.assertContains(resp, "Sei Python")
        self.client.post(reverse("projetos:responder_interesse", args=[interesse.pk]), {"acao": "aceitar"})
        interesse.refresh_from_db()
        self.assertEqual(interesse.status, Interesse.Status.ACEITO)

        # Aluno aparece na equipe; painel mostra o status
        self.client.force_login(self.aluno)
        resp = self.client.get(reverse("projetos:painel"))
        self.assertContains(resp, "Aceito na equipe")

    def test_outro_usuario_nao_responde_interesse(self):
        interesse = Interesse.objects.create(projeto=self.projeto, estudante=self.aluno)
        self.client.force_login(self.outro)
        resp = self.client.post(reverse("projetos:responder_interesse", args=[interesse.pk]), {"acao": "aceitar"})
        self.assertEqual(resp.status_code, 404)
        interesse.refresh_from_db()
        self.assertEqual(interesse.status, Interesse.Status.PENDENTE)

    def test_indicadores_publicos(self):
        resp = self.client.get(reverse("projetos:indicadores"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python")


class AcessibilidadeTests(DadosBase):
    """Verificações automáticas básicas de acessibilidade nas páginas principais."""

    paginas = ["projetos:lista", "projetos:indicadores", "login", "contas:cadastro"]

    def test_estrutura_basica_acessivel(self):
        for nome in self.paginas:
            with self.subTest(pagina=nome):
                html = self.client.get(reverse(nome)).content.decode()
                self.assertIn('<html lang="pt-BR">', html)
                self.assertIn('href="#conteudo"', html)          # link para pular ao conteúdo
                self.assertIn('<main id="conteudo"', html)       # região principal
                self.assertEqual(html.count("<h1"), 1)           # um único título principal

    def test_campos_de_formulario_tem_rotulo(self):
        html = self.client.get(reverse("contas:cadastro")).content.decode()
        for campo in ["id_first_name", "id_email", "id_username", "id_password1", "id_password2"]:
            self.assertIn(f'for="{campo}"', html)
