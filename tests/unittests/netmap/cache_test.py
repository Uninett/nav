"""Tests for netmap cache utilities"""

from unittest.mock import patch

from nav.web.netmap.cache import (
    _safe_cache_set,
    cache_topology,
    cache_traffic,
)


class TestSafeCacheSet:
    def test_when_cache_set_succeeds_it_should_call_cache_set(self):
        with patch('nav.web.netmap.cache.cache') as mock_cache:
            _safe_cache_set('key', 'value', 60)
            mock_cache.set.assert_called_once_with('key', 'value', 60)

    def test_when_cache_set_raises_it_should_log_warning_not_raise(self):
        with patch('nav.web.netmap.cache.cache') as mock_cache:
            mock_cache.set.side_effect = Exception('object too large for cache')
            with patch('nav.web.netmap.cache._logger') as mock_logger:
                _safe_cache_set('key', 'value', 60)
                mock_logger.warning.assert_called_once()


class TestCacheTopology:
    def test_when_cache_set_fails_it_should_still_return_result(self):
        with patch('nav.web.netmap.cache.cache') as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.side_effect = Exception('object too large for cache')

            @cache_topology("layer 2")
            def my_func(view=None):
                return {'nodes': {}, 'links': []}

            result = my_func(view=None)
            assert result == {'nodes': {}, 'links': []}

    def test_when_cached_data_exists_it_should_return_cached_data(self):
        cached_data = {'nodes': {'a': 1}, 'links': []}
        with patch('nav.web.netmap.cache.cache') as mock_cache:
            mock_cache.get.return_value = cached_data

            @cache_topology("layer 2")
            def my_func(view=None):
                return {'nodes': {}, 'links': []}

            result = my_func(view=None)
            assert result == cached_data


class TestCacheTraffic:
    def test_when_cache_set_fails_it_should_still_return_result(self):
        with patch('nav.web.netmap.cache.cache') as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.side_effect = Exception('object too large for cache')

            @cache_traffic("layer 2")
            def my_func(location_or_room_id):
                return [{'source': 1, 'target': 2}]

            result = my_func(None)
            assert result == [{'source': 1, 'target': 2}]
