from mock import patch

from nav.metrics.graphs import get_sensor_meta
from nav.models.manage import Sensor


def test_get_sensor_meta_should_not_crash_on_missing_human_readable():
    sensor = Sensor(human_readable=None)

    with patch('nav.metrics.lookup.lookup') as lookup:
        lookup.return_value = sensor
        meta = get_sensor_meta('bogus')
        assert meta, "result is empty"
