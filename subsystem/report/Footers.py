#!/usr/bin/env python

class Footers:
    """
    The bottom row of the report table. Where the sum of some columns is displayed
    """

    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the list of footers

        - cell : the cell to be appended

        """
        
        self.cells.append(cell)

