from unittest import TestCase

from nav.snmptrapd.agent_se import TrapListener

class TrapListenerTest(TestCase):
    def test_v1_wxgoose_trap_agent_is_decoded_correctly(self):
        """Encodes 10.0.0.42 as the trap agent of an SNMPv1 trap message and
        verifies that this is the decoded trap agent address.

        """
        trap_packet = "0\x81\x8e\x02\x01\x00\x04\x06public\xa4\x81\x80\x06\x08+\x06\x01\x04\x01\x81\x87]@\x04\n\x00\x00*\x02\x01\x06\x02\x02'\xddC\x04$\x02\xf8@0a0\x12\x06\r+\x06\x01\x04\x01\x81\x87]\x02\x02\x01\x05\x01\x02\x01\x1f0 \x06\r+\x06\x01\x04\x01\x81\x87]\x02\x02\x01\x03\x01\x04\x0fClimate Monitor0\x17\x06\x0b+\x06\x01\x04\x01\x81\x87]\x02\x01\x03\x04\x08WxGoos-10\x10\x06\x0b+\x06\x01\x04\x01\x81\x87]\x02\x01\x06\x02\x01\x01"
        listener = DisabledTrapListener()
        source = ('192.168.1.10', 31252)
        trap = listener._decode(trap_packet, source)

        self.assertEquals(trap.agent, '10.0.0.42')

    def test_v2_wxgoose_trap_agent_is_set_correctly(self):
        trap_packet = '0\x81\x83\x02\x01\x01\x04\x06public\xa7v\x02\x02\x01\xf0\x02\x01\x00\x02\x01\x000j0\x12\x06\r+\x06\x01\x04\x01\x81\x87]\x03\x02\x01\x05\x01\x02\x01\x170 \x06\r+\x06\x01\x04\x01\x81\x87]\x03\x02\x01\x03\x01\x04\x0fWeatherGoose II0\x1f\x06\x0c+\x06\x01\x04\x01\x81\x87]\x03\x01\x03\x00\x04\x0fWeatherGoose II0\x11\x06\x0c+\x06\x01\x04\x01\x81\x87]\x03\x01\x06\x00\x02\x01\x02'
        listener = DisabledTrapListener()
        source = ('10.0.0.42', 31252)
        trap = listener._decode(trap_packet, source)

        self.assertEquals(trap.agent, '10.0.0.42')


class DisabledTrapListener(TrapListener):
    def __init__(self):
        pass
