"""Tests for AliasListField and AliasListWidget"""

import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict

from nav.django.forms import AliasListField, AliasListWidget
from nav.django.validators import MAX_ALIAS_LENGTH, validate_aliases


class TestAliasListFieldClean:
    def test_when_value_is_none_then_it_should_return_empty_list(self):
        field = AliasListField(required=False)
        assert field.clean(None) == []

    def test_when_value_is_empty_list_then_it_should_return_empty_list(self):
        field = AliasListField(required=False)
        assert field.clean([]) == []

    def test_when_value_has_strings_then_it_should_return_them(self):
        field = AliasListField(required=False)
        assert field.clean(['foo', 'bar']) == ['foo', 'bar']

    def test_when_value_has_whitespace_then_it_should_strip(self):
        field = AliasListField(required=False)
        assert field.clean(['  foo  ', ' bar ']) == ['foo', 'bar']

    def test_when_value_has_empty_strings_then_it_should_remove_them(self):
        field = AliasListField(required=False)
        assert field.clean(['foo', '', '  ', 'bar']) == ['foo', 'bar']

    def test_when_value_has_duplicates_then_it_should_deduplicate(self):
        field = AliasListField(required=False)
        assert field.clean(['foo', 'bar', 'foo']) == ['foo', 'bar']

    def test_when_value_has_non_string_then_it_should_raise_validation_error(self):
        field = AliasListField(required=False)
        with pytest.raises(ValidationError):
            field.clean([123])

    def test_when_alias_exceeds_max_length_then_it_should_raise_validation_error(self):
        field = AliasListField(required=False)
        long_alias = 'a' * (MAX_ALIAS_LENGTH + 1)
        with pytest.raises(ValidationError):
            field.clean([long_alias])

    def test_when_alias_contains_pipe_then_it_should_raise_validation_error(self):
        field = AliasListField(required=False)
        with pytest.raises(ValidationError):
            field.clean(['foo|bar'])


class TestAliasListWidgetValueFromDatadict:
    def test_when_data_has_json_then_it_should_return_list(self):
        widget = AliasListWidget()
        data = QueryDict(mutable=True)
        data['aliases_json'] = '["foo", "bar"]'
        assert widget.value_from_datadict(data, {}, 'aliases') == ['foo', 'bar']

    def test_when_data_has_no_json_then_it_should_return_empty_list(self):
        widget = AliasListWidget()
        data = QueryDict(mutable=True)
        assert widget.value_from_datadict(data, {}, 'aliases') == []

    def test_when_data_has_invalid_json_then_it_should_return_empty_list(self):
        widget = AliasListWidget()
        data = QueryDict(mutable=True)
        data['aliases_json'] = 'not valid json'
        assert widget.value_from_datadict(data, {}, 'aliases') == []

    def test_when_data_has_non_list_json_then_it_should_return_empty_list(self):
        widget = AliasListWidget()
        data = QueryDict(mutable=True)
        data['aliases_json'] = '{"key": "value"}'
        assert widget.value_from_datadict(data, {}, 'aliases') == []


class TestAliasListFieldPrepareValue:
    def test_when_value_is_list_then_it_should_return_it(self):
        field = AliasListField(required=False)
        assert field.prepare_value(['a', 'b']) == ['a', 'b']

    def test_when_value_is_json_string_then_it_should_parse(self):
        field = AliasListField(required=False)
        assert field.prepare_value('["a", "b"]') == ['a', 'b']

    def test_when_value_is_none_then_it_should_return_empty_list(self):
        field = AliasListField(required=False)
        assert field.prepare_value(None) == []


class TestValidateAliases:
    def test_when_value_is_none_then_it_should_return_empty_list(self):
        assert validate_aliases(None) == []

    def test_when_value_is_empty_list_then_it_should_return_empty_list(self):
        assert validate_aliases([]) == []

    def test_when_value_has_strings_then_it_should_return_them(self):
        assert validate_aliases(['foo', 'bar']) == ['foo', 'bar']

    def test_when_value_has_whitespace_then_it_should_strip(self):
        assert validate_aliases(['  foo  ', ' bar ']) == ['foo', 'bar']

    def test_when_value_has_empty_strings_then_it_should_remove_them(self):
        assert validate_aliases(['foo', '', '  ', 'bar']) == ['foo', 'bar']

    def test_when_value_has_duplicates_then_it_should_deduplicate(self):
        assert validate_aliases(['foo', 'bar', 'foo']) == ['foo', 'bar']

    def test_when_value_has_non_string_then_it_should_raise_validation_error(self):
        with pytest.raises(ValidationError):
            validate_aliases([123])

    def test_when_alias_exceeds_max_length_then_it_should_raise_validation_error(self):
        long_alias = 'a' * (MAX_ALIAS_LENGTH + 1)
        with pytest.raises(ValidationError):
            validate_aliases([long_alias])

    def test_when_alias_contains_pipe_then_it_should_raise_validation_error(self):
        with pytest.raises(ValidationError):
            validate_aliases(['foo|bar'])
