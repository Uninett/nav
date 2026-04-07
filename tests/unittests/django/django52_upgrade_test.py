"""Tests to verify the custom format module produces expected output."""

from datetime import datetime

import pytest
from django.template import Context, Template


class TestDateTimeFormatting:
    """Verify that the custom format module in nav.django.formats.en
    makes bare |date and |time filters produce ISO-style output."""

    @pytest.fixture()
    def sample_datetime(self):
        return datetime(2026, 3, 15, 14, 30, 45)

    def test_when_bare_date_filter_then_it_should_render_iso_date(
        self, sample_datetime
    ):
        template = Template('{{ value|date }}')
        rendered = template.render(Context({'value': sample_datetime}))
        assert rendered == '2026-03-15'

    def test_when_bare_time_filter_then_it_should_render_hms(self, sample_datetime):
        template = Template('{{ value|time }}')
        rendered = template.render(Context({'value': sample_datetime}))
        assert rendered == '14:30:45'

    def test_when_date_filter_on_none_with_default_then_it_should_show_default(self):
        template = Template('{{ value|date|default:"N/A" }}')
        rendered = template.render(Context({'value': None}))
        assert rendered == 'N/A'
