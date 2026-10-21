from django.urls import path

from . import views

app_name = "projetos"

urlpatterns = [
    path("", views.ProjetoListView.as_view(), name="lista"),
    path("projetos/novo/", views.ProjetoCreateView.as_view(), name="criar"),
    path("projetos/<int:pk>/", views.ProjetoDetailView.as_view(), name="detalhe"),
    path("projetos/<int:pk>/editar/", views.ProjetoUpdateView.as_view(), name="editar"),
    path("projetos/<int:pk>/excluir/", views.ProjetoDeleteView.as_view(), name="excluir"),
    path("projetos/<int:pk>/interesse/", views.manifestar_interesse, name="manifestar_interesse"),
    path("interesses/<int:pk>/cancelar/", views.cancelar_interesse, name="cancelar_interesse"),
    path("interesses/<int:pk>/responder/", views.responder_interesse, name="responder_interesse"),
    path("painel/", views.painel, name="painel"),
    path("indicadores/", views.indicadores, name="indicadores"),
]
