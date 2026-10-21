from django.core.exceptions import PermissionDenied, ValidationError

from projetos import services
from projetos.models import Interesse, Projeto

from .base import DadosBase


class ManifestarInteresseTests(DadosBase):
    def test_cria_interesse_pendente(self):
        i = services.manifestar_interesse(self.projeto, self.aluno, "  Quero ajudar  ")
        self.assertEqual(i.status, Interesse.Status.PENDENTE)
        self.assertEqual(i.mensagem, "Quero ajudar")

    def test_autor_nao_pode_se_candidatar(self):
        with self.assertRaises(ValidationError):
            services.manifestar_interesse(self.projeto, self.autor)

    def test_nao_permite_interesse_duplicado(self):
        services.manifestar_interesse(self.projeto, self.aluno)
        with self.assertRaises(ValidationError):
            services.manifestar_interesse(self.projeto, self.aluno)

    def test_projeto_encerrado_nao_aceita_interesse(self):
        self.projeto.status = Projeto.Status.ENCERRADO
        self.projeto.save()
        with self.assertRaises(ValidationError):
            services.manifestar_interesse(self.projeto, self.aluno)


class ResponderInteresseTests(DadosBase):
    def test_aceitar_adiciona_membro_e_reduz_vagas(self):
        i = services.manifestar_interesse(self.projeto, self.aluno)
        services.responder_interesse(i, self.autor, aceitar=True)
        self.assertEqual(self.projeto.membros, [self.aluno])
        self.assertEqual(self.projeto.vagas_restantes, 1)
        self.assertIsNotNone(Interesse.objects.get(pk=i.pk).respondido_em)

    def test_somente_autor_responde(self):
        i = services.manifestar_interesse(self.projeto, self.aluno)
        with self.assertRaises(PermissionDenied):
            services.responder_interesse(i, self.outro, aceitar=True)

    def test_nao_responde_duas_vezes(self):
        i = services.manifestar_interesse(self.projeto, self.aluno)
        services.responder_interesse(i, self.autor, aceitar=False)
        with self.assertRaises(ValidationError):
            services.responder_interesse(i, self.autor, aceitar=True)

    def test_preencher_vagas_muda_status_para_equipe_formada(self):
        for estudante in (self.aluno, self.outro):
            i = services.manifestar_interesse(self.projeto, estudante)
            services.responder_interesse(i, self.autor, aceitar=True)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.status, Projeto.Status.EM_ANDAMENTO)
        self.assertFalse(self.projeto.aceita_interesse)


class ContatoTests(DadosBase):
    def test_contato_visivel_apenas_entre_membros(self):
        self.assertFalse(services.pode_ver_contato(self.aluno, self.autor))
        i = services.manifestar_interesse(self.projeto, self.aluno)
        self.assertFalse(services.pode_ver_contato(self.aluno, self.autor))  # pendente ainda não vê
        services.responder_interesse(i, self.autor, aceitar=True)
        self.assertTrue(services.pode_ver_contato(self.aluno, self.autor))
        self.assertTrue(services.pode_ver_contato(self.autor, self.aluno))
        self.assertFalse(services.pode_ver_contato(self.outro, self.aluno))

    def test_membros_da_mesma_equipe_se_veem(self):
        for estudante in (self.aluno, self.outro):
            i = services.manifestar_interesse(self.projeto, estudante)
            services.responder_interesse(i, self.autor, aceitar=True)
        self.assertTrue(services.pode_ver_contato(self.aluno, self.outro))

    def test_retirar_interesse_aceito_nao_permitido(self):
        i = services.manifestar_interesse(self.projeto, self.aluno)
        services.responder_interesse(i, self.autor, aceitar=True)
        with self.assertRaises(ValidationError):
            services.cancelar_interesse(i, self.aluno)
