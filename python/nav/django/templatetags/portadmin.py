from django import template

register = template.Library()


@register.filter
def drawLight(value):
    if value == 1:
        return "green.png"
    else:
        return "red.png"
