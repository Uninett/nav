import pytest
from nav.django.validators import (
    is_valid_point_string,
    validate_hstore,
    ValidationError,
)


class TestValidPointString(object):
    def test_valid_point_string(self):
        point_string = "(2.3,4.5)"
        assert is_valid_point_string(point_string)

    def test_valid_point_parens_and_sapce(self):
        point_string = "(9.888, 3.2222)"
        assert is_valid_point_string(point_string)

    def test_valid_point_no_parens(self):
        point_string = "5.5,8.7"
        assert is_valid_point_string(point_string)

    def test_valid_point_no_parens_and_space(self):
        point_string = "77.22134124, 543.3342"
        assert is_valid_point_string(point_string)

    def test_valid_point_no_comma(self):
        point_string = "(2.4)"
        assert not is_valid_point_string(point_string)

    def test_valid_point_chars(self):
        point_string = "foo, bar"
        assert not is_valid_point_string(point_string)


class TestValidHStoreField(object):
    def test_empty_hstore_field(self):
        inputs = ('', None, {})
        for input in inputs:
            result = validate_hstore(input)
            assert result == {}

    def test_non_dict(self):
        inputs = ((), [], 0)
        for input in inputs:
            with pytest.raises(ValidationError):
                validate_hstore(input)

    def test_bytes_json(self):
        input = b'{"a": "b"}'
        result = validate_hstore(input)
        assert result == {'a': 'b'}

    def test_good_json(self):
        input = '{"a": "b"}'
        result = validate_hstore(input)
        assert result == {'a': 'b'}
