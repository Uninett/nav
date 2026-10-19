import unittest

from django.template import engines

from nav.django.templatetags.string_manipulation import deep_urlize


class DeepUrlizeTest(unittest.TestCase):
    def test_deep_urlize_noturl(self):
        for noturl in (None, '', 'blbl', 'a2'):
            durl = deep_urlize(noturl)
            self.assertEqual(durl, noturl)

    def test_deep_urlize_correct_url(self):
        teststr = 'https://x:y@www.vg.no/x-4312432;a=b?q=a#foo'
        durl = deep_urlize(teststr)
        self.assertEqual(durl, '<a href="{}">{}</a>'.format(teststr, teststr))

    def test_when_text_has_markup_then_it_should_escape_it(self):
        self.assertEqual(deep_urlize("<b>bold</b>"), "&lt;b&gt;bold&lt;/b&gt;")

    def test_when_url_is_surrounded_by_markup_then_it_should_link_only_the_url(
        self,
    ):
        self.assertEqual(
            deep_urlize("<i>see https://example.org/</i>"),
            '&lt;i&gt;see <a href="https://example.org/">https://example.org/</a>'
            "&lt;/i&gt;",
        )

    def test_when_url_contains_a_quote_then_it_should_not_break_out_of_href(self):
        self.assertEqual(
            deep_urlize('http://x/"onclick="alert(1)'),
            '<a href="http://x/">http://x/</a>&quot;onclick=&quot;alert(1)',
        )

    def test_when_autoescape_is_off_then_it_should_leave_text_unescaped(self):
        self.assertEqual(deep_urlize("<b>bold</b>", autoescape=False), "<b>bold</b>")

    def test_when_url_has_an_ampersand_then_it_should_escape_it_in_the_link(self):
        self.assertEqual(
            deep_urlize("https://a/?x=1&y=2"),
            '<a href="https://a/?x=1&amp;y=2">https://a/?x=1&amp;y=2</a>',
        )

    def test_when_rendered_in_a_template_then_it_should_not_be_escaped_again(self):
        template = engines["django"].from_string(
            "{% load string_manipulation %}{{ value|deep_urlize }}"
        )
        self.assertEqual(
            template.render({"value": "<b> https://a/"}),
            '&lt;b&gt; <a href="https://a/">https://a/</a>',
        )
