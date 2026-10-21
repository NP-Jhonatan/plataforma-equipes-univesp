from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path("perfil/<str:username>/", views.perfil, name="perfil"),
]
