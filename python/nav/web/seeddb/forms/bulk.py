#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
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

class BulkImportForm(forms.Form):
    bulk_file = forms.FileField(label="Upload a bulk data file")

    bulk_data = forms.CharField(label="Or paste data here",
        widget=forms.Textarea(attrs={
                'rows': 25,
                'cols':80
                }))

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        bulk_file = self.files.get('bulk_file', None)
        if bulk_file:
            self.data['bulk_data'] = bulk_file.read()

    def get_raw_data(self):
        data = self.data.get('bulk_data', None)
        if isinstance(data, unicode):
            return data.encode('utf-8')
        else:
            return data
