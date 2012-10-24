from django import forms
from nav.models.logger import Priority, LoggerCategory, Origin, LogMessageType


class LoggerSearchForm(forms.Form):
    DATEFORMAT = "%Y-%m-%d %H:%M:%S"

    priority = forms.ModelMultipleChoiceField(queryset=Priority.objects.all())
    message_type = forms.ModelMultipleChoiceField(queryset=LogMessageType.objects.all())
    category = forms.ModelMultipleChoiceField(queryset=LoggerCategory.objects.all())
    origin = forms.ModelMultipleChoiceField(queryset=Origin.objects.all())
    timestamp_from = forms.DateTimeField(input_formats=DATEFORMAT)
    timestamp_to = forms.DateTimeField(input_formats=DATEFORMAT)