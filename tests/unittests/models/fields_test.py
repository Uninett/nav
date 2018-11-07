# -*- coding: utf-8 -*-

from datetime import datetime as dt
from decimal import Decimal
import pickle
from unittest import TestCase

from django.core import exceptions
from django.db import connection
from django.db.models import DateTimeField

from nav.models.fields import CIDRField
from nav.models.fields import DateTimeInfinityField
from nav.models.fields import DictAsJsonField
from nav.models.fields import LegacyGenericForeignKey
from nav.models.fields import PointField


class CIDRFieldTestCase(TestCase):

    def test_to_python_empty(self):
        falsey = (None, u'', 0, False, [], {}, set(), 0.0)
        field = CIDRField()
        for value in falsey:
            result = field.to_python(value)
            self.assertEqual(result, value)

    def test_to_python_valid_cidr(self):
        field = CIDRField()
        cidr4 = u'192.168.0.0/23'
        result4 = field.to_python(cidr4)
        self.assertEqual(cidr4, result4)
        cidr6 = u'1234:dead:beef::/64'
        result6 = field.to_python(cidr6)
        self.assertEqual(cidr6, result6)

    def test_to_python_valid_ip(self):
        field = CIDRField()
        ip4 = u'192.168.0.0'
        result4 = field.to_python(ip4)
        self.assertEqual(ip4, result4)
        bip4 = b'192.168.0.0'
        bresult4 = field.to_python(bip4)
        self.assertEqual(ip4, bresult4)
        ip6 = u'1234:dead:beef::63'
        result6 = field.to_python(ip6)
        self.assertEqual(ip6, result6)
        bip6 = b'1234:dead:beef::63'
        bresult6 = field.to_python(bip6)
        self.assertEqual(ip6, bresult6)

    def test_to_python_invalid(self):
        field = CIDRField()
        values = (u'333.222.999.0', u'blåbærsyltetøy', 300, 3.1415, [True])
        for value in values:
            with self.assertRaises(exceptions.ValidationError):
                field.to_python(value)


class DateTimeInfinityFieldTestCase(TestCase):

    def test_get_db_prep_value_infinity(self):
        field = DateTimeInfinityField()
        result_min = field.get_db_prep_value(dt.min, connection)
        self.assertEqual(result_min, u'-infinity')
        result_max = field.get_db_prep_value(dt.max, connection)
        self.assertEqual(result_max, u'infinity')

    def test_get_db_prep_value_prepared_other(self):
        field = DateTimeInfinityField()
        test_val = dt(2018, 3, 5)
        result = field.get_db_prep_value(test_val, connection, prepared=True)

        # The actual result here will vary with Django versions and which
        # database engine has been selected in the Django settings!
        expected = super(DateTimeInfinityField, field).get_db_prep_value(
            test_val, connection, prepared=True)

        self.assertEqual(result, expected)

    def test_get_db_prep_value_unprepared_other(self):
        field = DateTimeInfinityField()
        test_val = dt(2018, 3, 5)
        result = field.get_db_prep_value(test_val, connection, prepared=False)

        # The actual result here will vary with Django versions and which
        # database engine has been selected in the Django settings!
        expected = super(DateTimeInfinityField, field).get_db_prep_value(
            test_val, connection, prepared=False)

        self.assertEqual(result, expected)


class DictAsJsonFieldTest(TestCase):

    def test_to_python_dict(self):
        field = DictAsJsonField()
        value = {'a': 'b'}
        result = field.to_python(value)
        self.assertEqual(result, value)

    def test_to_python_json(self):
        field = DictAsJsonField()
        value = u'{"a": "b"}'
        result = field.to_python(value)
        self.assertEqual(result, {"a": "b"})
        value = u'[1, 2, 3]'
        result = field.to_python(value)
        self.assertEqual(result, [1, 2, 3])
        value = b'[1, 2, 3]'
        result = field.to_python(value)
        self.assertEqual(result, [1, 2, 3])

    def test_to_python_pickle(self):
        field = DictAsJsonField()
        orig_value = 2
        value = pickle.dumps(orig_value)
        result = field.to_python(value)
        self.assertEqual(result, orig_value)

    def test_get_prep_value_empty(self):
        field = DictAsJsonField()
        result = field.get_prep_value(None)
        self.assertEqual(result, None)

    def test_get_prep_value_filled(self):
        field = DictAsJsonField()
        result = field.get_prep_value({'a': 'b'})
        self.assertEqual(result, u'{"a": "b"}')


class LegacyGenericForeignKeyTest(TestCase):

    def test_get_model_class_unknown_model(self):
        mc = LegacyGenericForeignKey.get_model_class('doesnotexistindb')
        self.assertEqual(mc, None)

    def test_get_model_class_known_model(self):
        # use existing class
        mc = LegacyGenericForeignKey.get_model_class('subsystem')
        self.assertTrue(bool(mc))


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
