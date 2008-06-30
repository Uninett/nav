# -*- coding: utf-8 -*-
# $Id: DatabaseResult.py 3425 2006-06-08 13:07:54Z mortenv $
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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

        connection = db.getConnection('webfront','manage')

        database = connection.cursor()

        self.sql = reportConfig.makeSQL()
        sql = reportConfig.orig_sql
        self.originalSQL = sql
        self.sums = dict([(sum_key, '') for sum_key in reportConfig.sum])

        try:
            database.execute(self.sql)
            self.result = database.fetchall()

            ## total count of the rows returned
            totalSQL = reportConfig.makeTotalSQL()
            database.execute(totalSQL)
            self.rowcount = database.rowcount

            ## handling of the "sum" option
            if self.sums:
                sumsql = reportConfig.makeSumSQL()
                database.execute(sumsql)
                sums = database.fetchone()

                # Converting float to int, tuple to list
                sums_list = []
                for index, sum in enumerate(sums):
                    sums_list.append(int(long(sum)))

                sums = sums_list

            ## coherce the results from the databasequery to the field-labels
                if sums:
                    for sum in reportConfig.sum:
                        self.sums[sum] = sums[reportConfig.sum.index(sum)]


        except psycopg.ProgrammingError,p:
            #raise ProblemExistBetweenKeyboardAndChairException
            self.error = "Configuration error! The report generator is not able to do such things."+str(p)
