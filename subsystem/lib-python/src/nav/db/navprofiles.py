import nav.db
from nav.db.forgotten.navprofiles import *

class Account(nav.db.forgotten.navprofiles.Account):
    def getGroups(self):
        links = self.getChildren(Accountingroup)
        return [Accountgroup(link.group) for link in links]

def _customizeTables():
    nav.db.forgotten.navprofiles._Wrapper.cursor = nav.db.cursor
    nav.db.forgotten.navprofiles._Wrapper._dbModule = nav.db.driver



##### Initialization #####

_customizeTables()
