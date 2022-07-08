from mock import patch
import pytest

from nav.metrics.graphs import extract_series_name, translate_serieslist_to_regex
from nav.metrics.graphs import get_sensor_meta
from nav.models.manage import Sensor


def test_get_sensor_meta_should_not_crash_on_missing_human_readable():
    sensor = Sensor(human_readable=None)

    with patch('nav.metrics.lookup.lookup') as lookup:
        lookup.return_value = sensor
        meta = get_sensor_meta('bogus')
        assert meta, "result is empty"


series_name_data = (
    (
        'scaleToSeconds(nonNegativeDerivative(scale(nav.devices.example-sw_example_org.ports.Po3.ifOutOctets,8)),1)',
        'nav.devices.example-sw_example_org.ports.Po3.ifOutOctets',
    ),
    ('scale(nav.something.*.{in,out}data, 8)', 'nav.something.*.{in,out}data'),
)


@pytest.mark.parametrize("series, expected", series_name_data)
def test_extract_series_name(series, expected):
    assert extract_series_name(series) == expected


translate_data = (
    ('plain.jane', ['plain.jane'], ['plain.joe']),
    (
        'far.out.in.the.*.western.spiral.{arm,leg}',
        [
            'far.out.in.the.uncharted.western.spiral.arm',
            'far.out.in.the.charted.western.spiral.leg',
        ],
        ['far.out.in.the.forgotten.western.spiral.neck'],
    ),
    ('one.two.thre?', ['one.two.three', 'one.two.threx'], ['one.two.throws']),
)


@pytest.mark.parametrize("series,matches,nonmatches", translate_data)
def test_translate_serieslist_to_regex(series, matches, nonmatches):
    pattern = translate_serieslist_to_regex(series)
    for string in matches:
        assert pattern.match(string), "%s doesn't match %s" % (string, series)

    for string in nonmatches:
        assert not pattern.match(string), "%s matches %s" % (string, series)
