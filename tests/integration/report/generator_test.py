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
