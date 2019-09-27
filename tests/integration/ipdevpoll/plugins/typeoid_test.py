from nav.ipdevpoll.plugins import typeoid
from nav.models import manage


def test_get_vendor_should_return_expected_vendor():
    sysobjectid = "1.3.6.1.4.1.11.2.3.7.11.51"
    result = typeoid.TypeOid._get_vendor(sysobjectid)
    assert isinstance(result, manage.Vendor)
    assert result.id == "hp"


def test_make_new_vendor_should_return_expected_vendor_object():
    sysobjectid = "1.3.6.1.4.1.11.2.3.7.11.51"
    result = typeoid.TypeOid._make_new_vendor(sysobjectid)
    assert isinstance(result, manage.Vendor)
    assert result.id == "hewlettpackard"
