from __future__ import unicode_literals

import unittest

from nav.django.templatetags.string_manipulation import deep_urlize


class DeepUrlizeTest(unittest.TestCase):

    def test_deep_urlize_noturl(self):
        for noturl in (None, u'', u'blbl', u'a2'):
            durl = deep_urlize(noturl)
            self.assertEqual(durl, noturl)

    def test_deep_urlize_correct_url(self):
        teststr = u'https://x:y@www.vg.no/x-4312432;a=b?q=a#foo'
        durl = deep_urlize(teststr)
        self.assertEqual(durl, u'<a href="{}">{}</a>'.format(teststr, teststr))
