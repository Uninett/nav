# -*- coding: utf-8 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#          Jørgen Abrahamsen <jorgen.abrahamsen@uninett.no>
#

from nav import db
import psycopg

class DatabaseResult:
    """
    The restults obtained from the database
    """

    def __init__(self,reportConfig):
        """
        Does everything in the constructor. queries and returnes the values
        from the database, according to the configuration

        - reportConfig : the configuration to use when
        """

        self.sql = ""
        self.originalSQL = ""
        self.result = []
        self.rowcount = 0
        self.sums = {}
        self.error = ""
        self.hidden = []

        connection = db.getConnection('default')

        database = connection.cursor()

        self.sql = reportConfig.makeSQL()
        sql = reportConfig.orig_sql
        self.originalSQL = sql

        ## Make a dictionary of which columns to summarize
        self.sums = dict([(sum_key, '') for sum_key in reportConfig.sum])

        try:
            database.execute(self.sql)
            self.result = database.fetchall()

            ## Total count of the rows returned - no need for SQL query.
            self.rowcount = len(self.result)

        except psycopg.ProgrammingError,p:
            #raise ProblemExistBetweenKeyboardAndChairException
            self.error = "Configuration error! The report generator is not able to do such things. " + str(p)
