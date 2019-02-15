"""Tests for bulkparse"""

# pylint: disable=C0111, C0103, W0614

from io import BytesIO
from unittest import TestCase

from django.utils import six

from nav import bulkparse


class TestBulkParser(TestCase):
    def test_init(self):
        data = b"room1:10.0.0.186:myorg:OTHER::parrot::"
        b = bulkparse.BulkParser(data)
        self.assertTrue(isinstance(b, bulkparse.BulkParser))

    def test_overriden_validator(self):
        class TestParser(bulkparse.BulkParser):
            format = ('one', 'two')
            required = 2

            def _validate_one(self, value):
                return value == '1'

        data = b"1:2\nonce:twice"
        b = TestParser(data)
        try:
            list(b)
        except bulkparse.InvalidFieldValue as error:
            self.assertEqual(error.line_num, 2)
            self.assertEqual(error.field, 'one')
            self.assertEqual(error.value, 'once')
        else:
            self.fail("No exception raised")


class TestNetboxBulkParser(TestCase):
    def test_parse_returns_iterator(self):
        data = b"room1:10.0.0.186:myorg:OTHER::parrot::"
        b = bulkparse.NetboxBulkParser(data)
        self.assertTrue(hasattr(b, '__next__'))

    def test_parse_single_line_should_yield_value(self):
        data = b"room1:10.0.0.186:myorg:OTHER::parrot::"
        b = bulkparse.NetboxBulkParser(data)
        out_data = six.next(b)
        self.assertTrue(out_data is not None)

    def test_parse_single_line_yields_columns(self):
        data = (b"room1:10.0.0.186:myorg:SW:1:public:secret:amaster:doesthings:"
                b"key=value:blah1:blah2")
        b = bulkparse.NetboxBulkParser(data)
        out_data = six.next(b)
        self.assertTrue(isinstance(out_data, dict), out_data)
        self.assertEqual(out_data['roomid'], 'room1')
        self.assertEqual(out_data['ip'], '10.0.0.186')
        self.assertEqual(out_data['orgid'], 'myorg')
        self.assertEqual(out_data['catid'], 'SW')
        self.assertEqual(out_data['master'], 'amaster')
        self.assertEqual(out_data['data'], 'key=value')
        self.assertEqual(out_data['netboxgroup'], ['blah1', 'blah2'])

    def test_get_header(self):
        self.assertEqual(
            bulkparse.NetboxBulkParser.get_header(),
            "#roomid:ip:orgid:catid"
            "[:snmp_version:ro:rw:master:function:data:netboxgroup:...]")

    def test_two_rows_returned_with_empty_lines_in_input(self):
        data = (b"room1:10.0.0.186:myorg:SW:1:public:parrot::\n"
                b"\n"
                b"room1:10.0.0.187:myorg:OTHER::parrot::\n")
        b = bulkparse.NetboxBulkParser(data)
        out_data = list(b)
        self.assertEqual(len(out_data), 2)

    def test_three_lines_with_two_rows_should_be_counted_as_three(self):
        data = (b"room1:10.0.0.186:myorg:SW:1:public:parrot::\n"
                b"\n"
                b"room1:10.0.0.187:myorg:OTHER::parrot::\n")
        b = bulkparse.NetboxBulkParser(data)
        out_data = list(b)
        self.assertEqual(b.line_num, 3)

    def test_short_line_should_raise_error(self):
        data = b"room1:10.0.0.8"
        b = bulkparse.NetboxBulkParser(data)
        self.assertRaises(bulkparse.RequiredFieldMissing, b.__next__)

    def test_invalid_ip_should_raise_error(self):
        data = b"room1:10.0.x.x:myorg:SW:public:parrot::\n"
        b = bulkparse.NetboxBulkParser(data)
        self.assertRaises(bulkparse.InvalidFieldValue, lambda: six.next(b))

    def test_short_line_should_raise_error_with_correct_details(self):
        data = b"room1:10.0.0.8"
        b = bulkparse.NetboxBulkParser(data)
        try:
            six.next(b)
        except bulkparse.RequiredFieldMissing as error:
            self.assertEqual(error.line_num, 1)
            self.assertEqual(error.missing_field, 'orgid')
        else:
            self.fail("No exception raised")


class TestUsageBulkParser(TestCase):
    def test_get_header(self):
        self.assertEqual(
            bulkparse.UsageBulkParser.get_header(),
            "#usageid:descr")

    def test_leading_comments_should_be_stripped(self):
        data = b"#comment\nsby:student village"
        b = bulkparse.UsageBulkParser(data)
        first_row = six.next(b)
        self.assertEqual(first_row['usageid'], 'sby')


class TestPrefixBulkParser(TestCase):
    def test_invalid_prefix_should_raise_error(self):
        data = b"10.0.0.x/3f:scope"
        b = bulkparse.PrefixBulkParser(data)
        self.assertRaises(bulkparse.InvalidFieldValue, lambda: six.next(b))

    def test_valid_prefix_should_not_raise_error(self):
        data = b"10.0.0.0/8:scope"
        b = bulkparse.PrefixBulkParser(data)
        self.assertTrue(six.next(b))


class TestServiceBulkParser(TestCase):
    def test_invalid_service_arguments_should_raise_error(self):
        data = b"host.example.org;http;port80"
        b = bulkparse.ServiceBulkParser(data)
        self.assertRaises(bulkparse.InvalidFieldValue, lambda: six.next(b))

    def test_valid_service_arguments_should_not_raise_error(self):
        data = b"host.example.org;http;port=80;uri=/"
        b = bulkparse.ServiceBulkParser(data)
        self.assertTrue(six.next(b))


class TestCommentStripper(TestCase):
    def test_leading_comment_should_be_stripped(self):
        data = iter(['#leadingcomment\n', 'something\n'])
        stripper = bulkparse.CommentStripper(data)
        self.assertEqual(six.next(stripper), '\n')
        self.assertEqual(six.next(stripper), 'something\n')

    def test_suffix_comment_should_be_stripped(self):
        data = iter(['somedata\n', 'otherdata    # ignore this\n'])
        stripper = bulkparse.CommentStripper(data)
        self.assertEqual(six.next(stripper), 'somedata\n')
        self.assertEqual(six.next(stripper), 'otherdata\n')


class TestHeaderGenerator(TestCase):
    def test_simple(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three')
            required = 3

        self.assertEqual(C.get_header(), "#one:two:three")

    def test_one_optional(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'optional')
            required = 3

        self.assertEqual(C.get_header(), "#one:two:three[:optional]")

    def test_two_optional(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'opt1', 'opt2')
            required = 3

        self.assertEqual(C.get_header(), "#one:two:three[:opt1:opt2]")

    def test_optional_with_restkey(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'optional')
            restkey = 'arg'
            required = 3

        self.assertEqual(C.get_header(), "#one:two:three[:optional:arg:...]")

    def test_two_required_plus_restkey(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            required = 2

        self.assertEqual(C.get_header(), "#one:two[:rest:...]")

    def test_two_required_plus_restkey_format(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            restkey_format = 'thing=value'
            required = 2

        self.assertEqual(C.get_header(), "#one:two[:thing=value:...]")
