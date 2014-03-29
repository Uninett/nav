#
# Copyright (C) 2014 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Contains customized forms for NAV usage"""

from django import forms
from django.utils.safestring import mark_safe


class InlineCheckBoxSelectMultiple(forms.CheckboxSelectMultiple):
    """Display the list of checkboxes with inline style"""
    def render(self, name, value, attrs=None, choices=()):
        html = super(InlineCheckBoxSelectMultiple, self).render(
            name, value, attrs, choices)
        return mark_safe(html.replace('<ul>', '<ul class="inline-list">'))


class InlineMultipleChoiceField(forms.MultipleChoiceField):
    """Use inline widget for displaying checkboxes"""
    widget = InlineCheckBoxSelectMultiple
