# mock/patch/hack/workaround: gammudispatcher normally requires gammu to be
# installed, but we're only testing functionality from the module that is not
# dependent on this. If there is no gammu module, we fake it so we can import
# gammudispather without failures.
try:
    import gammu
except ImportError:
    import sys

    gammu = sys.modules['gammu'] = type(sys)('gammu')
from nav.smsd.gammudispatcher import decode_sms_to_unicode, GammuDispatcher


class TestThat_decode_sms_to_unicode:
    def test_should_decode_ascii_bytes_to_comparable_string(self):
        sms = 'Hello'
        unicode_sms = decode_sms_to_unicode(sms)
        assert sms == unicode_sms

    def test_should_decode_string_to_comparable_string(self):
        sms = u'A m\xf8\xf8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        assert sms == unicode_sms

    def test_should_decode_utf8_string_properly(self):
        sms = b'A m\xc3\xb8\xc3\xb8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        expected = u'A m\xf8\xf8se once bit my sister'
        assert unicode_sms == expected
