"""
forms and functions used for loggerhandler in NAV
"""

from django import forms
from nav.models.logger import Priority, LoggerCategory, Origin, LogMessageType

DATEFORMAT = ("%Y-%m-%d %H:%M:%S",)

def choice_values(model, field_name):
    """
    Generates a choice_values list to be used with ChoiceField etc.
    :param model: django model
    :param field_name: field to aggregate on
    :return: values_list based on model and field_name
    """
    choice_list = model.objects.values_list(
        field_name).select_related().distinct()
    choices = [(choice[0], choice[0]) for choice in choice_list]
    choices.sort()
    choices.insert(0, ('', u'(All)'))
    return choices


class LoggerGroupSearchForm(forms.Form):
    """LoggerSearchForm"""

    facility = forms.ChoiceField(
        choices=choice_values(LogMessageType, 'facility'), required=False)
    priority = forms.ChoiceField(choices=choice_values(Priority, 'keyword'),
        required=False)
    mnemonic = forms.ChoiceField(
        choices=choice_values(LogMessageType, 'mnemonic'), required=False)
    origin = forms.ChoiceField(choices=choice_values(Origin, 'name'),
        required=False)
    category = forms.ModelChoiceField(queryset=LoggerCategory.objects.all(),
        required=False, empty_label=u'(All)')
    timestamp_from = forms.DateTimeField(input_formats=DATEFORMAT)
    timestamp_to = forms.DateTimeField(input_formats=DATEFORMAT)
    show_log = forms.BooleanField(required=False)