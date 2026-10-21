"""Filtros para renderizar campos de formulário com Bootstrap e atributos de acessibilidade."""

from django import template

register = template.Library()


@register.filter
def tipo_widget(campo):
    return campo.field.widget.__class__.__name__


@register.filter
def campo_acessivel(campo, classe="form-control"):
    """Adiciona classe CSS, aria-describedby e aria-invalid ao widget."""
    attrs = {"class": classe}
    descritores = []
    if campo.help_text:
        descritores.append(f"{campo.auto_id}_ajuda")
    if campo.errors:
        descritores.append(f"{campo.auto_id}_erro")
        attrs["aria-invalid"] = "true"
        attrs["class"] += " is-invalid"
    if descritores:
        attrs["aria-describedby"] = " ".join(descritores)
    if campo.field.required:
        attrs["required"] = True
    return campo.as_widget(attrs=attrs)


@register.simple_tag(takes_context=True)
def url_pagina(context, numero):
    qs = context.get("querystring", "")
    return f"?{qs + '&' if qs else ''}page={numero}"
