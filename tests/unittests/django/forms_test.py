from unittest import TestCase
import json

from nav.django.forms import JSONWidget


class JSONWidgetTest(TestCase):
    def test_render_empty_value(self):
        widget = JSONWidget()
        expected = ''
        value = ''
        result = widget._render_value(value)
        self.assertEqual(result, expected)
        value = None
        result = widget._render_value(value)
        self.assertEqual(result, expected)
        value = {}
        result = widget._render_value(value)
        self.assertEqual(result, expected)

    def test_render_good_value(self):
        widget = JSONWidget()
        value = {'a': b'a'}
        expected = {'a': 'a'}
        result = widget._render_value(value)
        from_json = json.loads(result)
        self.assertEqual(expected, from_json)
        value = [1, None, b'q', 'foo']
        expected = [1, None, 'q', 'foo']
        result = widget._render_value(value)
        from_json = json.loads(result)
        self.assertEqual(expected, from_json)
