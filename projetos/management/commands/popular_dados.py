"""Cria competências básicas e, opcionalmente, dados de demonstração.

Uso:
    python manage.py popular_dados           # só competências
    python manage.py popular_dados --demo    # competências + usuários e projetos fictícios
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from contas.models import Competencia
from projetos.models import Interesse, Projeto

COMPETENCIAS = [
    "Python", "Django", "JavaScript", "HTML e CSS", "Banco de dados", "Análise de dados",
    "Design de interfaces", "Acessibilidade", "Redação acadêmica", "Revisão de textos",
    "Pesquisa bibliográfica", "Matemática", "Estatística", "Pedagogia", "Libras",
    "Gestão de projetos", "Comunicação", "Edição de vídeo", "Inglês", "Eletrônica",
]

SENHA_DEMO = "demo12345"

DEMO_USUARIOS = [
    ("ana.silva", "Ana", "Silva", "Engenharia de Computação", "Itapevi", ["Python", "Django", "Banco de dados"]),
    ("bruno.costa", "Bruno", "Costa", "Licenciatura em Matemática", "Diadema", ["Matemática", "Estatística", "Pedagogia"]),
    ("carla.souza", "Carla", "Souza", "Letras", "Mogi das Cruzes", ["Redação acadêmica", "Revisão de textos", "Inglês"]),
    ("diego.lima", "Diego", "Lima", "Ciência de Dados", "Itapevi", ["Python", "Análise de dados", "Estatística"]),
    ("elisa.rocha", "Elisa", "Rocha", "Pedagogia", "Diadema", ["Pedagogia", "Libras", "Comunicação"]),
]

DEMO_PROJETOS = [
    ("ana.silva", "App de caronas solidárias entre polos",
     "Aplicativo web para estudantes combinarem caronas até os polos nos dias de prova.",
     "Muitos colegas moram longe do polo e gastam muito com transporte nos dias de avaliação presencial. "
     "A ideia é criar um sistema simples de oferta e procura de caronas.",
     "Entregar um protótipo funcional e testá-lo com estudantes do Polo Itapevi.",
     Projeto.Tipo.EXTRACURRICULAR, ["Django", "JavaScript", "Design de interfaces"], 3),
    ("bruno.costa", "Grupo de estudos de Cálculo I",
     "Encontros semanais on-line para resolver listas de Cálculo juntos.",
     "Proposta de grupo de estudos colaborativo, com rodízio de quem apresenta cada tópico.",
     "Melhorar o desempenho do grupo nas avaliações de Cálculo I.",
     Projeto.Tipo.ACADEMICO, ["Matemática", "Comunicação"], 5),
    ("carla.souza", "Revista digital de contos dos estudantes",
     "Publicação semestral reunindo textos literários de alunos de todos os cursos.",
     "Queremos montar uma equipe editorial para selecionar, revisar e diagramar contos e crônicas.",
     "Publicar a primeira edição até o fim do semestre.",
     Projeto.Tipo.EXTRACURRICULAR, ["Revisão de textos", "Design de interfaces", "Edição de vídeo"], 4),
    ("diego.lima", "Painel de evasão no ensino superior a distância",
     "Análise de dados públicos do INEP sobre evasão em cursos EaD.",
     "Usar microdados do Censo da Educação Superior para entender padrões de evasão em cursos a distância.",
     "Produzir um painel interativo e um artigo curto com os principais achados.",
     Projeto.Tipo.ACADEMICO, ["Python", "Análise de dados", "Estatística", "Redação acadêmica"], 3),
]


class Command(BaseCommand):
    help = "Cria competências básicas e, com --demo, usuários e projetos de demonstração."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Cria também dados fictícios para apresentação.")

    def handle(self, *args, **opts):
        for nome in COMPETENCIAS:
            Competencia.objects.get_or_create(nome=nome)
        self.stdout.write(self.style.SUCCESS(f"{len(COMPETENCIAS)} competências disponíveis."))

        if not opts["demo"]:
            return

        comp = {c.nome: c for c in Competencia.objects.all()}
        usuarios = {}
        for username, nome, sobrenome, curso, polo, competencias in DEMO_USUARIOS:
            user, criado = User.objects.get_or_create(
                username=username,
                defaults={"first_name": nome, "last_name": sobrenome, "email": f"{username}@exemplo.com"},
            )
            if criado:
                user.set_password(SENHA_DEMO)
                user.save()
            perfil = user.perfil
            perfil.curso, perfil.polo = curso, polo
            perfil.contato = f"{username}@exemplo.com"
            perfil.save()
            perfil.competencias.set([comp[c] for c in competencias])
            usuarios[username] = user

        for autor, titulo, resumo, descricao, objetivo, tipo, competencias, vagas in DEMO_PROJETOS:
            projeto, _ = Projeto.objects.get_or_create(
                titulo=titulo,
                defaults=dict(autor=usuarios[autor], resumo=resumo, descricao=descricao,
                              objetivo=objetivo, tipo=tipo, vagas=vagas),
            )
            projeto.competencias_desejadas.set([comp[c] for c in competencias])

        carona = Projeto.objects.get(titulo__startswith="App de caronas")
        Interesse.objects.get_or_create(projeto=carona, estudante=usuarios["diego.lima"],
                                        defaults={"mensagem": "Posso ajudar com o back-end em Django."})
        Interesse.objects.get_or_create(projeto=carona, estudante=usuarios["carla.souza"],
                                        defaults={"mensagem": "Tenho interesse em cuidar dos textos e da divulgação.",
                                                  "status": Interesse.Status.ACEITO})

        self.stdout.write(self.style.SUCCESS(
            f"Dados de demonstração criados. Usuários: {', '.join(usuarios)} (senha: {SENHA_DEMO})."
        ))
