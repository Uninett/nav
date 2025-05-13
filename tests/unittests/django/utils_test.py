# -*- coding: utf-8 -*-
from nav.django.utils import get_verbose_name, reverse_with_query


def test_verbose_name():
    """Test that get_verbose_name() works on all supported Django versions"""
    from nav.models.manage import Netbox

    name = get_verbose_name(Netbox, 'type__name')
    assert name == 'type name'


def test_reverse_with_query_should_work_with_unicode():
    """Reveals issues with PY2/PY3 co-compatibility"""
    assert reverse_with_query("maintenance-new", roomid="bø-123")
