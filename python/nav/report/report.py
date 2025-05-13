# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
"""Representing a report object."""

import re
from urllib.parse import quote


class Field(object):
    def __init__(self):
        self.title = ""
        self.raw = ""

    def __repr__(self):
        return "<Field %s = %s>" % (self.title, self.raw)


class Report(object):
    """A nice formatted Report object, ready for presentation"""

    def __init__(self, configuration, database, query_dict):
        """The constructor of the Report class

        :param configuration: a ReportConfig object containing all the
                              configuration
        :param database: a DatabaseResult object that will be modified
                         according to the configuration
        :param query_dict: mutable Query Dict

        """

        self.rowcount = database.rowcount
        self.sums = database.sums
        self.report_id = configuration.report_id

        self.limit = int(str((self.set_limit(configuration.limit))))
        self.offset = int(str(self.set_offset(configuration.offset)))

        # oh, the smell, it kills me!
        if self.limit:
            self.formatted = database.result[self.offset : self.limit + self.offset]
        else:
            self.formatted = database.result
        self.dbresult = database.result

        self.query_args = self.strip_pagination_arguments(query_dict)

        self.title = configuration.title
        self.hide = configuration.hidden
        self.extra = configuration.extra

        self.name = configuration.name
        self.explain = configuration.explain
        self.uri = configuration.uri

        self.fields = configuration.sql_select + self.extra
        self.sql_fields = configuration.sql_select
        (self.field_name_map, self.field_num_map) = self.build_field_maps(self.fields)
        self.fields_count = len(self.fields)
        self.shown = self.hide_index()

        self.uri = self.remake_uri(self.uri)

        self.table = self.make_table_contents()
        footers = self.make_table_footers(self.sums)
        self.table.set_footers(footers)
        headers = self.make_table_headers(
            self.name, self.explain, configuration.order_by
        )
        self.table.set_headers(headers)

        self.form = self.make_form(self.name)
        self.database_error = database.error

    def set_limit(self, limit):
        """Returns the limit according to the configuration, or the default.

        :param limit: the configured limit or None
        :returns: the configured limit or 1000

        """
        if limit or limit == 0:
            return limit
        else:
            return 100000

    def set_offset(self, offset):
        """Returns the offset according to the configuration, or the default.

        :param offset: the configured offset or None
        :returns: the configured offset or 0
        """
        if offset:
            return offset
        else:
            return 0

    def strip_pagination_arguments(self, query_dict):
        """removes the 'limit' and 'offset' arguments from the query_dict

        :param query_dict: a dict-like object.
        :returns: the modified query_dict instance.

        """
        strippable = ('limit', 'offset')
        for field in strippable:
            if field in query_dict:
                del query_dict[field]
        return query_dict

    def build_field_maps(self, fields):
        """Returns two dicts mapping field numbers and names to each other.a

        :param fields: a list containing the field names
        :returns: (dict(fields_by_name), dict(fields_by_number)

        """
        fields_by_name = {}
        fields_by_number = {}

        for number, name in enumerate(fields):
            fields_by_name[name] = number
            fields_by_number[number] = name

        return fields_by_name, fields_by_number

    def remake_uri(self, uri):
        """takes a dict of uris associated to their names, and returns a dict
        of uris associated to their field numbers. this is a more effective
        approach than doing queries to a dictionary.

        :param uri: a dict of fieldnames and their uris
        :returns: a dict of fieldnumbers and their uris

        """
        uri_hash = uri
        uri_new = {}

        for key, value in uri_hash.items():
            if self.fields.count(key):
                key_index = self.fields.index(key)

                if self.shown.count(key_index):
                    uri_new[key_index] = value

        return uri_new

    def make_table_headers(self, names, explain, sort_fields=None):
        """Makes the table headers.

        :param names: a dict mapping field names to field numbers
        :param explain: a dict mapping field names to their explanations

        :returns: a list of cells that later will represent the headers of the
                  table

        """
        headers = Headers()
        sorted_field = sort_fields[0] if sort_fields else None

        # for each of the cols that will be displayed
        for header in self.shown:
            # get the names of it
            title = self.fields[header]

            if sorted_field == title:
                self.query_args['sort'] = '-' + title
                self.query_args['order_by'] = '-' + title
            else:
                self.query_args['sort'] = title
                self.query_args['order_by'] = title

            uri = "?{0}".format(self.query_args.urlencode())

            # change if the names exist in the overrider hash
            title = names.get(title, title)
            explanation = explain.get(title, "")

            field = Cell(title, uri, explanation)
            headers.append(field)

        return headers

    def make_table_footers(self, sums):
        """Makes the table footers. ie. the sums of the columns if specified.

        :param sums: a list containing the numbers of the fields that will be
                     summed.

        :returns: a list of cells that later will represent the footers of the
                  table

        """
        footers = Footers()

        # for each of the cols that will be displayed
        for footer in self.shown:
            # get the name of it
            title = self.fields[footer]

            this_sum = Cell()

            # change if the name exist in the overrider hash
            if title in sums:
                # Sum the results for a given title
                part_sum = 0
                for fmt in self.formatted:
                    if fmt[footer] is not None:
                        part_sum += int(str(fmt[footer]))

                total_sum = 0
                for res in self.dbresult:
                    if res[footer] is not None:
                        total_sum += int(str(res[footer]))

                if part_sum == total_sum:
                    this_sum.set_sum(str(part_sum))

                elif sums[title] == 0:
                    this_sum.set_sum("0")

                else:
                    this_sum.set_sum(str(part_sum) + "/" + str(total_sum))

            footers.append(this_sum)

        return footers

    def hide_index(self):
        """Makes a copy of the list of all fields where those that will be
        hidden is ignored

        :returns: the list of fields that will be displayed in the report.

        """
        shown = []
        for field in range(0, self.fields_count):
            if not self.hide.count(self.fields[field]):
                shown.append(field)

        return shown

    def make_table_contents(self):
        """Makes the contents of the table of the report.

        :returns: a table containing the data of the report (without header
                  and footer etc)

        """
        link_pattern = re.compile(r"\$(.+?)(?:$|\$|&|\"|\'|\s|;|/)", re.M)

        newtable = Table()
        for line in self.formatted:
            newline = Row()
            for field in self.shown:
                newfield = Cell()

                # the number of fields shown may be larger than the size
                # of the tuple returned from the database
                try:
                    if self.extra.count(self.field_num_map[field]):
                        text = self.fields[field]
                    else:
                        text = line[field]

                except KeyError:
                    text = "feil"

                newfield.set_text(text)

                if field in self.uri:
                    uri = self.uri[field]

                    links = link_pattern.findall(uri)
                    if links:
                        for column_ref in links:
                            value = str(line[self.field_name_map[column_ref]]) or ""
                            pattern = '$' + column_ref
                            uri = uri.replace(pattern, quote(value))
                    newfield.set_hyperlink(uri)

                newline.append(newfield)

            newtable.append(newline)

        return newtable

    def make_form(self, name):
        form = []

        for num, field_name in self.field_num_map.items():
            field = None
            # does not use aggregate function elements
            if not self.extra.count(field_name) and not self.sql_fields[num].count("("):
                field = Field()
                field.raw = self.sql_fields[num]
                if field_name in name:
                    field.title = name[field_name]
                else:
                    field.title = field_name

                form.append(field)

        return form


class Table(object):
    """A table that will contain the results of the report"""

    def __init__(self):
        self.rows = []
        self.header = []
        self.footer = []

    def append(self, row):
        """Appends a row to the table

        :param row: the row to be appended to the table

        """
        self.rows.append(row)

    def extend(self, rows):
        """Extends the table with a list of rows

        :param rows: the list of rows to append to the table

        """
        self.rows.extend(rows)

    def set_headers(self, headers):
        """Sets the headers of the table

        :param headers: the list of cells that represents the headers

        """
        self.header = headers

    def set_footers(self, footers):
        """Sets the footers of the table

        :param footers: the list of cells that represents the footers (the
                        bottom line)

        """
        self.footer = footers

    def set_contents(self, contents):
        """Sets the contents of the table

        :param contents: the new contents of the table

        """
        self.rows = contents


class Row(object):
    """A row of a table"""

    def __init__(self):
        self.cells = []

    def append(self, cell):
        """Appends a cell to the row

        :param cell : the cell to be appended

        """
        self.cells.append(cell)


class Cell(object):
    """One cell of the table"""

    text = uri = explanation = sum = None

    def __init__(self, text="", uri="", explanation=""):
        self.set_text(text)
        self.set_hyperlink(uri)
        self.set_explanation(explanation)
        self.sum = ""

    def set_text(self, text):
        """Sets the contents of the cell to the text specified

        :param text : the text to be used

        """
        self.text = unicode_utf8(text)

    def set_hyperlink(self, url):
        """Sets an URL to use as a hyperlink from the cell

        :param url: the text to be used as the url

        """
        self.uri = unicode_utf8(url)

    def set_explanation(self, explanation):
        """Sets the explanation of the column to the text specified

        :param explanation : the text to be used as the explanation

        """
        self.explanation = unicode_utf8(explanation)

    def set_sum(self, colsum):
        """Sets the colsum of the column to the text specified

        :param colsum: the text to be used as the colsum of the column

        """
        self.sum = unicode_utf8(colsum)


class Headers(object):
    """The top row of the report table. Where the titles and descriptions
    etc, is displayed.

    """

    def __init__(self):
        self.cells = []

    def append(self, cell):
        """Appends a cell to the list of headers

        :param cell: the cell to be appended

        """
        self.cells.append(cell)


class Footers(object):
    """The bottom row of the report table, where the sum of some columns is
    displayed

    """

    def __init__(self):
        self.cells = []

    def append(self, cell):
        """Appends a cell to the list of footers

        :param cell: the cell to be appended

        """
        self.cells.append(cell)


def unicode_utf8(thing):
    """Casts thing to unicode, assuming utf-8 encoding if a binary string.

    If the argument is None, it is returned unchanged.

    """
    if isinstance(thing, bytes):
        return thing.decode('utf-8')
    elif thing is not None:
        return str(thing)
