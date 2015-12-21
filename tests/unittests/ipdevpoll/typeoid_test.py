from nav.ipdevpoll.plugins import typeoid


def test_make_new_vendor_id_has_reasonable_response():
    sysobjectid = '1.3.6.1.4.1.11.2.3.7.11.51'
    assert typeoid.make_new_vendor_id(sysobjectid) == 'hewlettpackard'
