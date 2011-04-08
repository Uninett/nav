from unittest import TestCase
from nav.bulkparse import *

class TestBulkParser(TestCase):
    def test_init(self):
        data = "room1:10.0.0.186:myorg:OTHER::parrot::"
        b = BulkParser(data)
        self.assertTrue(isinstance(b, BulkParser))

    def test_overriden_validator(self):
        class TestParser(BulkParser):
            format = ('one', 'two')
            required = 2

            def _validate_one(self, value):
                return value == '1'

        data = "1:2\nonce:twice"
        b = TestParser(data)
        try:
            list(b)
        except InvalidFieldValue, error:
            self.assertEquals(error.line_num, 2)
            self.assertEquals(error.field, 'one')
            self.assertEquals(error.value, 'once')
        else:
            self.fail("No exception raised")

class TestNetboxBulkParser(TestCase):
    def test_parse_returns_iterator(self):
        data = "room1:10.0.0.186:myorg:OTHER::parrot::"
        b = NetboxBulkParser(data)
        self.assertTrue(hasattr(b, 'next'))

    def test_parse_single_line_should_yield_value(self):
        data = "room1:10.0.0.186:myorg:OTHER::parrot::"
        b = NetboxBulkParser(data)
        out_data = b.next()
        self.assertTrue(out_data is not None)

    def test_parse_single_line_yields_columns(self):
        data = ("room1:10.0.0.186:myorg:SW:public:parrot:secret:doesthings:"
                "blah1:blah2")
        b = NetboxBulkParser(data)
        out_data = b.next()
        self.assertTrue(isinstance(out_data, dict), out_data)
        self.assertEquals(out_data['roomid'], 'room1')
        self.assertEquals(out_data['ip'], '10.0.0.186')
        self.assertEquals(out_data['orgid'], 'myorg')
        self.assertEquals(out_data['catid'], 'SW')
        self.assertEquals(out_data['serial'], 'parrot')
        self.assertEquals(out_data['subcat'], ['blah1', 'blah2'])

    def test_get_header(self):
        self.assertEquals(
            NetboxBulkParser.get_header(),
            "#roomid:ip:orgid:catid[:ro:serial:rw:function:subcat:...]")

    def test_two_rows_returned_with_empty_lines_in_input(self):
        data = ("room1:10.0.0.186:myorg:SW:public:parrot::\n"
                "\n"
                "room1:10.0.0.187:myorg:OTHER::parrot::\n")
        b = NetboxBulkParser(data)
        out_data = list(b)
        self.assertEquals(len(out_data), 2)

    def test_three_lines_with_two_rows_should_be_counted_as_three(self):
        data = ("room1:10.0.0.186:myorg:SW:public:parrot::\n"
                "\n"
                "room1:10.0.0.187:myorg:OTHER::parrot::\n")
        b = NetboxBulkParser(data)
        out_data = list(b)
        self.assertEquals(b.line_num, 3)

    def test_short_line_should_raise_error(self):
        data = "room1:10.0.0.8"
        b = NetboxBulkParser(data)
        self.assertRaises(RequiredFieldMissing, b.next)

    def test_invalid_ip_should_raise_error(self):
        data = "room1:10.0.x.x:myorg:SW:public:parrot::\n"
        b = NetboxBulkParser(data)
        self.assertRaises(InvalidFieldValue, b.next)


    def test_short_line_should_raise_error_with_correct_details(self):
        data = "room1:10.0.0.8"
        b = NetboxBulkParser(data)
        try:
            b.next()
        except RequiredFieldMissing, error:
            self.assertEquals(error.line_num, 1)
            self.assertEquals(error.missing_field, 'orgid')
        else:
            self.fail("No exception raised")

class TestUsageBulkParser(TestCase):
    def test_get_header(self):
        self.assertEquals(
            UsageBulkParser.get_header(),
            "#usageid:descr")

    def test_leading_comments_should_be_stripped(self):
        data = "#comment\nsby:student village"
        b = UsageBulkParser(data)
        first_row = b.next()
        self.assertEquals(first_row['usageid'], 'sby')

class TestPrefixBulkParser(TestCase):
    def test_invalid_prefix_should_raise_error(self):
        data = "10.0.0.x/3f:scope"
        b = PrefixBulkParser(data)
        self.assertRaises(InvalidFieldValue, b.next)

    def test_valid_prefix_should_not_raise_error(self):
        data = "10.0.0.0/8:scope"
        b = PrefixBulkParser(data)
        self.assertTrue(b.next())

class TestServiceBulkParser(TestCase):
    def test_invalid_service_arguments_should_raise_error(self):
        data = "host.example.org;http;port80"
        b = ServiceBulkParser(data)
        self.assertRaises(InvalidFieldValue, b.next)

    def test_valid_service_arguments_should_not_raise_error(self):
        data = "host.example.org;http;port=80;uri=/"
        b = ServiceBulkParser(data)
        self.assertTrue(b.next())

class TestCommentStripper(TestCase):
    def test_leading_comment_should_be_stripped(self):
        data = StringIO('#leadingcomment\nsomething\n')
        stripper = CommentStripper(data)
        self.assertEquals(stripper.next(), '\n')
        self.assertEquals(stripper.next(), 'something\n')

    def test_suffix_comment_should_be_stripped(self):
        data = StringIO('somedata\notherdata    # ignore this\n')
        stripper = CommentStripper(data)
        self.assertEquals(stripper.next(), 'somedata\n')
        self.assertEquals(stripper.next(), 'otherdata\n')

class TestHeaderGenerator(TestCase):
    def test_simple(self):
        class C(BulkParser):
            format = ('one', 'two', 'three')
            required = 3

        self.assertEquals(C.get_header(), "#one:two:three")

    def test_one_optional(self):
        class C(BulkParser):
            format = ('one', 'two', 'three', 'optional')
            required = 3

        self.assertEquals(C.get_header(), "#one:two:three[:optional]")

    def test_two_optional(self):
        class C(BulkParser):
            format = ('one', 'two', 'three', 'opt1', 'opt2')
            required = 3

        self.assertEquals(C.get_header(), "#one:two:three[:opt1:opt2]")

    def test_optional_with_restkey(self):
        class C(BulkParser):
            format = ('one', 'two', 'three', 'optional')
            restkey = 'arg'
            required = 3

        self.assertEquals(C.get_header(), "#one:two:three[:optional:arg:...]")

    def test_two_required_plus_restkey(self):
        class C(BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            required = 2

        self.assertEquals(C.get_header(), "#one:two[:rest:...]")

    def test_two_required_plus_restkey_format(self):
        class C(BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            restkey_format = 'thing=value'
            required = 2

        self.assertEquals(C.get_header(), "#one:two[:thing=value:...]")
