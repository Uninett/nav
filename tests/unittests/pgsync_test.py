from nav.pgsync import ChangeScriptFinder, Synchronizer


from unittest import TestCase


class TestChangeScriptFinder(TestCase):
    def test_init_should_read_sql_filenames_from_package_and_return_list_of_relative_filenames(  # noqa: E501
        self,
    ):
        csf = ChangeScriptFinder('nav.models')
        self.assertTrue(len(csf) > 40)
        for sql_filename in csf:
            self.assertTrue(sql_filename.startswith('sql/'))
            self.assertTrue(sql_filename.endswith('.sql'))


class TestSynchronizer(TestCase):
    def test_should_read_sql_file_from_package_and_return_bytes(self):
        syncer = Synchronizer('nav.models', config=True)
        filename = "sql/baseline/manage.sql"
        sql = syncer._read_sql_file(filename)
        self.assertIn("CREATE TABLE org", str(sql))
