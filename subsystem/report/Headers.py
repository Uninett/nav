#!/usr/bin/env python

class Headers:
    """
    The top row of the report table. Where the titles and descriptions etc, is displayed
    """
    
    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the list of headers

        - cell : the cell to be appended

        """
        
        self.cells.append(cell)
