from nav.pgsync import ChangeScriptFinder


from unittest import TestCase


class TestChangeScriptFinder(TestCase):
    def test_init_should_read_sql_filenames_from_package_and_return_list_of_relative_filenames(
        self,
    ):
        csf = ChangeScriptFinder('nav.models')
        self.assertTrue(len(csf) > 40)
        for sql_filename in csf:
            self.assertTrue(sql_filename.startswith('sql/'))
            self.assertTrue(sql_filename.endswith('.sql'))
