import re

from django.core.exceptions import ValidationError


class CompositionValidator:
    DEFAULT_SPECIAL_CHARACTERS = '-=_+,.; :!@#$%&*'
    MAPPING = {
        'min_numeric': {
            'pattern': r'[0-9]',
            'help_singular': '%i digit',
            'help_plural': '%i digits',
        },
        'min_upper': {
            'pattern': r'[A-Z]',
            'help_singular': '%i uppercase letter',
            'help_plural': '%i uppercase letters',
        },
        'min_lower': {
            'pattern': r'[a-z]',
            'help_singular': '%i lowercase letter',
            'help_plural': '%i lowercase letters',
        },
        'min_special': {
            'pattern': None,
            'help_singular': '%i special character from the following: %%s',
            'help_plural': '%i special characters from the following: %%s',
        },
    }

    def __init__(
        self,
        min_numeric=1,
        min_upper=1,
        min_lower=1,
        min_special=1,
        special_characters=DEFAULT_SPECIAL_CHARACTERS,
    ):
        self.check_mapping = {}
        self.special_characters = special_characters
        self._build_check_mapping_item('min_numeric', int(min_numeric))
        self._build_check_mapping_item('min_upper', int(min_upper))
        self._build_check_mapping_item('min_lower', int(min_lower))
        self._build_check_mapping_item('min_special', int(min_special))

    def validate(self, password, user=None):
        errors = []
        for name, value in self.check_mapping.items():
            pattern = self.MAPPING[name]['pattern']
            required = value['required']
            if name == 'min_special':
                pattern = r'[' + self.special_characters + ']'
            found = re.findall(pattern, password)
            if len(found) >= required:
                continue
            # not found
            errors.append(name)
        if errors:
            error_msg = self._build_error_msg(errors)
            raise ValidationError(
                'Invalid password, must have at least ' + error_msg,
                code='password_is_insufficiently_complex',
            )

    def get_help_text(self):
        msg = "The password needs to contain at least: "
        help_texts = [v['help_text'] for v in self.check_mapping.values()]
        if len(self.check_mapping) == 1:
            return msg + help_texts[-1]
        return msg + ', '.join(help_texts[:-1]) + ' and ' + help_texts[-1]

    def _build_check_mapping_item(self, name, count):
        if not count:
            return
        if name == 'min_special' and not self.special_characters:
            return
        self.check_mapping[name] = {'required': count}
        if count == 1:
            help_text = self.MAPPING[name]['help_singular']
        else:
            help_text = self.MAPPING[name]['help_plural']
        help_text = help_text % count
        if name == 'min_special':
            help_text = help_text % self.special_characters
        self.check_mapping[name]['help_text'] = help_text

    def _build_error_msg(self, errors):
        error_msgs = []
        for error in errors:
            error_msgs.append(self.check_mapping[error]['help_text'])
        if len(errors) == 1:
            return error_msgs[0]
        return ' '.join(error_msgs[:-1]) + ' and ' + error_msgs[-1]
