from django import forms

from contas.forms import salvar_novas_competencias
from contas.models import Competencia

from .models import Interesse, Projeto


class ProjetoForm(forms.ModelForm):
    novas_competencias = forms.CharField(
        label="Outras competências", required=False,
        help_text="Não encontrou na lista? Digite separando por vírgula.",
    )

    class Meta:
        model = Projeto
        fields = ("titulo", "resumo", "descricao", "objetivo", "tipo",
                  "competencias_desejadas", "vagas", "status")
        widgets = {
            "resumo": forms.TextInput(attrs={"maxlength": 200, "data-contador": "true"}),
            "descricao": forms.Textarea(attrs={"rows": 6}),
            "objetivo": forms.Textarea(attrs={"rows": 3}),
            "competencias_desejadas": forms.CheckboxSelectMultiple,
        }

    def save(self, commit=True):
        projeto = super().save(commit=commit)
        if commit:
            projeto.competencias_desejadas.add(
                *salvar_novas_competencias(self.cleaned_data.get("novas_competencias"))
            )
        return projeto


class InteresseForm(forms.ModelForm):
    class Meta:
        model = Interesse
        fields = ("mensagem",)
        widgets = {"mensagem": forms.Textarea(attrs={"rows": 3, "maxlength": 500, "data-contador": "true"})}
        labels = {"mensagem": "Mensagem para o autor (opcional)"}


class FiltroForm(forms.Form):
    q = forms.CharField(label="Buscar", required=False,
                        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Título, tema ou palavra-chave"}))
    competencia = forms.ModelChoiceField(
        label="Competência", queryset=Competencia.objects.all(), required=False,
        empty_label="Todas", to_field_name="slug",
    )
    tipo = forms.ChoiceField(label="Tipo", required=False,
                             choices=[("", "Todos")] + list(Projeto.Tipo.choices))
    abertos = forms.BooleanField(label="Somente projetos com vagas abertas", required=False)
