from nav.config import _config_resource_walk


from unittest import TestCase


class TestConfigResourceWalk(TestCase):
    def test_should_read_relative_paths_as_strings_from_nav_package_and_return_a_long_list_of_strings(  # noqa: E501
        self,
    ):
        # result should be many, many relative paths as strings
        result = tuple(_config_resource_walk())  # generator
        self.assertTrue(len(result) > 20)
        for relpath in result:
            self.assertIsInstance(relpath, str)
            self.assertFalse(relpath.startswith('/'))
