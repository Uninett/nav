# -*- coding: utf-8 -*-
from nav.web.ipdevinfo.utils import get_interface_counter_graph_url
from mock import Mock


def test_get_interface_counter_graph_url_should_handle_utf8():
    ifc = Mock()
    ifc.netbox.sysname = u"example-sw.example.org"
    ifc.ifname = u"Ethernet1/1"
    ifc.ifalias = u"æøå"
    assert get_interface_counter_graph_url(ifc) != ""
