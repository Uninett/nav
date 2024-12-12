from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_twisted

from nav.ipdevpoll import shadows
from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.arp import ipv6_address_in_mappings, Arp


class TestCheckAndUpdatePrefixCache:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_when_cache_is_expired_it_should_call_update(self):
        with patch.object(Arp, "_update_prefix_cache") as update:
            Arp.prefix_cache_update_time = datetime.now() - Arp.prefix_cache_max_age * 2
            yield Arp._check_and_update_prefix_cache()
            assert update.called

    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_when_cache_is_not_expired_it_should_not_call_update(self):
        with patch.object(Arp, "_update_prefix_cache") as update:
            Arp.prefix_cache_update_time = datetime.now()
            yield Arp._check_and_update_prefix_cache()
            assert not update.called


def test_none_in_mappings_should_not_raise():
    mappings = [(None, None, None)]
    assert not ipv6_address_in_mappings(mappings)


def test_make_new_mappings_should_not_raise_on_empty_ip():
    a = Arp(None, None, ContainerRepository())
    mappings = [(None, '00:0b:ad:c0:ff:ee')]
    a._make_new_mappings(mappings)


def test_when_arp_records_exist_is_arp_already_collected_should_return_true():
    containers = ContainerRepository()
    containers.factory(('192.168.0.1', '00:co:ff:ee:ba:be'), shadows.Arp)
    plugin = Arp(None, None, containers)
    assert plugin._is_arp_already_collected()


def test_when_arp_records_do_not_exist_is_arp_already_collected_should_return_false():
    plugin = Arp(None, None, ContainerRepository())
    assert not plugin._is_arp_already_collected()
