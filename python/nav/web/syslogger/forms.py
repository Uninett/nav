"""
forms and functions used for syslogger in NAV
"""

from django import forms
from nav.models.logger import Priority, LoggerCategory, Origin, LogMessageType
from nav.web.crispyforms import (
    FlatFieldset,
    FormRow,
    FormColumn,
    set_flat_form_attributes,
)

DATEFORMAT = ("%Y-%m-%d %H:%M",)


def _choice_values(model, field_name):
    """
    Generates a choice_values list to be used with ChoiceField etc.
    :param model: django model
    :param field_name: field to aggregate on
    :return: values_list based on model and field_name
    """
    choice_list = model.objects.values_list(field_name).distinct()
    choices = [(choice[0], choice[0]) for choice in choice_list]
    choices.sort()
    choices.insert(0, ('', '(All)'))
    return choices


class LoggerGroupSearchForm(forms.Form):
    """LoggerSearchForm"""

    facility = forms.ChoiceField(required=False)
    priority = forms.ChoiceField(required=False)
    mnemonic = forms.ChoiceField(required=False)
    origin = forms.ChoiceField(required=False)
    category = forms.ModelChoiceField(
        queryset=LoggerCategory.objects.all(), required=False, empty_label='(All)'
    )
    timestamp_from = forms.DateTimeField(input_formats=DATEFORMAT)
    timestamp_to = forms.DateTimeField(input_formats=DATEFORMAT)
    show_log = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(LoggerGroupSearchForm, self).__init__(*args, **kwargs)
        self.fields['facility'].choices = _choice_values(LogMessageType, 'facility')
        self.fields['priority'].choices = _choice_values(Priority, 'keyword')
        self.fields['mnemonic'].choices = _choice_values(LogMessageType, 'mnemonic')
        self.fields['origin'].choices = _choice_values(Origin, 'name')

        self.fields['timestamp_from'].widget.format = DATEFORMAT[0]
        self.fields['timestamp_to'].widget.format = DATEFORMAT[0]

        for field in ('facility', 'priority', 'mnemonic', 'origin', 'category'):
            self.fields[field].widget.attrs.update({"class": "select2"})

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend='Filter',
                                    fields=[
                                        FormRow(
                                            fields=[
                                                FormColumn(
                                                    fields=[self['facility']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['priority']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['mnemonic']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['origin']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['category']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['timestamp_from']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['timestamp_to']],
                                                    css_classes='medium-12',
                                                ),
                                                FormColumn(
                                                    fields=[self['show_log']],
                                                    css_classes='medium-12',
                                                ),
                                            ]
                                        )
                                    ],
                                    template='syslogger/frag-search-form-fieldset.html',
                                )
                            ],
                            css_classes='medium-12',
                        )
                    ]
                )
            ]
        )
