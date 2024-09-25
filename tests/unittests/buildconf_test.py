# ruff: noqa: F401 - importing to test availability

from unittest import TestCase


class TestBuildconf(TestCase):
    def test_VERSION_can_be_imported(self):
        try:
            from nav.buildconf import VERSION
        except ImportError:
            self.fail('VERSION could not be imported')
