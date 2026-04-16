"""Tests for NAV's custom date format module"""

import datetime

from django.template import Context, Template
from django.utils.formats import get_format

SAMPLE_DATETIME = datetime.datetime(2026, 3, 20, 14, 5, 9)


class TestDateFormatSpecifiers:
    """Verify NAV's custom format module provides ISO format specifiers"""

    def test_when_l10n_active_datetime_format_should_be_iso(self):
        assert get_format('DATETIME_FORMAT') == 'Y-m-d H:i:s'

    def test_when_l10n_active_date_format_should_be_iso(self):
        assert get_format('DATE_FORMAT') == 'Y-m-d'

    def test_when_l10n_active_short_datetime_format_should_be_iso(self):
        assert get_format('SHORT_DATETIME_FORMAT') == 'Y-m-d H:i'

    def test_when_l10n_active_time_format_should_be_24h(self):
        assert get_format('TIME_FORMAT') == 'H:i:s'


class TestRenderedDateOutput:
    """Verify that template date filters produce ISO-formatted output"""

    def _render(self, format_name):
        template = Template('{{ val|date:"' + format_name + '" }}')
        return template.render(Context({'val': SAMPLE_DATETIME}))

    def test_when_rendering_datetime_format_should_produce_iso_string(self):
        assert self._render('DATETIME_FORMAT') == '2026-03-20 14:05:09'

    def test_when_rendering_date_format_should_produce_iso_string(self):
        assert self._render('DATE_FORMAT') == '2026-03-20'

    def test_when_rendering_short_datetime_format_should_produce_iso_string(self):
        assert self._render('SHORT_DATETIME_FORMAT') == '2026-03-20 14:05'

    def test_when_rendering_time_format_should_produce_24h_string(self):
        assert self._render('TIME_FORMAT') == '14:05:09'
