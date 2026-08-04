"""Unit tests for nav.db helper functions."""

from nav.db import escape


class TestEscape:
    def test_it_should_quote_a_plain_string_as_an_sql_literal(self):
        assert escape("6 months") == "'6 months'"

    def test_it_should_double_embedded_single_quotes(self):
        assert escape("o'brien") == "'o''brien'"

    def test_it_should_return_a_str(self):
        assert isinstance(escape("foo"), str)
