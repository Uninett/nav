#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms used for Bulk import of data"""

from django import forms
import six

from nav.bulkparse import BulkParseError, CommentStripper
from nav.bulkimport import BulkImportError


class BulkImportForm(forms.Form):
    """Generic bulk import form"""

    bulk_file = forms.FileField(label="Upload a bulk data file", required=False)

    bulk_data = forms.CharField(
        label="Or paste data here",
        required=False,
        widget=forms.Textarea(attrs={'rows': 25, 'cols': 80}),
    )

    def __init__(self, parser, *args, **kwargs):
        self.parser = parser
        kwargs['initial'] = {'bulk_data': "%s\n" % self.parser.get_header()}
        super(BulkImportForm, self).__init__(*args, **kwargs)

        if self.is_bound and self.is_valid():
            self.fields['bulk_file'].widget = forms.HiddenInput()
            self.fields['bulk_data'].widget = forms.HiddenInput()

    def get_raw_data(self):
        """Returns the bulk data as an utf-8 encoded string"""
        data = self.cleaned_data.get('bulk_data', None)
        if six.PY2 and isinstance(data, six.string_types):
            return data.encode('utf-8')
        else:
            return data

    def get_parser(self):
        """Returns a parser instance primed with the form's bulk data"""
        return self.parser(self.get_raw_data())

    def clean(self):
        """Ensures that either the bulk text is filled, or the bulk file
        uploaded.

        """
        if self._no_data_found() or self._is_bulk_data_unchanged():
            raise forms.ValidationError("There was no data in the form")

        return self.cleaned_data

    def clean_bulk_data(self):
        """Replaces the bulk data with the contents of the uploaded file, if any"""
        bulk_file = self.files.get("bulk_file", None)
        if bulk_file:
            cleaned_data = bulk_file.read().decode("utf-8")
        else:
            cleaned_data = self.cleaned_data.get("bulk_data", "")

        if self._is_bulk_data_empty(cleaned_data):
            raise forms.ValidationError("There was nothing to import")
        else:
            return cleaned_data

    def _no_data_found(self):
        bulk_file = self.files.get('bulk_file', None)
        bulk_data = self.cleaned_data.get('bulk_data', None)
        return not bulk_file and not bulk_data

    def _is_bulk_data_unchanged(self):
        bulk_data = self.cleaned_data.get('bulk_data', '').strip()
        bulk_initial = self.initial.get('bulk_data', '').strip()
        return bulk_data == bulk_initial

    @staticmethod
    def _is_bulk_data_empty(bulk_data):
        bulk_lines = bulk_data.split('\n')
        stripper = CommentStripper(iter(bulk_lines))
        stripped_lines = [l for l in stripper if l.strip()]
        return len(stripped_lines) < 1

    def bulk_process_check(self, importer):
        """Processes the bulk data using the importer and returns a list of
        status dictionaries for each line of the import.

        """
        data = self.get_raw_data()
        lines = data.split('\n')
        processed = []
        for line_num, objects in importer:
            if isinstance(objects, BulkParseError):
                processed.append(
                    {
                        'status': (
                            isinstance(objects, BulkImportError) and 'other' or 'syntax'
                        ),
                        'line_number': line_num,
                        'input': lines[line_num - 1],
                        'message': objects,
                    }
                )
            else:
                processed.append(
                    {
                        'status': 'ok',
                        'line_number': line_num,
                        'input': lines[line_num - 1],
                        'message': '',
                    }
                )
        return processed
