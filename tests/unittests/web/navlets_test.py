from nav.web.navlets import Navlet


class TestAddBustParamToUrl:
    def test_when_url_has_no_query_params_then_it_should_use_question_mark(self):
        result = Navlet.add_bust_param_to_url('http://example.com/image.jpg')
        assert '?bust=' in result

    def test_when_url_has_existing_query_params_then_it_should_use_ampersand(self):
        result = Navlet.add_bust_param_to_url('http://example.com/graph?target=foo')
        assert '&bust=' in result
        assert result.startswith('http://example.com/graph?target=foo&bust=')
