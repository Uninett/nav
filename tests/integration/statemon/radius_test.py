from nav.statemon.checker.RadiusChecker import DEFAULT_DICTIONARY

from pyrad.dictionary import Dictionary


def test_installed_pyrad_can_parse_default_dictionary():
    assert Dictionary(DEFAULT_DICTIONARY)
