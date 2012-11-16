import unittest

from presenter_testcase import PresenterTestCase

class PresenterTests(PresenterTestCase):
    """A collection of unit tests testing the Presenter class"""

    def test_add_invalid_single_item_datasources(self):
        self.assertRaises(ValueError, self.presentation.add_datasource,
            'invalid')
        self.assertRaises(ValueError, self.presentation.add_datasource, -1)
        self.assertEquals(0, len(self.presentation.datasources))

    def test_add_invalid_array_datasources_transaction(self):
        self.assertRaises(ValueError, self.presentation.add_datasource,
            ['invalid', -1])
        self.assertEquals(0, len(self.presentation.datasources))

        self.assertRaises(ValueError, self.presentation.add_datasource, [-1])
        self.assertEquals(0, len(self.presentation.datasources))

        self.assertRaises(ValueError, self.presentation.add_datasource,
            [self.test_data[0], 1])
        self.assertEquals(0, len(self.presentation.datasources))

        self.assertRaises(ValueError, self.presentation.add_datasource,
            [-2, self.test_data[0]])
        self.assertEquals(0, len(self.presentation.datasources))


    def test_add_invalid_none_datasources(self):
        self.assertRaises(ValueError, self.presentation.add_datasource, [None])
        self.assertRaises(ValueError, self.presentation.add_datasource, None)
        self.assertEquals(0, len(self.presentation.datasources))


    def test_add_datasource(self):
        self.presentation.add_datasource(self.test_data[0])
        self.assertEquals(1, len(self.presentation.datasources))

        self.presentation.add_datasource(self.test_data[1])
        self.assertEquals(2, len(self.presentation.datasources))

        self.presentation.add_datasource(self.test_data[2])
        self.presentation.add_datasource(self.test_data[3])
        self.presentation.add_datasource(self.test_data[4])

        self.assertEquals(5, len(self.presentation.datasources))

    def test_add_datasources(self):
        self.presentation.add_datasource(self.test_data[:4])
        self.assertEquals(4, len(self.presentation.datasources))

        self.presentation.add_datasource(self.test_data[5:])
        self.assertEquals(9, len(self.presentation.datasources))

    def test_add_duplicate_entry(self):
        self.presentation.add_datasource(self.test_data[0])
        self.presentation.add_datasource(self.test_data[0])
        self.assertEquals(1, len(self.presentation.datasources))


    def test_remove_datasource(self):
        rrd_datasource_2 = self._create_datasource(2)
        self.presentation.datasources = [
            self._create_datasource(1),
            rrd_datasource_2,
            self._create_datasource(3)
        ]

        self.assertEquals(3, len(self.presentation.datasources))
        self.presentation.remove_datasource(rrd_datasource_2)
        self.assertEquals(2, len(self.presentation.datasources))
        self.assertEquals('ds1', self.presentation.datasources[0].name)
        self.assertEquals('ds3', self.presentation.datasources[1].name)

    def test_delete_all_datasources(self):
        self.presentation.remove_all_datasources()
        self.assertEquals(0, len(self.presentation.datasources))

        self.presentation.datasources = self.test_data
        self.assertEquals(10, len(self.presentation.datasources))

        self.presentation.remove_all_datasources()
        self.assertEquals(0, len(self.presentation.datasources))

if __name__ == '__main__':
    unittest.main()
