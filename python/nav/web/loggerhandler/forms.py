from django import forms
from nav.models.logger import Priority, LoggerCategory, Origin, LogMessageType

DATEFORMAT = ("%Y-%m-%d %H:%M:%S",)

class LoggerSearchForm(forms.Form):
    priority = forms.ModelMultipleChoiceField(queryset=Priority.objects.all(), required=False)
    message_type = forms.ModelMultipleChoiceField(queryset=LogMessageType.objects.all(), required=False)
    category = forms.ModelMultipleChoiceField(queryset=LoggerCategory.objects.all(), required=False)
    origin = forms.ModelMultipleChoiceField(queryset=Origin.objects.all(), required=False)
    timestamp_from = forms.DateTimeField(input_formats=DATEFORMAT)
    timestamp_to = forms.DateTimeField(input_formats=DATEFORMAT)

class LoggerGroupSearchForm(forms.Form):
    priority = forms.ModelChoiceField(queryset=Priority.objects.all(), required=False)
    message_type = forms.ModelChoiceField(queryset=LogMessageType.objects.all(), required=False)
    category = forms.ModelChoiceField(queryset=LoggerCategory.objects.all(), required=False)
    origin = forms.ModelChoiceField(queryset=Origin.objects.all(), required=False)
    timestamp_from = forms.DateTimeField(input_formats=DATEFORMAT)
    timestamp_to = forms.DateTimeField(input_formats=DATEFORMAT)