#
# Copyright (C) 2008 Uninett AS
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
#
"""Represents the meta information and result from a database query."""

import psycopg2

from nav import db


class DatabaseResult(object):
    """The results obtained from the database"""

    def __init__(self, report_config):
        """Does everything in the constructor. queries and returns the values
        from the database, according to the configuration

        :param report_config: a ReportConfig object containing the SQL query.

        """
        self.sql = ""
        self.result = []
        self.rowcount = 0
        self.sums = {}
        self.error = ""
        self.hidden = []

        connection = db.getConnection('default')
        cursor = connection.cursor()

        self.sql, self.parameters = report_config.make_sql()

        # Make a dictionary of which columns to summarize
        self.sums = {sum_key: '' for sum_key in report_config.sum}

        try:
            cursor.execute(self.sql, self.parameters or None)
            self.result = cursor.fetchall()

            # A list of the column headers.
            report_config.sql_select = [col.name for col in cursor.description]

            # Total count of the rows returned.
            self.rowcount = len(self.result)

        except psycopg2.ProgrammingError as error:
            self.error = (
                "There was an unhandled SQL error! There may be "
                "something wrong with the definition of the '{}' "
                "report: {}".format(report_config.title, error)
            )

        except psycopg2.DataError as error:
            self.error = (
                "Data error! Some of your input data is of an invalid type: {}".format(
                    error
                )
            )
        else:
            self.error = report_config.error

    def __repr__(self):
        return "<{} sql={!r} parameters={!r}>".format(
            self.__class__.__name__,
            self.sql,
            self.parameters,
        )
