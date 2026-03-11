from urllib.parse import urlparse, parse_qs

from nav.web.navlets import Navlet


class TestAddBustParamToUrl:
    def test_when_url_has_no_query_params_then_it_should_use_question_mark(self):
        result = Navlet.add_bust_param_to_url('http://example.com/image.jpg')
        assert '?bust=' in result

    def test_when_url_has_existing_query_params_then_it_should_preserve_them(self):
        result = Navlet.add_bust_param_to_url(
            'http://example.com/graph?target=foo&filter=a&filter=b&simple'
        )
        parsed = urlparse(result)
        params = parse_qs(parsed.query, keep_blank_values=True)
        assert params['target'] == ['foo']
        assert sorted(params['filter']) == ['a', 'b']
        assert params['simple'] == ['']
        assert 'bust' in params

    def test_when_url_has_fragment_then_bust_should_be_in_query_not_fragment(self):
        result = Navlet.add_bust_param_to_url('http://example.com/image.jpg#section')
        parsed = urlparse(result)
        assert 'bust' in parse_qs(parsed.query)
        assert parsed.fragment == 'section'

    def test_when_url_has_params_and_fragment_then_bust_should_be_in_query(self):
        result = Navlet.add_bust_param_to_url(
            'http://example.com/graph?target=foo#section'
        )
        parsed = urlparse(result)
        params = parse_qs(parsed.query)
        assert 'target' in params
        assert 'bust' in params
        assert parsed.fragment == 'section'
