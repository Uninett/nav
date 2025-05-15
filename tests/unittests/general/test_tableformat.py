from unittest import TestCase
from nav.tableformat import SimpleTableFormatter


class TestSimpleTableFormatter(TestCase):
    def test_column_count(self):
        data = (('one', 'two', 'three'), ('alice', 'bob', 'charlie'))
        s = SimpleTableFormatter(data)
        self.assertEqual(s._get_column_count(), 3)

    def test_get_max_width_of_column(self):
        data = (('1234', '12345', '1234567'), ('123', '12', '123456'))
        s = SimpleTableFormatter(data)
        self.assertEqual(s._get_max_width_of_column(0), 4)
        self.assertEqual(s._get_max_width_of_column(1), 5)
        self.assertEqual(s._get_max_width_of_column(2), 7)

    def test_get_max_width_of_column_with_integers(self):
        data = ((1234, '12345', '1234567'), ('123', 12, '123456'))
        s = SimpleTableFormatter(data)
        self.assertEqual(s._get_max_width_of_column(0), 4)
        self.assertEqual(s._get_max_width_of_column(1), 5)
        self.assertEqual(s._get_max_width_of_column(2), 7)

    def test_find_widest_elements(self):
        data = (('1234', '12345', '1234567'), ('123', '12', '123456'))
        s = SimpleTableFormatter(data)
        self.assertEqual(s._find_widest_elements(), [4, 5, 7])

    def test_format_row(self):
        row = ['one', 'two', 'three']
        widths = [len(i) for i in row]
        s = SimpleTableFormatter(None)
        self.assertEqual(s._format_row(row, widths), 'one | two | three')

    def test_get_formatted_table(self):
        data = (('1234', '12345', '1234567'), ('123', '12', '123456'))
        s = SimpleTableFormatter(data)
        self.assertEqual(
            s.get_formatted_table(), "1234 | 12345 | 1234567\n 123 |    12 |  123456"
        )
