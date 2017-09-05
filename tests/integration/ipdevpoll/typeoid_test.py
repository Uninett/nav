from django.utils import six

from nav.ipdevpoll.plugins import typeoid


# Mainly here to ensure the SQL statement is valid
def test_get_vendorid_has_reasonable_response():
    sysobjectid = '1.3.6.1.4.1.11.2.3.7.11.51'
    assert isinstance(typeoid.get_vendor_id(sysobjectid), six.string_types)
