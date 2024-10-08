"""Template filters for forms"""

from django import forms, template

register = template.Library()


# Copied from
# https://github.com/django-crispy-forms/django-crispy-forms/blob/1.8.1/crispy_forms/templatetags/crispy_forms_field.py
@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.inclusion_tag('foundation-5/field.html')
def show_field(field):
    """Renders a form field using a predefined template.

    Usage::

        {% load forms %}
        {% show_field form.my_field %}


    :param field: The form field to be rendered.
    :type field: django.forms.BoundField
    :return: A dictionary that will be used as a template context for the field
    template.
    :rtype: dict
    """
    return {'field': field}
