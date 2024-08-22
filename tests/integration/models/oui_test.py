import pytest

from django.db.utils import IntegrityError

from nav.models.oui import OUI


class TestOUI:
    def test_string_representation_should_match_oui(self, valid_oui):
        assert str(valid_oui) == valid_oui.oui

    def test_save_should_raise_error_if_last_3_bytes_are_not_zero(self, invalid_oui):
        with pytest.raises(IntegrityError):
            invalid_oui.save()

    def test_save_should_allow_oui_if_last_3_bytes_are_zero(self, valid_oui):
        valid_oui.save()


@pytest.fixture()
def valid_oui():
    oui = "aa:bb:cc:00:00:00"
    instance = OUI(oui=oui, vendor="myvendor")
    yield instance
    instance.delete()


@pytest.fixture()
def invalid_oui():
    oui = "aa:bb:cc:dd:ee:ff"
    instance = OUI(oui=oui, vendor="myvendor")
    yield instance
    instance.delete()
