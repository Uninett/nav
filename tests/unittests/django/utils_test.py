from nav.django.utils import get_verbose_name


def test_verbose_name():
    """Test that get_verbose_name() works on all supported Django versions"""
    from nav.models.manage import Netbox
    name = get_verbose_name(Netbox, 'type__name')
    assert name == 'type name'
