#!/usr/bin/env python

class Row:
    """
    A row of a table
    """

    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the row

        - cell : the cell to be appended

        """
        
        self.cells.append(cell)
