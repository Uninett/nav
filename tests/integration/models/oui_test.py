import pytest

from django.core.exceptions import ValidationError

from nav.models.oui import OUI


class TestOUI:
    def test_validation_should_raise_error_if_oid_is_less_than_6_characters(self):
        with pytest.raises(ValidationError):
            instance = OUI(oui="AABB", vendor="myvendor")
            instance.full_clean()

    def test_validation_should_raise_error_if_oid_is_more_than_6_characters(self):
        with pytest.raises(ValidationError):
            instance = OUI(oui="AABBCCDD", vendor="myvendor")
            instance.full_clean()

    def test_validation_should_allow_oid_with_6_characters(self):
        instance = OUI(oui="AABBCC", vendor="myvendor")
        instance.full_clean()

    def test_string_representation_should_match_oid(self):
        oui = "AABBCC"
        instance = OUI(oui=oui, vendor="myvendor")
        assert str(instance) == oui
