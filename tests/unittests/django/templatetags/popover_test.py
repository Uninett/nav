"""Tests for popover template tags"""

import pytest
from django.template import Context, Template, TemplateSyntaxError

from nav.django.templatetags.popover import confirm_popover


class TestConfirmPopover:
    """Tests for the confirm_popover inclusion tag"""

    def test_when_minimal_params_then_it_should_render_correctly(self):
        template = Template(
            '{% load popover %}'
            '{% confirm_popover popover_id="test-id" action_url="/delete/" %}'
        )
        rendered = template.render(Context({}))

        # Basic structure
        assert 'id="test-id"' in rendered
        assert 'class="popover with-arrow"' in rendered
        assert 'action="/delete/"' in rendered
        assert 'data-popover-target="#test-id"' in rendered
        # ARIA attributes
        assert 'aria-haspopup="true"' in rendered
        assert 'aria-expanded="false"' in rendered
        # Default values
        assert 'Are you sure?' in rendered
        assert '>Yes</button>' in rendered
        assert '>No</button>' in rendered
        assert 'fa-times-circle' in rendered
        assert 'popover-content tiny' in rendered

    def test_when_custom_title_then_it_should_render_title(self):
        template = Template(
            '{% load popover %}'
            '{% confirm_popover popover_id="test-id" action_url="/delete/" '
            'title="Delete this?" %}'
        )
        rendered = template.render(Context({}))

        assert 'Delete this?' in rendered

    def test_when_custom_button_text_then_it_should_render_button_text(self):
        template = Template(
            '{% load popover %}'
            '{% confirm_popover popover_id="test-id" action_url="/delete/" '
            'confirm_text="Confirm" cancel_text="Abort" %}'
        )
        rendered = template.render(Context({}))

        assert '>Confirm</button>' in rendered
        assert '>Abort</button>' in rendered

    def test_when_trigger_text_then_it_should_pass_trigger_text_to_context(self):
        result = confirm_popover(
            context={},
            popover_id="test-id",
            action_url="/delete/",
            trigger_text="Delete",
            trigger_icon="",
        )

        assert result['trigger_text'] == "Delete"
        assert result['trigger_icon'] == ""
        assert result['trigger_classes'] == "secondary"

    @pytest.mark.parametrize(
        "param,value,expected",
        [
            ("align", "end", 'data-align="end"'),
            ("side", "top", 'data-side="top"'),
            ("size", "medium", "popover-content medium"),
        ],
    )
    def test_when_param_set_then_it_should_render_in_output(
        self, param, value, expected
    ):
        template = Template(
            '{% load popover %}'
            '{% confirm_popover popover_id="test-id" action_url="/delete/" '
            f'{param}="{value}" %}}'
        )
        rendered = template.render(Context({}))

        assert expected in rendered

    def test_when_variable_id_then_it_should_resolve_variable(self):
        template = Template(
            '{% load popover %}'
            '{% confirm_popover popover_id=item_id action_url=delete_url %}'
        )
        rendered = template.render(
            Context({'item_id': 'dynamic-123', 'delete_url': '/items/123/delete/'})
        )

        assert 'id="dynamic-123"' in rendered
        assert 'action="/items/123/delete/"' in rendered


class TestPopoverCloseButton:
    """Tests for the popover_close_button inclusion tag"""

    def test_when_minimal_params_then_it_should_render_defaults(self):
        template = Template('{% load popover %}{% popover_close_button %}')
        rendered = template.render(Context({}))

        assert '>Cancel</button>' in rendered
        assert 'secondary' in rendered
        assert 'data-close-popover' in rendered

    def test_when_custom_text_then_it_should_render_text(self):
        template = Template('{% load popover %}{% popover_close_button "Dismiss" %}')
        rendered = template.render(Context({}))

        assert '>Dismiss</button>' in rendered

    def test_when_custom_classes_then_it_should_include_classes(self):
        template = Template(
            '{% load popover %}{% popover_close_button "Close" classes="alert" %}'
        )
        rendered = template.render(Context({}))

        assert 'alert' in rendered


class TestPopoverBlockTag:
    """Tests for the {% popover %}...{% endpopover %} block tag"""

    def test_when_basic_usage_then_it_should_render_correctly(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text="About" %}'
            '<p>Content here</p>'
            '{% endpopover %}'
        )
        rendered = template.render(Context({}))

        # Basic structure
        assert 'id="info"' in rendered
        assert 'class="popover with-arrow"' in rendered
        assert '<p>Content here</p>' in rendered
        assert '>About</button>' in rendered
        # ARIA attributes
        assert 'aria-haspopup="true"' in rendered
        assert 'aria-expanded="false"' in rendered

    def test_when_trigger_element_a_then_it_should_render_anchor(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text="About" trigger_element="a" %}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(Context({}))

        assert '<a ' in rendered
        assert 'href' not in rendered  # No href to avoid scroll-to-top
        assert '>About</a>' in rendered

    def test_when_title_then_it_should_render_header(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text="About" title="Information" %}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(Context({}))

        assert '<h5>Information</h5>' in rendered

    def test_when_no_arrow_then_it_should_not_have_arrow_class(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text="About" with_arrow=False %}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(Context({}))

        assert 'with-arrow' not in rendered

    @pytest.mark.parametrize(
        "params,expected",
        [
            ('size="medium"', "popover-content medium"),
            ('side="right"', 'data-side="right"'),
            ('align="end"', 'data-align="end"'),
        ],
    )
    def test_when_param_set_then_it_should_render_in_output(self, params, expected):
        template = Template(
            '{% load popover %}'
            f'{{% popover popover_id="info" trigger_text="About" {params} %}}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(Context({}))

        assert expected in rendered

    def test_when_variable_params_then_it_should_resolve_variables(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id=popover_id trigger_text=link_text title=header %}'
            '<p>{{ body }}</p>'
            '{% endpopover %}'
        )
        rendered = template.render(
            Context(
                {
                    'popover_id': 'dynamic-info',
                    'link_text': 'Click here',
                    'header': 'Dynamic Title',
                    'body': 'Dynamic content',
                }
            )
        )

        assert 'id="dynamic-info"' in rendered
        assert '>Click here</button>' in rendered
        assert '<h5>Dynamic Title</h5>' in rendered
        assert '<p>Dynamic content</p>' in rendered

    def test_when_missing_popover_id_then_it_should_raise_error(self):
        with pytest.raises(TemplateSyntaxError) as exc_info:
            Template(
                '{% load popover %}'
                '{% popover trigger_text="About" %}'
                '<p>Content</p>'
                '{% endpopover %}'
            )
        assert "requires 'popover_id' argument" in str(exc_info.value)

    def test_when_missing_trigger_text_then_it_should_raise_error(self):
        with pytest.raises(TemplateSyntaxError) as exc_info:
            Template(
                '{% load popover %}'
                '{% popover popover_id="info" %}'
                '<p>Content</p>'
                '{% endpopover %}'
            )
        assert "requires 'trigger_text' argument" in str(exc_info.value)

    def test_when_trigger_text_contains_html_then_it_should_escape(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text=malicious_text %}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(
            Context({'malicious_text': '<script>alert("XSS")</script>'})
        )

        assert '<script>' not in rendered
        assert '&lt;script&gt;' in rendered

    def test_when_title_contains_html_then_it_should_escape(self):
        template = Template(
            '{% load popover %}'
            '{% popover popover_id="info" trigger_text="About" title=malicious_title %}'
            '<p>Content</p>'
            '{% endpopover %}'
        )
        rendered = template.render(
            Context({'malicious_title': '<img onerror="alert(1)">'})
        )

        assert '<img onerror' not in rendered
        assert '&lt;img onerror' in rendered

    def test_when_invalid_trigger_element_then_it_should_raise_error(self):
        with pytest.raises(TemplateSyntaxError) as exc_info:
            Template(
                '{% load popover %}'
                '{% popover popover_id="info" trigger_text="X" '
                'trigger_element="div" %}'
                '<p>Content</p>'
                '{% endpopover %}'
            )
        assert "trigger_element must be one of" in str(exc_info.value)
        assert "'div'" in str(exc_info.value)

    def test_when_invalid_side_then_it_should_raise_error(self):
        with pytest.raises(TemplateSyntaxError) as exc_info:
            Template(
                '{% load popover %}'
                '{% popover popover_id="info" trigger_text="About" side="center" %}'
                '<p>Content</p>'
                '{% endpopover %}'
            )
        assert "side must be one of" in str(exc_info.value)
        assert "'center'" in str(exc_info.value)

    def test_when_invalid_align_then_it_should_raise_error(self):
        with pytest.raises(TemplateSyntaxError) as exc_info:
            Template(
                '{% load popover %}'
                '{% popover popover_id="info" trigger_text="About" align="middle" %}'
                '<p>Content</p>'
                '{% endpopover %}'
            )
        assert "align must be one of" in str(exc_info.value)
        assert "'middle'" in str(exc_info.value)
