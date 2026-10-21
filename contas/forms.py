from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Competencia, Perfil


def salvar_novas_competencias(texto):
    """Cria (se preciso) competências digitadas separadas por vírgula."""
    novas = []
    for nome in {n.strip() for n in (texto or "").split(",") if n.strip()}:
        existente = Competencia.objects.filter(nome__iexact=nome).first()
        novas.append(existente or Competencia.objects.create(nome=nome[:60]))
    return novas


class CadastroForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", help_text="Use preferencialmente seu e-mail institucional.")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Nome de usuário"}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Nome", "last_name": "Sobrenome", "email": "E-mail"}


class PerfilForm(forms.ModelForm):
    novas_competencias = forms.CharField(
        label="Outras competências", required=False,
        help_text="Não encontrou na lista? Digite separando por vírgula.",
    )

    class Meta:
        model = Perfil
        fields = ("curso", "polo", "bio", "interesses", "competencias", "contato")
        widgets = {
            "competencias": forms.CheckboxSelectMultiple,
            "bio": forms.Textarea(attrs={"rows": 4, "maxlength": 600}),
        }

    def save(self, commit=True):
        perfil = super().save(commit=commit)
        if commit:
            perfil.competencias.add(*salvar_novas_competencias(self.cleaned_data.get("novas_competencias")))
        return perfil
