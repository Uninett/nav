#!/usr/bin/env python

class Table:
    """
    A table that will contain the results of the report
    """
    
    def __init__(self):

        self.rows = []
        self.header = []
        self.footer = []

    def append(self,row):
        """
        Appends a row to the table

        - row : the row to be appended to the table

        """
        
        self.rows.append(row)

    def extend(self,listOfRows):
        """
        Extends the table with a list of rows

        - listOfRows : the list of rows to append to the table

        """
        
        self.rows.extend(listOfRows)

    def setHeaders(self,header):
        """
        Sets the headers of the table

        - header : the list of cells that represents the header

        """
        
        self.header = header

    def setFooters(self,footer):
        """
        Sets the footers of the table

        - footer : the list of cells that represents the footer (the bottom line)

        """
        
        self.footer = footer

    def setContents(self,contents):
        """
        Sets the contents of the table

        - contents : the new contents of the table

        """
        
        self.rows = contents
    
