#!/usr/bin/env python

class Cell:
    """
    One cell of the table
    """

    def __init__(self,text="",uri="",explanation=""):

        self.text = text
        self.uri = uri
        self.explanation = explanation
        self.sum = ""

    def setText(self,text):
        """
        Sets the contents of the cell to the text specified

        - text : the text to be used
        
        """
        
        self.text = text


    def setUri(self,uri):
        """
        Sets the uri of the cell to the text specified

        - uri : the text to be used as the uri

        """
        
        self.uri = uri


    def setExplanation(self,explanation):
        """
        Sets the explanation of the column to the text specified

        - explanation : the text to be used as the explanation

        """
        
        self.explanation = explanation

    def setSum(self,sum):
        """
        Sets the sum of the column to the text specified

        - sum : the text to be used as the sum of the column

        """
        
        self.sum = sum


