from unittest import TestCase

from nav.models.fields import *

class PointFieldTest(TestCase):
    def test_to_python_from_string(self):
        expected_point = (Decimal("1.2"), Decimal("3.4"))
        point_string = "(1.2, 3.4)"
        field = PointField()
        point = field.to_python(point_string)
        self.assertEquals(expected_point, point)

    def get_db_prep_value(self):
        expected_db_string = "(7.1,5.12)"
        point = (Decimal("7.1"), Decimal("5.12"))
        field = PointField()
        db_string = field.get_db_prep_value(point)
        self.assertEquals(expected_db_string, db_string)
