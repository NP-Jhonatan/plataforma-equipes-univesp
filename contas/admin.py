from django.contrib import admin

from .models import Competencia, Perfil


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "curso", "polo")
    search_fields = ("usuario__username", "usuario__first_name", "curso", "polo")
    filter_horizontal = ("competencias",)
