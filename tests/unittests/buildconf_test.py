# ruff: noqa: F401 - importing to test availability

from unittest import TestCase

import nav.buildconf


class TestBuildconf(TestCase):
    def test_VERSION_can_be_imported(self):
        try:
            from nav.buildconf import VERSION
        except ImportError:
            self.fail('VERSION could not be imported')

    def test_VERSION_contains_dot(self):
        """
        Assumes that VERSION containing a '.' implies
        it is set to a valid version string
        """
        assert "." in nav.buildconf.VERSION
