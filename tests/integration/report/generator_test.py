# -*- coding: utf-8 -*-
"""Integration tests for the report generator.

`test_report` enumerates all known reports and checks that each one runs
without error. The rest check how malicious or awkward requests are handled,
which needs a live connection because identifier quoting is done by the driver.
"""

import pytest

from django.http import QueryDict
from django.urls import reverse

from nav import db
from nav.report.generator import ArgumentParser, Generator, ReportConfig, ReportList
from nav.config import find_config_dir, list_config_files_from_dir

from os.path import join

config_files_dir = join(find_config_dir() or "", "report", "report.conf.d/")


def report_list():
    result = ReportList(list_config_files_from_dir(config_files_dir))
    return [report.id for report in result.reports]


@pytest.mark.parametrize("report_name", report_list())
def test_report(report_name):
    # uri = 'http://example.com/report/%s/' % report_name
    uri = QueryDict('').copy()
    db.closeConnections()  # Ensure clean connection for each test

    generator = Generator()
    report, contents, neg, operator, adv, config, dbresult = generator.make_report(
        report_name, list_config_files_from_dir(config_files_dir), uri, None, None
    )

    assert dbresult, 'dbresult is None'
    assert not dbresult.error, dbresult.error + '\n' + dbresult.sql


def test_non_ascii_filter_should_work(client):
    url = reverse('report-by-name', kwargs={'report_name': 'room'})
    url = "{}?roomid=æøå".format(url)
    response = client.get(url, follow=True)
    assert response.status_code == 200


def test_when_order_by_is_injected_then_report_should_error_not_execute():
    """Use a sort token that only fails once it is quoted.

    "(SELECT 1)" is a valid ORDER BY term, so vulnerable code runs the query
    without error. The fix quotes it as a column name, which does not exist.
    """
    query = QueryDict(mutable=True)
    query["order_by"] = "(SELECT 1)"
    dbresult = run_report("room", query)
    assert dbresult.error
    assert "does not exist" in dbresult.error


def test_when_filter_field_is_injected_then_report_should_error_not_execute():
    """Use a filter field that only fails once it is quoted.

    On vulnerable code the field "'x'" gives "'x' = %s", which is valid SQL.
    The fix quotes it as a column name, which does not exist.
    """
    query = QueryDict(mutable=True)
    query["'x'"] = "x"
    dbresult = run_report("room", query)
    assert dbresult.error
    assert "does not exist" in dbresult.error


def test_when_filter_field_has_a_percent_then_report_should_error_not_crash():
    """A % in a field name must give a handled error, not an HTTP 500.

    An unescaped % reached psycopg2's parameter interpolation and raised an
    exception. With % doubled, the query fails with "column does not exist".
    """
    query = QueryDict(mutable=True)
    query["sysname%s"] = "x"
    dbresult = run_report("room", query)
    assert dbresult.error
    assert "does not exist" in dbresult.error


class TestMakeSqlQuotesUntrustedIdentifiers:
    def test_when_filter_field_is_malicious_then_make_sql_should_quote_it(self):
        sql = build_sql({"(SELECT 1 FROM pg_sleep(3)) OR sysname": "x"})
        assert '"(SELECT 1 FROM pg_sleep(3)) OR sysname" = %s' in sql

    def test_when_filter_field_has_a_quote_then_make_sql_should_double_it(self):
        sql = build_sql({'x"y': "v"})
        assert '"x""y" = %s' in sql

    def test_when_filter_field_has_a_percent_then_make_sql_should_double_it(self):
        sql = build_sql({"a%s": "v"})
        assert '"a%%s" = %s' in sql

    @pytest.mark.parametrize(
        "query, expected",
        [
            ({"op_x": "in", "x": "a*,b*"}, '("x" ilike %s or "x" ilike %s)'),
            ({"op_x": "between", "x": "1,2"}, '"x" between %s and %s'),
            ({"x": "null"}, '"x" is %s'),
            ({"x": "null", "not_x": "1"}, '"x" is not %s'),
        ],
    )
    def test_when_operator_builds_a_clause_then_make_sql_should_quote_every_field(
        self, query, expected
    ):
        assert expected in build_sql(query)

    def test_when_order_by_is_malicious_then_make_sql_should_quote_the_token(self):
        sql = build_sql({"order_by": "sysname,(SELECT 1)"})
        assert 'ORDER BY "sysname","(SELECT 1)"' in sql

    def test_when_order_by_is_descending_then_make_sql_should_quote_and_add_desc(self):
        sql = build_sql({"order_by": "-sysname"})
        assert 'ORDER BY "sysname" DESC' in sql

    def test_when_order_by_has_whitespace_then_make_sql_should_strip_the_token(self):
        sql = build_sql({"order_by": "sysname, ifindex"})
        assert 'ORDER BY "sysname","ifindex"' in sql


class TestMakeSqlRendersTrustedClauses:
    def test_when_config_defines_a_sort_expression_then_make_sql_should_pass_it_verbatim(  # noqa: E501
        self,
    ):
        sql = build_sql({}, trusted_sort=["priority DESC"])
        assert "ORDER BY priority DESC" in sql

    def test_when_config_defines_a_where_clause_then_make_sql_should_pass_it_verbatim(
        self,
    ):
        sql = build_sql({}, trusted_where="descr='cats as pets'")
        assert "WHERE descr='cats as pets'" in sql


def build_sql(query, trusted_sort=None, trusted_where=None):
    config = ReportConfig()
    config.sql = "SELECT sysname FROM netbox"
    if trusted_sort:
        config.add_trusted_sort(trusted_sort)
    if trusted_where:
        config.add_trusted_where(trusted_where)
    ArgumentParser(config).parse_query(query)
    return config.make_sql(db.getConnection("default"))[0]


def run_report(report_name, query):
    config_files = list_config_files_from_dir(config_files_dir)
    try:
        db.closeConnections()  # start each test from a clean connection
        result = Generator().make_report(report_name, config_files, query, None, None)
        return result[6]  # the DatabaseResult
    finally:
        # The injection tests deliberately error, which aborts the legacy
        # connection's transaction. Discard it so later tests get a clean one.
        db.closeConnections()
