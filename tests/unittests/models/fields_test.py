# -*- coding: utf-8 -*-

from datetime import datetime as dt
from decimal import Decimal
import pickle

from django.core import exceptions
from django.db import connection

import pytest

from nav.models.fields import CIDRField
from nav.models.fields import DateTimeInfinityField
from nav.models.fields import DictAsJsonField
from nav.models.fields import LegacyGenericForeignKey
from nav.models.fields import PointField


class TestCIDRField(object):
    def test_to_python_empty(self):
        falsey = (None, '', 0, False, [], {}, set(), 0.0)
        field = CIDRField()
        for value in falsey:
            result = field.to_python(value)
            assert result == value

    def test_to_python_valid_cidr(self):
        field = CIDRField()
        cidr4 = '192.168.0.0/23'
        result4 = field.to_python(cidr4)
        assert cidr4 == result4
        cidr6 = '1234:dead:beef::/64'
        result6 = field.to_python(cidr6)
        assert cidr6 == result6

    def test_to_python_valid_ip(self):
        field = CIDRField()
        ip4 = '192.168.0.0'
        result4 = field.to_python(ip4)
        assert ip4 == result4
        bip4 = b'192.168.0.0'
        bresult4 = field.to_python(bip4)
        assert ip4 == bresult4
        ip6 = '1234:dead:beef::63'
        result6 = field.to_python(ip6)
        assert ip6 == result6
        bip6 = b'1234:dead:beef::63'
        bresult6 = field.to_python(bip6)
        assert ip6 == bresult6

    def test_to_python_invalid(self):
        field = CIDRField()
        values = ('333.222.999.0', 'blåbærsyltetøy', 300, 3.1415, [True])
        for value in values:
            with pytest.raises(exceptions.ValidationError):
                field.to_python(value)

    def test_to_python_seemingly_valid(self):
        # IPY works on CIDRs for networks, not hosts
        field = CIDRField()
        ip6 = '1234:dead:beef::63/23'
        with pytest.raises(exceptions.ValidationError):
            field.to_python(ip6)


class TestDateTimeInfinityField(object):
    def test_get_db_prep_value_infinity(self):
        field = DateTimeInfinityField()
        result_min = field.get_db_prep_value(dt.min, connection)
        assert result_min == '-infinity'
        result_max = field.get_db_prep_value(dt.max, connection)
        assert result_max == 'infinity'

    def test_get_db_prep_value_prepared_other(self):
        field = DateTimeInfinityField()
        test_val = dt(2018, 3, 5)
        result = field.get_db_prep_value(test_val, connection, prepared=True)

        # The actual result here will vary with Django versions and which
        # database engine has been selected in the Django settings!
        expected = super(DateTimeInfinityField, field).get_db_prep_value(
            test_val, connection, prepared=True
        )

        assert result == expected

    def test_get_db_prep_value_unprepared_other(self):
        field = DateTimeInfinityField()
        test_val = dt(2018, 3, 5)
        result = field.get_db_prep_value(test_val, connection, prepared=False)

        # The actual result here will vary with Django versions and which
        # database engine has been selected in the Django settings!
        expected = super(DateTimeInfinityField, field).get_db_prep_value(
            test_val, connection, prepared=False
        )

        assert result == expected


class TestDictAsJsonField(object):
    def test_to_python_dict(self):
        field = DictAsJsonField()
        value = {'a': 'b'}
        result = field.to_python(value)
        assert result == value

    def test_to_python_json(self):
        field = DictAsJsonField()
        value = '{"a": "b"}'
        result = field.to_python(value)
        assert result == {"a": "b"}
        value = '[1, 2, 3]'
        result = field.to_python(value)
        assert result == [1, 2, 3]
        value = b'[1, 2, 3]'
        result = field.to_python(value)
        assert result == [1, 2, 3]

    def test_to_python_pickle(self):
        field = DictAsJsonField()
        orig_value = 2
        value = pickle.dumps(orig_value, protocol=1)
        result = field.to_python(value)
        assert result == orig_value

    def test_to_python_pickle_str(self):
        # Github issue #2085
        # Not all pickles can be converted to Py3 str at all so use an actual
        # production value
        field = DictAsJsonField()
        orig_value = {'refresh_interval': 600000}
        value = "(dp0\nS'refresh_interval'\np1\nI600000\ns."
        result = field.to_python(value)
        assert result == orig_value

    def test_get_prep_value_empty(self):
        field = DictAsJsonField()
        result = field.get_prep_value(None)
        assert result is None

    def test_get_prep_value_filled(self):
        field = DictAsJsonField()
        result = field.get_prep_value({'a': 'b'})
        assert result == '{"a": "b"}'


class TestLegacyGenericForeignKey(object):
    def test_get_model_class_unknown_model(self):
        mc = LegacyGenericForeignKey.get_model_class('doesnotexistindb')
        assert mc is None

    def test_get_model_class_known_model(self):
        # use existing class
        mc = LegacyGenericForeignKey.get_model_class('subsystem')
        assert bool(mc)


class TestPointField(object):
    def test_to_python_from_string(self):
        expected_point = (Decimal("1.2"), Decimal("3.4"))
        point_string = "(1.2, 3.4)"
        field = PointField()
        point = field.to_python(point_string)
        assert expected_point == point

    def get_db_prep_value(self):
        expected_db_string = "(7.1,5.12)"
        point = (Decimal("7.1"), Decimal("5.12"))
        field = PointField()
        db_string = field.get_db_prep_value(point)
        assert expected_db_string == db_string
