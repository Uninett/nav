#!/usr/bin/env python

from URI import URI

class Navigator:
    """
    An object that represents the next-previous-status (navigation) parts of the page displayed
    """
    
    def __init__(self):

        self.view = ""
        self.previous = ""
        self.next = ""

    def setNavigator(self,limit,offset,address,number):
        """
        Sets the values of the navigator object

        - limit  : the number of results per page
        - offset : the number of the first result displayed on the page
        - address : the uri used when making the next an previous buttons
        - number : total number of restults returned from the query
        
        """
        
        number_int = int(number)
        number = str(number)
        offset_int = int(offset)
        offset = str(offset)
        limit_int = int(limit)
        limit = str(limit)
        number_int = int(number)
        number = str(number)

        next = str(offset_int+limit_int)
        previous = str(offset_int-limit_int)
        view_from = str(offset_int+1)
        view_to_int = offset_int + limit_int
        view_to = str(view_to_int)
        
        if offset_int:

            uri = URI(address)
            uri.setArguments(['limit'],limit)
            uri.setArguments(['offset'],previous)

            self.previous = uri.make()

        if limit_int+offset_int<number_int:

            uri = URI(address)
            uri.setArguments(['limit'],limit)
            uri.setArguments(['offset'],next)

            self.next = uri.make()

        if number_int:
            if limit_int>number_int:
                self.view = number+" hits"
            elif view_to_int>number_int:
                self.view = view_from+" - "+number+" of "+number
            else:
                self.view = view_from+" - "+view_to+" of "+number
        else:
            self.view = "Sorry, your search did not return any results"

            
