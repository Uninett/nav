from django import forms

from nav.util import is_valid_ip


# TODO: Borrowed from newer radius. Need to be removed
# TODO: and imported from elsewhere
class MultitypeQueryWidget(forms.MultiWidget):
    """
    Widget for MultitypeQueryField
    """

    def decompress(self, value):
        return [value]

    def format_output(self, rendered_widgets):
        # FIXME: Added for better foundation integration
        # FIXME: Backport to radius
        return ''.join(
            [
                '<div class="medium-6 columns">',
                '<span class="dropdown prefix">',
                rendered_widgets[1],
                '</span>',
                '</div>',
                '<div class="medium-6 columns">',
                rendered_widgets[0],
                '</div>',
            ]
        )


# TODO: Borrowed from newer radius. Need to be removed
# TODO: and imported from elsewhere
class MultitypeQueryField(forms.MultiValueField):
    """
    Field that accepts a text query and a query type
    input, and validates the query according to the type.
    """

    def __init__(self, choices, validators={}, *args, **kwargs):
        """
        :param validators:  A dict that maps query type
        values to validators.
        """
        # Prevent Django from affecting "required" by setting the fields
        # ourselves
        super(MultitypeQueryField, self).__init__(fields=(), *args, **kwargs)
        self.fields = (
            forms.CharField(min_length=1),
            forms.ChoiceField(choices=choices),
        )
        self.widget = MultitypeQueryWidget(
            (forms.TextInput(), forms.Select(choices=choices))
        )
        self.query_validators = validators

    def validate(self, value):
        query = value[0]
        query_type = value[1]
        if query_type in self.query_validators:
            self.query_validators[query_type](query)

    def compress(self, data_list):
        return data_list


class NetworkSearchForm(forms.Form):
    """Form for searching in local networks"""

    QUERY_TYPES = (
        ('sysname', 'Sysname'),
        ('ip', 'IP'),
        ('mac', 'MAC'),
        ('port', 'Port Description'),
        ('vlan', 'Vlan'),
        ('room', 'Room'),
    )
    query = MultitypeQueryField(QUERY_TYPES)
    exact_results = forms.BooleanField(
        label='Search exact (no substring)', required=False
    )
    hide_ports = forms.BooleanField(
        label='Hide ports with no description', required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("query"):
            query, query_type = cleaned_data["query"]
            if query_type == "ip" and cleaned_data["exact_results"]:
                if not is_valid_ip(query):
                    self._errors['address'] = self.error_class(["Invalid IP address"])
        return cleaned_data
