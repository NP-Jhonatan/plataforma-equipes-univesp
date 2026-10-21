# Equipes Univesp

Plataforma web colaborativa para **divulgação de ideias e formação de equipes** em projetos acadêmicos e extracurriculares entre estudantes da Univesp.

Projeto Integrador em Computação II (PJI240) · Engenharia de Computação · Univesp
Polos Itapevi, Diadema e Mogi das Cruzes · Comunidade parceira: Polo Itapevi

**Grupo:** Adilson Leite de Freitas Junior · João Paulo Santos de Melo · Jhonatan Pontes do Nascimento · Pedro Valentim Damasceno · Rafael de Almeida Neves · Ricardo de Oliveira Chamas · Robson Pereira Prado

---

## O que a plataforma faz

1. O estudante cria uma conta e preenche o **perfil** com curso, polo, interesses e competências.
2. Quem tem uma ideia **divulga o projeto**: título, resumo, descrição, objetivo, tipo (acadêmico ou extracurricular), competências procuradas e número de vagas.
3. Os demais **exploram os projetos**, com busca por palavra-chave e filtros por competência, tipo e vagas abertas.
4. O interessado clica em **“Tenho interesse em participar”** e pode deixar uma mensagem.
5. O autor vê os pedidos no projeto e no **painel**, e **aceita ou recusa** cada um. Quando as vagas são preenchidas, o projeto passa a “Equipe formada”.
6. O **contato** (e-mail, WhatsApp etc.) só fica visível entre o autor e os membros aceitos da equipe.
7. A página de **indicadores** mostra números de uso e o comparativo de competências **procuradas × oferecidas** (análise de dados).

## Como os requisitos do PI são atendidos

| Requisito | Onde está |
|---|---|
| Framework web | Django 5.2 (`config/`, apps `contas/` e `projetos/`) |
| Banco de dados | PostgreSQL em produção (via `DATABASE_URL`); SQLite opcional no desenvolvimento |
| Script web (JavaScript) | `static/js/app.js`: envio do interesse via API com `fetch`, contador de caracteres, barra de acessibilidade |
| API | Django REST Framework em `/api/` (`projetos/api.py`) |
| Nuvem | Render (`render.yaml` + `build.sh`), com Gunicorn e WhiteNoise |
| Acessibilidade | Recomendações do eMAG: atalhos de teclado [1][2][3], alto contraste, ajuste de fonte, HTML semântico, rótulos e erros associados aos campos, foco visível, `aria-live` |
| Controle de versão | Git + GitHub |
| Testes | 37 testes automatizados (`*/tests/`) e GitHub Actions rodando a cada push |
| Análise de dados (opcional) | Página `/indicadores/` |

## Rodando no seu computador

Pré-requisito: Python 3.11 ou mais recente.

```bash
git clone https://github.com/NP-Jhonatan/plataforma-equipes-univesp.git
cd plataforma-equipes-univesp

python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env                 # no Windows: copy .env.example .env

python manage.py migrate
python manage.py popular_dados --demo   # competências + usuários e projetos de exemplo
python manage.py createsuperuser        # opcional: acesso a /admin/
python manage.py runserver
```

Acesse http://127.0.0.1:8000. Os usuários de demonstração (`ana.silva`, `bruno.costa`, `carla.souza`, `diego.lima`, `elisa.rocha`) usam a senha `demo12345`.

### Usando PostgreSQL localmente (opcional)

Com Docker instalado:

```bash
docker compose up -d db
```

Depois, descomente a linha `DATABASE_URL` no arquivo `.env` e rode `python manage.py migrate` de novo.

## Testes

```bash
python manage.py test
```

Os testes cobrem regras de negócio (vagas, permissões, visibilidade de contato), telas, API e verificações básicas de acessibilidade. No GitHub, a aba **Actions** mostra o resultado a cada envio.

## API REST

Navegável pelo próprio navegador em `/api/`. Leitura é pública; escrita exige login (sessão ou HTTP Basic).

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/projetos/` | Lista projetos. Filtros: `?q=`, `?competencia=<slug>`, `?tipo=academico\|extracurricular`, `?abertos=true` |
| POST | `/api/projetos/` | Cria projeto (`titulo`, `resumo`, `descricao`, `objetivo`, `tipo`, `vagas`, `competencias_ids`) |
| GET/PATCH/DELETE | `/api/projetos/{id}/` | Detalhe; alteração e exclusão só pelo autor |
| POST | `/api/projetos/{id}/interesse/` | Manifesta interesse (`{"mensagem": "..."}`) |
| GET | `/api/interesses/` | Interesses que você enviou ou recebeu |
| POST | `/api/interesses/{id}/responder/` | Autor responde (`{"acao": "aceitar"}` ou `"recusar"`) |
| DELETE | `/api/interesses/{id}/` | Retira um interesse pendente |
| GET | `/api/competencias/` | Lista de competências |
| GET | `/api/perfis/{username}/` | Perfil público (contato só para membros da mesma equipe) |

## Publicando na nuvem (Render)

1. Crie uma conta em https://render.com entrando com o GitHub.
2. No painel, clique em **New → Blueprint** e selecione este repositório.
3. O Render lê o `render.yaml`, cria o banco PostgreSQL e o serviço web, e executa o `build.sh` (instala dependências, migra o banco e cadastra as competências).
4. Para carregar os dados de demonstração, abra o **Shell** do serviço e rode `python manage.py popular_dados --demo`. Para o admin, `python manage.py createsuperuser`.

No plano gratuito, o serviço “dorme” após 15 minutos sem acesso (a primeira visita depois disso demora cerca de 1 minuto) e o banco gratuito expira 30 dias após a criação. Para as apresentações, acesse o site alguns minutos antes.

## Estrutura

```
config/            configurações, URLs e WSGI
contas/            cadastro, perfil e competências
projetos/          projetos, interesses, regras (services.py), API (api.py), testes
templates/         páginas (Django Templates + Bootstrap 5)
static/            CSS, JavaScript, Bootstrap local e ícone
```

## Fluxo de trabalho do grupo

- Crie uma branch para cada tarefa: `git checkout -b feature/nome-da-tarefa`.
- Faça commits pequenos com mensagens claras, em português.
- Abra um Pull Request para a `main`. Os testes rodam automaticamente; peça revisão de um colega antes de juntar.

---

Protótipo acadêmico desenvolvido por estudantes. Não é um serviço oficial da Univesp.
