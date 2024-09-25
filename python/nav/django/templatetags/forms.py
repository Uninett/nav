"""Template filters for forms"""

from django import forms, template

register = template.Library()


# Copied from
# https://github.com/django-crispy-forms/django-crispy-forms/blob/1.8.1/crispy_forms/templatetags/crispy_forms_field.py
@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)
