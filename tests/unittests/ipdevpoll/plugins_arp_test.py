from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.arp import ipv6_address_in_mappings, Arp

def test_none_in_mappings_should_not_raise():
    mappings = [(None, None, None)]
    assert not ipv6_address_in_mappings(mappings)

def test_make_new_mappings_should_not_raise_on_empty_ip():
    a = Arp(None, None, ContainerRepository())
    mappings = [(None, '00:0b:ad:c0:ff:ee')]
    a._make_new_mappings(mappings)
