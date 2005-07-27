# -*- coding: ISO8859-1 -*-
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
# $Id$
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#
"""
Two small classes that generate the menu of the Messages subsystem.
"""

from conf import BASEPATH
from nav.web import shouldShow

class MenuItem:

    def __init__(self,link,text,this=""):
        self.link = BASEPATH+link
        self.text = text
        if this == link:
            self.this = 1
        else:
            self.this = 0

class Menu:

    def __init__(self):
        self.contents = []

    def append(self,element):
        self.contents.append(element)

    def getMenu(self, user, this):
        """shows the menu. #some elements are access restricted"""
        menu = []
        menu.append(MenuItem("active","Active messages",this))
        menu.append(MenuItem("planned","Planned messages",this))
        menu.append(MenuItem("historic","Historic messages",this))

        menu.append(MenuItem("maintenance","Maintenance list"))
        if shouldShow(BASEPATH+'edit',user):
            menu.append(MenuItem("edit","New message",this))
            menu.append(MenuItem("add","Maintenance",this))
        return menu
