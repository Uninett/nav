from mock import Mock
import unittest
from nav.models.manage import Netbox, Room


class MetaClassTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.netbox = Mock(name='Netbox', spec=Netbox)
        self.netbox.pk = 1337
        self.netbox.id = self.netbox.pk
        self.netbox.sysname = 'fuu.example.net'
        self.netbox.category_id = 'GW'
        self.netbox.ip = '192.168.42.1'
        self.netbox.up = 'y'
        self.netbox.room = Mock(name='Room', spec=Room)
        self.netbox.room.__unicode__ = Mock(
            return_value='Galaxy (Universe Far Far away)'
        )
        self.netbox.room.id = 'Galaxy'
        self.netbox.room.location.id = 'Universe'
        self.netbox.room.location.description = 'Far far away'
