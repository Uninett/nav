from django.core.exceptions import ValidationError

from nav.web.auth.password_validation import CompositionValidator


def test_init_with_no_args_builds_default_check_mapping():
    default_check_mapping = {
        'min_numeric': {
            'required': 1,
            'help_text': '1 digit',
        },
        'min_upper': {
            'required': 1,
            'help_text': '1 uppercase letter',
        },
        'min_lower': {
            'required': 1,
            'help_text': '1 lowercase letter',
        },
        'min_special': {
            'required': 1,
            'help_text': (
                '1 special character from the following: %s'
                % CompositionValidator.DEFAULT_SPECIAL_CHARACTERS
            ),
        },
    }
    cv = CompositionValidator()
    assert cv.check_mapping == default_check_mapping, 'Check mapping was built wrong'


def test_init_with_int_args_as_zero_builds_empty_check_mapping():
    cv = CompositionValidator(min_numeric=0, min_upper=0, min_lower=0, min_special=0)
    assert cv.check_mapping == {}, 'Check mapping is not empty'


def test_init_with_empty_special_characters_menas_nop_special_check():
    cv = CompositionValidator(special_characters="")
    assert (
        'min_special' not in cv.check_mapping
    ), "Check mapping was built wrong, special check should not have been included"


def test_get_help_text_with_one_required_check_does_not_contain_and_or_comma():
    cv = CompositionValidator(min_upper=0, min_lower=0, min_special=0)
    help_text = cv.get_help_text()
    assert 'and' not in help_text, 'Help text for a single check is wrong, has "and"'
    assert ',' not in help_text, 'Help text for a single check is wrong, has comma'


def test_get_help_text_with_two_or_more_required_check_always_contains_and_and_may_contain_comma():
    cv = CompositionValidator(min_lower=0, min_special=0)
    help_text = cv.get_help_text()
    assert 'and' in help_text, 'Help text for two checks is wrongi, lacks "and"'
    cv = CompositionValidator(min_special=0)
    help_text = cv.get_help_text()
    assert 'and' in help_text, 'Help text for three checks is wrong, lacks "and"'
    assert ',' in help_text, 'Help text for three checks is wrong, lacks comma'
    cv = CompositionValidator()
    help_text = cv.get_help_text()
    assert 'and' in help_text, 'Help text for four checks is wrong'
    assert ',' in help_text, 'Help text for four checks is wrong, lacks comma'


def test_validate_with_correct_password_returns_None():
    cv = CompositionValidator(min_upper=0, min_lower=0, min_special=0)
    result = cv.validate("42")
    assert result is None, "The password did not validate but should"


def test_validate_with_incorrect_password_returns_ValidationError_with_error_message():
    cv = CompositionValidator(min_upper=0, min_lower=0, min_special=0)
    try:
        cv.validate("")
    except ValidationError as e:
        expected_error = 'Invalid password, must have at least 1 digit'
        assert (
            e.message == expected_error
        ), "Error message of incorrect password was wrong"
    else:
        assert False, "Incorrect password did not raise ValidationError"
