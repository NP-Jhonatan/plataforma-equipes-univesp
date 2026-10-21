from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from contas.models import Competencia

from . import services
from .forms import FiltroForm, InteresseForm, ProjetoForm
from .models import Interesse, Projeto


def filtrar_projetos(params, queryset=None):
    """Aplica busca e filtros (usado pela listagem e pela API)."""
    qs = queryset if queryset is not None else Projeto.objects.all()
    form = FiltroForm(params or None)
    if form.is_valid():
        dados = form.cleaned_data
        if dados.get("q"):
            termo = dados["q"]
            qs = qs.filter(
                Q(titulo__icontains=termo) | Q(resumo__icontains=termo)
                | Q(descricao__icontains=termo) | Q(competencias_desejadas__nome__icontains=termo)
            )
        if dados.get("competencia"):
            qs = qs.filter(competencias_desejadas=dados["competencia"])
        if dados.get("tipo"):
            qs = qs.filter(tipo=dados["tipo"])
        if dados.get("abertos"):
            qs = qs.filter(status=Projeto.Status.ABERTO)
    return form, qs.distinct()


class ProjetoListView(ListView):
    model = Projeto
    template_name = "projetos/lista.html"
    context_object_name = "projetos"
    paginate_by = 9

    def get_queryset(self):
        base = Projeto.objects.select_related("autor").prefetch_related("competencias_desejadas")
        self.filtro, qs = filtrar_projetos(self.request.GET, base)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro"] = self.filtro
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        ctx["filtrando"] = any(v for k, v in self.request.GET.items() if k != "page")
        return ctx


class ProjetoDetailView(DetailView):
    model = Projeto
    template_name = "projetos/detalhe.html"
    context_object_name = "projeto"

    def get_queryset(self):
        return Projeto.objects.select_related("autor", "autor__perfil").prefetch_related("competencias_desejadas")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projeto, user = self.object, self.request.user
        ctx["eh_autor"] = user.is_authenticated and user.pk == projeto.autor_id
        aceitos = projeto.interesses.filter(status=Interesse.Status.ACEITO).select_related("estudante__perfil")
        ctx["membros"] = [
            {"usuario": i.estudante, "contato": services.pode_ver_contato(user, i.estudante)} for i in aceitos
        ]
        ctx["contato_autor_visivel"] = services.pode_ver_contato(user, projeto.autor) and not ctx["eh_autor"]
        if ctx["eh_autor"]:
            ctx["pendentes"] = projeto.interesses.filter(status=Interesse.Status.PENDENTE).select_related("estudante__perfil")
        elif user.is_authenticated:
            ctx["meu_interesse"] = projeto.interesses.filter(estudante=user).first()
            ctx["form_interesse"] = InteresseForm()
        return ctx


class SomenteAutorMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.get_object().autor_id == self.request.user.pk


class ProjetoCreateView(LoginRequiredMixin, CreateView):
    model = Projeto
    form_class = ProjetoForm
    template_name = "projetos/form.html"

    def form_valid(self, form):
        form.instance.autor = self.request.user
        messages.success(self.request, "Projeto publicado! Agora outros estudantes podem encontrá-lo.")
        return super().form_valid(form)


class ProjetoUpdateView(SomenteAutorMixin, UpdateView):
    model = Projeto
    form_class = ProjetoForm
    template_name = "projetos/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Projeto atualizado.")
        return super().form_valid(form)


class ProjetoDeleteView(SomenteAutorMixin, DeleteView):
    model = Projeto
    template_name = "projetos/confirmar_exclusao.html"
    success_url = reverse_lazy("projetos:painel")

    def form_valid(self, form):
        messages.success(self.request, "Projeto excluído.")
        return super().form_valid(form)


@login_required
@require_POST
def manifestar_interesse(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    form = InteresseForm(request.POST)
    if form.is_valid():
        try:
            services.manifestar_interesse(projeto, request.user, form.cleaned_data["mensagem"])
            messages.success(request, "Interesse enviado! O autor do projeto vai avaliar seu pedido.")
        except ValidationError as erro:
            messages.error(request, erro.messages[0])
    else:
        messages.error(request, "Não foi possível enviar seu interesse. Verifique a mensagem.")
    return redirect(projeto)


@login_required
@require_POST
def cancelar_interesse(request, pk):
    interesse = get_object_or_404(Interesse, pk=pk, estudante=request.user)
    projeto = interesse.projeto
    try:
        services.cancelar_interesse(interesse, request.user)
        messages.success(request, "Seu interesse foi retirado.")
    except ValidationError as erro:
        messages.error(request, erro.messages[0])
    return redirect(request.POST.get("proximo") or projeto.get_absolute_url())


@login_required
@require_POST
def responder_interesse(request, pk):
    interesse = get_object_or_404(Interesse, pk=pk, projeto__autor=request.user)
    aceitar = request.POST.get("acao") == "aceitar"
    try:
        services.responder_interesse(interesse, request.user, aceitar)
        nome = interesse.estudante.get_full_name() or interesse.estudante.username
        messages.success(request, f"{nome} foi {'adicionado(a) à equipe' if aceitar else 'informado(a) da recusa'}.")
    except ValidationError as erro:
        messages.error(request, erro.messages[0])
    return redirect(interesse.projeto)


@login_required
def painel(request):
    meus_projetos = (
        request.user.projetos.annotate(
            n_pendentes=Count("interesses", filter=Q(interesses__status=Interesse.Status.PENDENTE)),
            n_membros=Count("interesses", filter=Q(interesses__status=Interesse.Status.ACEITO)),
        )
    )
    meus_interesses = request.user.interesses.select_related("projeto", "projeto__autor")
    return render(request, "projetos/painel.html", {
        "meus_projetos": meus_projetos,
        "meus_interesses": meus_interesses,
    })


def indicadores(request):
    """Indicadores simples de uso da plataforma (análise de dados)."""
    total_interesses = Interesse.objects.count()
    respondidos = Interesse.objects.exclude(status=Interesse.Status.PENDENTE).count()
    aceitos = Interesse.objects.filter(status=Interesse.Status.ACEITO).count()

    competencias = (
        Competencia.objects.annotate(
            procura=Count("projetos", distinct=True),
            oferta=Count("perfis", distinct=True),
        )
        .filter(Q(procura__gt=0) | Q(oferta__gt=0))
        .order_by("-procura", "-oferta", "nome")[:10]
    )
    maior = max([max(c.procura, c.oferta) for c in competencias] or [1]) or 1

    contexto = {
        "total_projetos": Projeto.objects.count(),
        "projetos_abertos": Projeto.objects.filter(status=Projeto.Status.ABERTO).count(),
        "equipes_formadas": Projeto.objects.filter(interesses__status=Interesse.Status.ACEITO).distinct().count(),
        "total_interesses": total_interesses,
        "taxa_aceite": round(100 * aceitos / respondidos) if respondidos else None,
        "por_tipo": Projeto.objects.values("tipo").annotate(total=Count("id")).order_by("tipo"),
        "competencias": [
            {"nome": c.nome, "slug": c.slug, "procura": c.procura, "oferta": c.oferta,
             "pct_procura": round(100 * c.procura / maior), "pct_oferta": round(100 * c.oferta / maior)}
            for c in competencias
        ],
        "rotulos_tipo": dict(Projeto.Tipo.choices),
    }
    return render(request, "projetos/indicadores.html", contexto)
