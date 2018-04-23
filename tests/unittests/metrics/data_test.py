import pytest
from mock import patch
from io import BytesIO

from nav.metrics.errors import GraphiteUnreachableError
from nav.metrics.data import get_metric_data


def test_get_metric_data_without_target_should_return_empty_list():
    assert get_metric_data(None) == []


def test_get_metric_data_with_no_graphite_server_should_fail():
    target = "nav.devices.example-sw_example_org.ports.1.ifInOctets"
    with patch('nav.metrics.data.CONFIG') as config:
        config.get.return_value = 'http://localhost:65042/'
        with pytest.raises(GraphiteUnreachableError):
            get_metric_data(target)


def test_get_metric_data_can_parse_response():
    target = "nav.devices.example-sw_example_org.ports.1.ifInOctets"
    with patch('nav.metrics.data.urlopen') as urlopen:
        urlopen.return_value = BytesIO(b'[1]')
        assert get_metric_data(target) == [1]
