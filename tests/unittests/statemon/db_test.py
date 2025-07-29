# Copyright (C) 2020 Universitetet i Oslo
# ruff: noqa E501

from nav.statemon.db import db
from unittest import TestCase


class DBTestcase(TestCase):
    def test_build_host_query(self):
        db_instance = db()

        # Make groups
        groups_included = ["INC_GROUP_ONE", "INC_GROUP_TWO"]
        groups_excluded = ["EXC_GROUP_ONE", "EXC_GROUP_TWO"]

        # Make query string for both groups
        query_both_groups = """SELECT distinct(netbox.netboxid), sysname, ip, up FROM netbox
                   LEFT JOIN netboxcategory USING (netboxid) WHERE netboxcategory.category IN %s AND (netboxcategory.category IS NULL OR netboxcategory.category NOT IN %s)"""

        # make query string for only included groups
        query_included_groups = """SELECT distinct(netbox.netboxid), sysname, ip, up FROM netbox
                   LEFT JOIN netboxcategory USING (netboxid) WHERE netboxcategory.category IN %s"""

        # make query string for only excluded groups
        query_excluded_groups = """SELECT distinct(netbox.netboxid), sysname, ip, up FROM netbox
                   LEFT JOIN netboxcategory USING (netboxid) WHERE (netboxcategory.category IS NULL OR netboxcategory.category NOT IN %s)"""

        # make query string for no groups
        query_no_groups = """SELECT distinct(netbox.netboxid), sysname, ip, up FROM netbox
                   LEFT JOIN netboxcategory USING (netboxid)"""

        # Both Groups Checks
        query, params = db_instance.build_host_query(
            groups_included=groups_included, groups_excluded=groups_excluded
        )
        # Check if the params of the query are correct
        self.assertListEqual(params, [tuple(groups_included), tuple(groups_excluded)])
        # Check the query string is correct
        self.assertEqual(query, query_both_groups)

        # Included Groups Checks
        query, params = db_instance.build_host_query(groups_included=groups_included)
        # Check if the params of the query are correct
        self.assertListEqual(params, [tuple(groups_included)])
        # Check the query string is correct
        self.assertEqual(query, query_included_groups)

        # Excluded Groups Checks
        query, params = db_instance.build_host_query(groups_excluded=groups_excluded)
        # Check if the params of the query are correct
        self.assertListEqual(params, [tuple(groups_excluded)])
        # Check the query string is correct
        self.assertEqual(query, query_excluded_groups)

        # No Groups Checks
        query, params = db_instance.build_host_query()
        # Check if the params of the query are correct
        self.assertListEqual(params, [])
        # Check the query string is correct
        self.assertEqual(query, query_no_groups)
