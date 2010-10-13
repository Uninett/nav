from unittest import TestCase
from nav.smsd.gammudispatcher import decode_sms_to_unicode

class EncodingTests(TestCase):
    def test_ascii_string_should_decode_to_equal_object(self):
        sms = 'Hello'
        unicode_sms = decode_sms_to_unicode(sms)
        self.assertEquals(sms, unicode_sms)

    def test_unicode_object_should_be_decoded_to_equal_object(self):
        sms = u'A m\xf8\xf8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        self.assertEquals(sms, unicode_sms)

    def test_utf_8_string_should_properly_decode(self):
        sms = 'A m\xc3\xb8\xc3\xb8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        expected = u'A m\xf8\xf8se once bit my sister'
        self.assertEquals( unicode_sms, expected)
