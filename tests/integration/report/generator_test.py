# -*- coding: utf-8 -*-
"""
Test report generators for basic errors.

These tests simply enumerate all known reports and ensure that the dbresult is
error free. This only ensures that the SQL can be run, no further verification
is performed.
"""

import pytest

from django.http import QueryDict
from django.urls import reverse

from nav import db
from nav.report.generator import ReportList, Generator
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


@pytest.mark.django_db
def test_when_concurrent_reports_then_no_connection_leaks():
    """Verify concurrent report generation uses connection pooling correctly"""
    import threading
    from django.db import connection

    # Track connection count before test
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE application_name LIKE '%NAV%'"
        )
        initial = cursor.fetchone()[0]

    errors = []

    def run_report():
        try:
            generator = Generator()
            uri = QueryDict('').copy()
            # Use a simple report that should exist
            result = generator.make_report(
                'netbox',
                list_config_files_from_dir(config_files_dir),
                uri,
                None,
                None,
            )
            # Verify report generated successfully
            assert result[6] is not None, "dbresult should not be None"
            assert not result[6].error, f"Report error: {result[6].error}"
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))

    # Run 20 concurrent report generations
    threads = [threading.Thread(target=run_report) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Check for errors during concurrent execution
    assert not errors, f"Concurrent access caused errors: {errors}"

    # Give Django time to return connections to pool
    import time

    time.sleep(1)

    # Check no significant connection leak (allow small variance for pooling)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE application_name LIKE '%NAV%'"
        )
        final = cursor.fetchone()[0]

    assert final - initial < 5, (
        f"Connection leak detected: {initial} connections -> {final} connections"
    )
