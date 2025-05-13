from unittest import TestCase

from nav.Snmp import safestring


class EncodingTests(TestCase):
    def test_latin1_encoded_ifalias_should_be_properly_decoded(self):
        result = safestring(b'A m\xf8\xf8se once bit my sister')
        expected = 'A m\xf8\xf8se once bit my sister'
        self.assertEqual(result, expected)

    def test_utf_8_encoded_ifalias_should_be_properly_decoded(self):
        result = safestring(b'A m\xc3\xb8\xc3\xb8se once bit my sister')
        expected = 'A m\xf8\xf8se once bit my sister'
        self.assertEqual(result, expected)

    def test_none_should_be_returned_unchanged(self):
        result = safestring(None)
        self.assertTrue(result is None)

    def test_unknown_encoding_should_not_raise_error(self):
        result = safestring(b'A m\x9b\x9bse once bit my sister')
        self.assertTrue(isinstance(result, str))

    def test_number_should_be_encoded(self):
        result = safestring(42)
        self.assertEqual(result, "42")
