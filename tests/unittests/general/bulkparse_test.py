"""Tests for bulkparse"""

import pytest

from nav import bulkparse


class TestBulkParser(object):
    def test_init(self):
        data = b"room1:10.0.0.186:myorg:OTHER::parrot::"
        b = bulkparse.BulkParser(data)
        assert isinstance(b, bulkparse.BulkParser)

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
            assert error.line_num == 2
            assert error.field == 'one'
            assert error.value == 'once'
        else:
            self.fail("No exception raised")


class TestNetboxBulkParser(object):
    def test_parse_returns_iterator(self):
        data = b"room1:10.0.0.186:myorg:OTHER:SNMP v1 read profile:::"
        b = bulkparse.NetboxBulkParser(data)
        assert hasattr(b, '__next__')

    def test_parse_single_line_should_yield_value(self):
        data = b"room1:10.0.0.186:myorg:OTHER:SNMP v2c read profile:::"
        b = bulkparse.NetboxBulkParser(data)
        out_data = next(b)
        assert out_data is not None

    def test_parse_single_line_yields_columns(self):
        data = (
            b"room1:10.0.0.186:myorg:SW:SNMP v2c read profile:amaster:doesthings:"
            b"key=value:blah1:blah2"
        )
        b = bulkparse.NetboxBulkParser(data)
        out_data = next(b)
        assert isinstance(out_data, dict)
        assert out_data['roomid'] == 'room1'
        assert out_data['ip'] == '10.0.0.186'
        assert out_data['orgid'] == 'myorg'
        assert out_data['catid'] == 'SW'
        assert out_data['master'] == 'amaster'
        assert out_data['data'] == 'key=value'
        assert out_data['netboxgroup'] == ['blah1', 'blah2']

    def test_get_header(self):
        assert (
            bulkparse.NetboxBulkParser.get_header() == "#roomid:ip:orgid:catid"
            "[:management_profiles:master:function:data:netboxgroup:...]"
        )

    def test_two_rows_returned_with_empty_lines_in_input(self):
        data = (
            b"room1:10.0.0.186:myorg:SW:SNMP v1 read profile::\n"
            b"\n"
            b"room1:10.0.0.187:myorg:OTHER:SNMP v1 read profile::\n"
        )
        b = bulkparse.NetboxBulkParser(data)
        out_data = list(b)
        assert len(out_data) == 2

    def test_three_lines_with_two_rows_should_be_counted_as_three(self):
        data = (
            b"room1:10.0.0.186:myorg:SW:SNMP v1 read profile::\n"
            b"\n"
            b"room1:10.0.0.187:myorg:OTHER:SNMP v2c read profile::\n"
        )
        b = bulkparse.NetboxBulkParser(data)
        list(b)  # Generator needs to be consumed for this test to succeed
        assert b.line_num == 3

    def test_short_line_should_raise_error(self):
        data = b"room1:10.0.0.8"
        b = bulkparse.NetboxBulkParser(data)
        with pytest.raises(bulkparse.RequiredFieldMissing):
            b.__next__()

    def test_invalid_ip_should_raise_error(self):
        data = b"room1:10.0.x.x:myorg:SW:SNMP v2c read profile::\n"
        b = bulkparse.NetboxBulkParser(data)
        with pytest.raises(bulkparse.InvalidFieldValue):
            next(b)

    def test_short_line_should_raise_error_with_correct_details(self):
        data = b"room1:10.0.0.8"
        b = bulkparse.NetboxBulkParser(data)
        try:
            next(b)
        except bulkparse.RequiredFieldMissing as error:
            assert error.line_num == 1
            assert error.missing_field == 'orgid'
        else:
            self.fail("No exception raised")


class TestManagementProfileBulkParser(object):
    def test_configuration_should_be_parsed(self):
        config = b'{"version":1, "community":"public"}'
        data = b'SNMP v1 read profile:SNMP:"' + config.replace(b'"', b'""') + b'"'
        b = bulkparse.ManagementProfileBulkParser(data)
        first_row = next(b)
        assert 'configuration' in first_row
        assert first_row['configuration'] == config.decode('utf-8')


class TestUsageBulkParser(object):
    def test_get_header(self):
        assert bulkparse.UsageBulkParser.get_header() == "#usageid:descr"

    def test_leading_comments_should_be_stripped(self):
        data = b"#comment\nsby:student village"
        b = bulkparse.UsageBulkParser(data)
        first_row = next(b)
        assert first_row['usageid'] == 'sby'


class TestPrefixBulkParser(object):
    def test_invalid_prefix_should_raise_error(self):
        data = b"10.0.0.x/3f:scope"
        b = bulkparse.PrefixBulkParser(data)
        with pytest.raises(bulkparse.InvalidFieldValue):
            next(b)

    def test_valid_prefix_should_not_raise_error(self):
        data = b"10.0.0.0/8:scope"
        b = bulkparse.PrefixBulkParser(data)
        assert next(b)


class TestServiceBulkParser(object):
    def test_invalid_service_arguments_should_raise_error(self):
        data = b"host.example.org;http;port80"
        b = bulkparse.ServiceBulkParser(data)
        with pytest.raises(bulkparse.InvalidFieldValue):
            next(b)

    def test_valid_service_arguments_should_not_raise_error(self):
        data = b"host.example.org;http;port=80;uri=/"
        b = bulkparse.ServiceBulkParser(data)
        assert next(b)


class TestCommentStripper(object):
    def test_leading_comment_should_be_stripped(self):
        data = iter(['#leadingcomment\n', 'something\n'])
        stripper = bulkparse.CommentStripper(data)
        assert next(stripper) == '\n'
        assert next(stripper) == 'something\n'

    def test_suffix_comment_should_be_stripped(self):
        data = iter(['somedata\n', 'otherdata    # ignore this\n'])
        stripper = bulkparse.CommentStripper(data)
        assert next(stripper) == 'somedata\n'
        assert next(stripper) == 'otherdata\n'


class TestHeaderGenerator(object):
    def test_simple(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three')
            required = 3

        assert C.get_header() == "#one:two:three"

    def test_one_optional(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'optional')
            required = 3

        assert C.get_header() == "#one:two:three[:optional]"

    def test_two_optional(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'opt1', 'opt2')
            required = 3

        assert C.get_header() == "#one:two:three[:opt1:opt2]"

    def test_optional_with_restkey(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two', 'three', 'optional')
            restkey = 'arg'
            required = 3

        assert C.get_header() == "#one:two:three[:optional:arg:...]"

    def test_two_required_plus_restkey(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            required = 2

        assert C.get_header() == "#one:two[:rest:...]"

    def test_two_required_plus_restkey_format(self):
        class C(bulkparse.BulkParser):
            format = ('one', 'two')
            restkey = 'rest'
            restkey_format = 'thing=value'
            required = 2

        assert C.get_header() == "#one:two[:thing=value:...]"
