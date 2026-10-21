from django.contrib import admin

from .models import Interesse, Projeto


class InteresseInline(admin.TabularInline):
    model = Interesse
    extra = 0
    readonly_fields = ("criado_em", "respondido_em")


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "tipo", "status", "vagas", "criado_em")
    list_filter = ("tipo", "status", "competencias_desejadas")
    search_fields = ("titulo", "resumo", "descricao", "autor__username")
    filter_horizontal = ("competencias_desejadas",)
    inlines = [InteresseInline]


@admin.register(Interesse)
class InteresseAdmin(admin.ModelAdmin):
    list_display = ("estudante", "projeto", "status", "criado_em")
    list_filter = ("status",)
    search_fields = ("estudante__username", "projeto__titulo")
