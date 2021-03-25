import unittest
from nav.models.manage import Netbox, Interface, Room, Location, Category


class TopologyTestCase(unittest.TestCase):
    def setUp(self):
        self.room = room = Room()
        room.id = 'Pegasus'
        room.description = 'room description'
        room.location = Location()
        room.location.id = 'galaxy'
        room.location.description = 'In a galaxy far far away'

        self.category_gw = Category(id='GW')

    def _next_id(self):
        self.model_id = self.model_id + 1
        return self.model_id

    def _netbox_factory(self, sysname, interface=None):
        netbox = Netbox()
        netbox.id = self._next_id()
        netbox.sysname = sysname
        netbox.interface = interface
        netbox.category = self.category_gw
        netbox.room = self.room
        netbox.ip = '::{0}'.format(self.model_id)
        return netbox

    def _interface_factory(self, ifname, netbox):
        interface = Interface()
        interface.id = self._next_id()
        interface.ifname = ifname
        if netbox and isinstance(netbox, Netbox):
            interface.netbox = netbox
        elif netbox:
            interface.netbox = self._netbox_factory(netbox, interface)
        return interface
