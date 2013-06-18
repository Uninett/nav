#
# Copyright (C) 2003-2004 Norwegian University of Science and Technology
# Copyright (C) 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Represents the meta information and result from a database query."""

from nav import db
import psycopg2


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
        database = connection.cursor()

        self.sql = report_config.make_sql()

        ## Make a dictionary of which columns to summarize
        self.sums = dict([(sum_key, '') for sum_key in report_config.sum])

        try:
            database.execute(self.sql)
            self.result = database.fetchall()

            # A list of the column headers.
            col_head = []
            for col in range(0, len(database.description)):
                col_head.append(database.description[col][0])
            report_config.sql_select = col_head

            ## Total count of the rows returned.
            self.rowcount = len(self.result)

        except psycopg2.ProgrammingError as error:
            #raise ProblemExistBetweenKeyboardAndChairException
            self.error = ("Configuration error! The report generator is not "
                          "able to do such things. " + str(error))
