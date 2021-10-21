# Django 4.0:
# s/nav.compatibility \(import force_str\)/django.utils.encoding \1/'
try:
    from django.utils.encoding import force_str
except ImoprtError:
    from django.utils.encoding import force_text as force_str

try:
    from django.utils.encoding import smart_str
except ImoprtError:
    from django.utils.encoding import smart_text as smart_str
