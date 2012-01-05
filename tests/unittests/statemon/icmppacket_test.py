from nav.statemon.icmppacket import PacketV4

def test_pid_over_32767_should_not_raise_error():
    p = PacketV4(32768, 'payload')
    p.construct()
