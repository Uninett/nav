#
# Copyright (C) 2010 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Formatting of table data to readable text."""


class SimpleTableFormatter(object):
    def __init__(self, data):
        """Initializes the table formatter with data.

        data -- a list of lists.  All the lists must be of the same
        length.

        """
        self.data = data

    def __str__(self):
        return self.get_formatted_table()

    def get_formatted_table(self):
        if not self.data:
            return ''
        widths = self._find_widest_elements()
        output = []
        for row in self.data:
            output.append(self._format_row(row, widths))
        return '\n'.join(output)

    def _format_row(self, row, widths):
        new_row = []
        for index, cell in enumerate(row):
            fmt = "%%%ds" % widths[index]
            new_row.append(fmt % str(cell))
        return ' | '.join(new_row)

    def _find_widest_elements(self):
        if not self.data:
            return [0]
        max_widths = []
        for column_number in range(self._get_column_count()):
            max_widths.append(self._get_max_width_of_column(column_number))
        return max_widths

    def _get_max_width_of_column(self, column_number):
        widths = [len(str(row[column_number])) for row in self.data]
        return max(widths)

    def _get_column_count(self):
        return len(self.data[0])
