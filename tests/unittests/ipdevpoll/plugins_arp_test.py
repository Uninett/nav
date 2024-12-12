from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_twisted

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
