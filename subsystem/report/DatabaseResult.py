#!/usr/bin/env python

import psycopg

class DatabaseResult:
    """
    The restults obtained from the database
    """

    def __init__(self,reportConfig):
        """
        Does everything in the constructor. queries and returnes the values from the database, according to the configuration

        - reportConfig : the configuration to use when 
        """
        
        self.sql = ""
        self.originalSQL = ""
        self.result = []
        self.rowcount = 0
        self.sums = {}
        self.error = ""

        connection = psycopg.connect(dsn="host=localhost user=manage dbname=manage password=eganam")
        database = connection.cursor()

        self.sql = reportConfig.makeSQL()
        #print self.sql
        sql = reportConfig.orig_sql
        self.originalSQL = sql

        try:
            database.execute(self.sql)
            go_on = 1
            #print self.sql
            self.result = database.fetchall()

            ## total count of the rows returned
            totalSQL = reportConfig.makeTotalSQL()
            database.execute(totalSQL)
            self.rowcount = database.rowcount

            ## handling of the "sum" option
            sumsql = reportConfig.makeSumSQL()
            database.execute(sumsql)
            sums = database.fetchone()

            ## coherce the results from the databasequery to the field-labels
            for sum in reportConfig.sum:
                self.sums[sum] = sums[reportConfig.sum.index(sum)]


        except psycopg.ProgrammingError,p:
            #raise ProblemExistBetweenKeyboardAndChairException
            self.error = "Configuration error! The report generator is not able to do such things."+str(p)
