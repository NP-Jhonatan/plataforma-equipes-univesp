from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from projetos.services import pode_ver_contato

from .forms import CadastroForm, PerfilForm, UsuarioForm


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("projetos:lista")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "Conta criada! Complete seu perfil para que os colegas conheçam suas competências.")
        return redirect("contas:editar_perfil")
    return render(request, "registration/cadastro.html", {"form": form})


def perfil(request, username):
    usuario = get_object_or_404(User.objects.select_related("perfil"), username=username)
    return render(request, "contas/perfil.html", {
        "usuario_perfil": usuario,
        "perfil": usuario.perfil,
        "projetos": usuario.projetos.all()[:10],
        "contato_visivel": pode_ver_contato(request.user, usuario),
    })


@login_required
def editar_perfil(request):
    perfil = request.user.perfil
    form_usuario = UsuarioForm(request.POST or None, instance=request.user, prefix="u")
    form_perfil = PerfilForm(request.POST or None, instance=perfil, prefix="p")
    if request.method == "POST" and form_usuario.is_valid() and form_perfil.is_valid():
        form_usuario.save()
        form_perfil.save()
        messages.success(request, "Perfil atualizado.")
        return redirect(perfil)
    return render(request, "contas/editar_perfil.html", {"form_usuario": form_usuario, "form_perfil": form_perfil})
