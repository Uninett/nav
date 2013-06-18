import unittest
from nav.web.info.vlan.views import rpn_sum

class TestVlan(unittest.TestCase):
    """Testcases for the info/vlan view functions"""

    def test_sumrpn_single_ds(self):
        vnames = ['id_1']
        self.assertEqual(rpn_sum(vnames), 'id_1')

    def test_sumrpn_two_ds(self):
        vnames = ['id_1', 'id_2']
        self.assertEqual(rpn_sum(vnames), 'id_1,id_2,+')

    def test_sunrpn_three_ds(self):
        vnames = ['id_1', 'id_2', 'id_3']
        self.assertEqual(rpn_sum(vnames), 'id_1,id_2,+,id_3,+')

    def test_sunrpn_five_ds(self):
        vnames = ['a','b','c','d','e']
        self.assertEqual(rpn_sum(vnames), 'a,b,+,c,+,d,+,e,+')

