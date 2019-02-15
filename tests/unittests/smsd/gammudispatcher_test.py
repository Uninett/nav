from unittest import TestCase
# mock/patch/hack/workaround: gammudispatcher normally requires gammu to be
# installed, but we're only testing functionality from the module that is not
# dependent on this. If there is no gammu module, we fake it so we can import
# gammudispather without failures.
try:
    import gammu
except ImportError:
    import sys
    gammu = sys.modules['gammu'] = type(sys)('gammu')
from nav.smsd.gammudispatcher import decode_sms_to_unicode


class EncodingTests(TestCase):
    def test_ascii_string_should_decode_to_equal_object(self):
        sms = 'Hello'
        unicode_sms = decode_sms_to_unicode(sms)
        self.assertEqual(sms, unicode_sms)

    def test_unicode_object_should_be_decoded_to_equal_object(self):
        sms = u'A m\xf8\xf8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        self.assertEqual(sms, unicode_sms)

    def test_utf_8_string_should_properly_decode(self):
        sms = b'A m\xc3\xb8\xc3\xb8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        expected = u'A m\xf8\xf8se once bit my sister'
        self.assertEqual( unicode_sms, expected)
