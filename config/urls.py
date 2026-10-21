from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from projetos import api

router = DefaultRouter()
router.register("projetos", api.ProjetoViewSet, basename="projeto")
router.register("competencias", api.CompetenciaViewSet, basename="competencia")
router.register("interesses", api.InteresseViewSet, basename="interesse")
router.register("perfis", api.PerfilViewSet, basename="perfil")

admin.site.site_header = "Administração — Equipes Univesp"
admin.site.site_title = "Equipes Univesp"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((router.urls, "api"))),
    path("api/auth/", include("rest_framework.urls")),
    path("contas/", include("django.contrib.auth.urls")),
    path("contas/", include("contas.urls")),
    path("", include("projetos.urls")),
]
