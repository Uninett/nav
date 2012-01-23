from unittest import TestCase
from minimock import Mock

from nav.ipdevpoll.plugins.ciscosup import find_supervisor

class SupervisorSearchTests(TestCase):

    def test_should_find_6509_supervisor(self):
        supervisor = _mod("WS-SUP720-3B 2 ports Supervisor Engine 720 Rev. 5.6")
        daughter = _mod("WS-SUP720 MSFC3 Daughterboard Rev. 3.1")

        modules = [
            _mod("WS-X6148A-GE-TX 48-port 10/100/1000 RJ45 EtherModule Rev. 1.6"),
            _mod("WS-X6148A-GE-TX 48-port 10/100/1000 RJ45 EtherModule Rev. 1.6"),
            supervisor,
            _mod("WS-X6724-SFP CEF720 24 port 1000mb SFP Rev. 3.1"),
            _mod("OSR-7600 Clock FRU 2"),
            daughter,
            _mod("SFP Transceiver 1000BaseSX Gi3/21"),
            ]

        self.assertTrue(find_supervisor(modules) is supervisor)


    def test_should_find_4506_supervisor(self):
        supervisor = _mod("Sup 7-E 10GE (SFP+), 1000BaseX (SFP) with 4 SFP+ Ports")
        modules = [
            _mod("10GE SFP+ with 12 SFP+ ports"),
            _mod("HP J4878B XL mini-GBIC module"),
            _mod("HP J4878A XL mini-GBIC module"),
            _mod("HP J4820A XL 10/100-TX module"),
            supervisor,
            _mod("10/100/1000BaseT (RJ45)+V E Series with 48 10/100/1000 baseT Premium PoE ports (Cisco/IEEE)"),
            ]

        self.assertTrue(find_supervisor(modules) is supervisor)

    def test_should_return_none_when_no_supervisor(self):
        modules = [
            _mod("WS-X6724-SFP CEF720 24 port 1000mb SFP Rev. 3.1"),
            _mod("OSR-7600 Clock FRU 2"),
            ]
        self.assertTrue(find_supervisor(modules) is None)

    def test_should_return_none_on_empty_module_list(self):
        self.assertTrue(find_supervisor([]) is None)


def _mod(description):
    return Mock('Module', description=description)
