"""Tests for the port_info template tags."""

from django.template import Context, Template

from nav.django.templatetags.port_info import topology_relation_label


class TestTopologyRelationLabel:
    def test_when_relation_is_lag_then_it_should_name_the_link_aggregate(self):
        assert topology_relation_label("lag") == "Member of link aggregate (LAG)"

    def test_when_relation_is_stack_then_it_should_name_ifstack_layering(self):
        assert topology_relation_label("stack") == "Layered below (ifStack)"

    def test_when_relation_is_both_then_it_should_name_both_relations(self):
        assert topology_relation_label("both") == "Bundled and layered (LAG + ifStack)"

    def test_when_relation_is_none_then_it_should_return_empty_string(self):
        assert topology_relation_label(None) == ""

    def test_when_relation_is_unknown_then_it_should_return_empty_string(self):
        assert topology_relation_label("frobnicate") == ""

    def test_when_loaded_in_a_template_then_the_filter_should_be_registered(self):
        template = Template("{% load port_info %}{{ rel|topology_relation_label }}")
        rendered = template.render(Context({"rel": "stack"}))
        assert rendered == "Layered below (ifStack)"
