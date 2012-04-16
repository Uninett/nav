from nav.ipdevpoll.shadows.adjacency import UnrecognizedNeighbor

def test_nonascii_remote_name_should_be_changed():
    remote_name = 'a\x9enon-ascii'
    u = UnrecognizedNeighbor()
    u.remote_name = remote_name
    u.prepare()
    assert u.remote_name != remote_name

def test_nonascii_remote_id_should_be_changed():
    remote_id = 'a\x9enon-ascii'
    u = UnrecognizedNeighbor()
    u.remote_id = remote_id
    u.prepare()
    assert u.remote_id != remote_id
