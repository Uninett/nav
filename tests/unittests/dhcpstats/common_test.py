from dataclasses import dataclass, replace
from itertools import chain
import logging
import random
import re

import IPy
import pytest

from nav.dhcpstats.common import (
    DhcpPath,
    drop_groups_not_in_prefixes,
    fetch_paths_from_graphite,
    group_paths,
    range_str,
)
from nav.metrics.templates import metric_path_for_dhcp


@dataclass
class Path:
    native: DhcpPath
    graphite: str


@pytest.fixture(
    params=[
        Path(
            DhcpPath(
                ip_version=4,
                server_name="server1",
                allocation_type="range",
                group_name="group1",
                group_name_source="custom_groups",
                first_ip=IPy.IP("192.0.0.1"),
                last_ip=IPy.IP("192.0.0.255"),
            ),
            "nav.dhcp.servers.server1.range.custom_groups.group1.4.192_0_0_1.192_0_0_255",
        ),
        Path(
            DhcpPath(
                ip_version=6,
                server_name="server1",
                allocation_type="range",
                group_name="group1",
                group_name_source="custom_groups",
                first_ip=IPy.IP("::1"),
                last_ip=IPy.IP("::ffff"),
            ),
            "nav.dhcp.servers.server1.range.custom_groups.group1.6.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
        ),
        Path(
            DhcpPath(
                ip_version=6,
                server_name="server1",
                allocation_type="range",
                group_name="standalone",
                group_name_source="special_groups",
                first_ip=IPy.IP("::1"),
                last_ip=IPy.IP("::ffff"),
            ),
            "nav.dhcp.servers.server1.range.special_groups.standalone.6.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
        ),
    ]
)
def path(request):
    return request.param


class TestDhcpPath:
    def test_to_graphite_path_should_return_expected_value(self, path):
        assert path.native.to_graphite_path(metric_name="foo") == path.graphite + ".foo"

    def test_to_graphite_path_should_be_reversed_by_from_graphite_path(self, path):
        assert (
            DhcpPath.from_graphite_path(path.native.to_graphite_path(metric_name="foo"))
            == path.native
        )

    def test_from_graphite_path_should_be_reversed_by_to_graphite_path(self, path):
        assert (
            DhcpPath.from_graphite_path(path.graphite).to_graphite_path(
                metric_name="foo"
            )
            == path.graphite + ".foo"
        )

    @pytest.mark.parametrize(
        "graphite_path",
        [
            "nav.dhcp.servers.server1.range.custom_groups.group1.6.0_0_0_1.0_0_0_255",
            "nav.dhcp.servers.server1.range.custom_groups.group1.4.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
            "nav.dhcp.servers.server1.range.custom_groups.group1.6.0_0_0_1.0_0_0_0_0_0_0_ffff",
            "nav.dhcp.servers.server1.range.custom_groups.group1.6.0_0_0_0_0_0_0_1.0_0_0_255",
        ],
    )
    def test_from_graphite_path_should_fail_on_ip_version_mismatch(self, graphite_path):
        with pytest.raises(ValueError):
            DhcpPath.from_graphite_path(graphite_path)

    @pytest.mark.parametrize(
        "graphite_path,reason",
        [
            (
                "nav.dhcp.servers.server1.range.custom_groups.group1.6.0_0_0_0_0_0_0_1",
                "missing <last_ip> segment",
            ),
            (
                "nav.dhcp.servers.server1.range.invalid.group1.6.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
                "invalid <group_name_source> segment",
            ),
            (
                "nav.dhcp.servers.server1.invalid.custom_groups.group1.6.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
                "invalid <allocation_type> segment",
            ),
            (
                "nav.dhcp.servers.server1.range.custom_groups.group1.invalid.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_ffff",
                "invalid <ip_version> segment",
            ),
        ],
    )
    def test_from_graphite_path_should_fail_on_invalid_names(
        self, graphite_path, reason
    ):
        with pytest.raises(ValueError):
            DhcpPath.from_graphite_path(graphite_path)
            pytest.fail(f"Didn't fail when {reason!r}")

    def test_from_graphite_path_should_work_with_metric_path_for_dhcp(self):
        path_kwargs = {
            "ip_version": 4,
            "server_name": "server1",
            "allocation_type": "range",
            "group_name_source": "custom_groups",
            "group_name": "group1",
            "first_ip": IPy.IP("192.0.0.1"),
            "last_ip": IPy.IP("192.0.0.255"),
        }
        assert DhcpPath.from_graphite_path(
            metric_path_for_dhcp(metric_name="foo", **path_kwargs)
        ) == DhcpPath(**path_kwargs)
        assert DhcpPath.from_graphite_path(
            metric_path_for_dhcp(metric_name="foo", **path_kwargs)
        ).to_graphite_path(metric_name="foo") == metric_path_for_dhcp(
            metric_name="foo", **path_kwargs
        )

    @pytest.mark.parametrize(
        "server_name,allocation_type,group_name,first_ip,last_ip,expected",
        [
            (
                "server1",
                "range",
                "group1",
                "192.0.0.1",
                "192.0.0.255",
                DhcpPath(
                    ip_version=4,
                    server_name="server1",
                    allocation_type="range",
                    group_name="group1",
                    group_name_source="custom_groups",
                    first_ip=IPy.IP("192.0.0.1"),
                    last_ip=IPy.IP("192.0.0.255"),
                ),
            ),
            (
                "server1",
                "subnet",
                None,
                "0.0.0.0",
                "255.255.255.255",
                DhcpPath(
                    ip_version=4,
                    server_name="server1",
                    allocation_type="subnet",
                    group_name="standalone",
                    group_name_source="special_groups",
                    first_ip=IPy.IP("0.0.0.0"),
                    last_ip=IPy.IP("255.255.255.255"),
                ),
            ),
            (
                "server2",
                "pool",
                "group2",
                "::1",
                "::ffff",
                DhcpPath(
                    ip_version=6,
                    server_name="server2",
                    allocation_type="pool",
                    group_name="group2",
                    group_name_source="custom_groups",
                    first_ip=IPy.IP("::1"),
                    last_ip=IPy.IP("::ffff"),
                ),
            ),
        ],
    )
    def test_from_external_info_should_work_when_given_valid_arguments(
        self, server_name, allocation_type, group_name, first_ip, last_ip, expected
    ):
        assert (
            DhcpPath.from_external_info(
                server_name, allocation_type, group_name, first_ip, last_ip
            )
            == expected
        )

    @pytest.mark.parametrize(
        "server_name,allocation_type,group_name,first_ip,last_ip,reason",
        [
            (
                "server1",
                "range",
                "group1",
                "::1",
                "0.0.0.255",
                "first_ip being IPv6 and last_ip being IPv4",
            ),
            (
                "server1",
                "range",
                "group1",
                "0.0.0.1",
                "::ffff",
                "first_ip being IPv4 and last_ip being IPv6",
            ),
            (
                "server1",
                "range",
                "192.0.0.1",
                "192.0.0.255",
                "group1",
                "last_ip being an invalid IP address",
            ),
            (
                "server1",
                "range",
                "group1",
                "192.0.0.255",
                "192.0.0.1",
                "first_ip being a greater IP address than last_ip",
            ),
            (
                "server2",
                "pool",
                "group2",
                "::1:",
                "::ffff",
                "first_ip being an invalid IP address",
            ),
            (
                "server2",
                "pool",
                "group2",
                "::1",
                "::fffff",
                "last_ip being an invalid IP address",
            ),
            (
                "server2",
                "pool",
                "group2",
                "::1",
                "::ffff:",
                "last_ip being an invalid IP address",
            ),
        ],
    )
    def test_from_external_info_should_fail_when_given_invalid_arguments(
        self, server_name, allocation_type, group_name, first_ip, last_ip, reason
    ):
        # We skip checking for errors that should be caught by a static type
        # checker such as invalid argument types
        with pytest.raises(ValueError):
            DhcpPath.from_external_info(
                server_name, allocation_type, group_name, first_ip, last_ip
            )
            pytest.fail(f"Didn't fail when {reason!r}")


def test_group_paths_should_group_special_standalone_groups_paths_individually():
    path0 = DhcpPath(
        ip_version=6,
        server_name="server1",
        allocation_type="range",
        group_name="standalone",
        group_name_source="special_groups",
        first_ip=IPy.IP("::0:1"),
        last_ip=IPy.IP("::0:ffff"),
    )
    path1 = replace(path0, first_ip=IPy.IP("::1:1"), last_ip=IPy.IP("::1:ffff"))
    path2 = replace(path0, first_ip=IPy.IP("::2:1"), last_ip=IPy.IP("::2:ffff"))
    assert sorted(group_paths([path0, path1, path2])) == sorted(
        [[path0], [path1], [path2]]
    )


def test_group_paths_should_group_special_groups_paths_separately_from_custom_groups_paths():  # noqa: E501
    path0 = DhcpPath(
        ip_version=6,
        server_name="server1",
        allocation_type="range",
        group_name="standalone",
        group_name_source="special_groups",
        first_ip=IPy.IP("::0:1"),
        last_ip=IPy.IP("::0:ffff"),
    )
    path1 = replace(path0, first_ip=IPy.IP("::1:1"), last_ip=IPy.IP("::1:ffff"))
    path2 = replace(
        path0,
        first_ip=IPy.IP("::2:1"),
        last_ip=IPy.IP("::2:ffff"),
        group_name_source="custom_groups",
    )
    path3 = replace(
        path0,
        first_ip=IPy.IP("::3:1"),
        last_ip=IPy.IP("::3:ffff"),
        group_name_source="custom_groups",
    )
    assert sorted(group_paths([path0, path1, path2, path3])) == sorted(
        [[path0], [path1], [path2, path3]]
    )


def test_group_paths_should_group_custom_groups_paths_together_when_only_ip_addresses_differ():  # noqa: E501
    path0 = DhcpPath(
        ip_version=6,
        server_name="server1",
        allocation_type="range",
        group_name="group1",
        group_name_source="custom_groups",
        first_ip=IPy.IP("::0:1"),
        last_ip=IPy.IP("::0:ffff"),
    )
    path1 = replace(path0, first_ip=IPy.IP("::1:1"), last_ip=IPy.IP("::1:ffff"))
    path2 = replace(
        path0,
        first_ip=IPy.IP("::2:1"),
        last_ip=IPy.IP("::2:ffff"),
        group_name="different",
    )
    path3 = replace(
        path0,
        first_ip=IPy.IP("::3:1"),
        last_ip=IPy.IP("::3:ffff"),
        allocation_type="pool",
    )
    path4 = replace(
        path0,
        first_ip=IPy.IP("::4:1"),
        last_ip=IPy.IP("::4:ffff"),
        server_name="different",
    )
    path5 = replace(
        path0, first_ip=IPy.IP("0.0.5.1"), last_ip=IPy.IP("0.0.5.255"), ip_version=4
    )
    assert sorted(group_paths([path0, path1, path2, path3, path4, path5])) == sorted(
        [[path0, path1], [path2], [path3], [path4], [path5]]
    )


def test_group_paths_should_group_custom_groups_paths_separately_when_other_than_ip_addresses_differ():  # noqa: E501
    path0 = DhcpPath(
        ip_version=6,
        server_name="server1",
        allocation_type="range",
        group_name="group1",
        group_name_source="custom_groups",
        first_ip=IPy.IP("::1"),
        last_ip=IPy.IP("::ff"),
    )
    path1 = replace(path0, group_name="different")
    path2 = replace(path0, server_name="different")
    path3 = replace(path0, allocation_type="subnet")
    path4 = replace(
        path0, first_ip=IPy.IP("0.0.0.1"), last_ip=IPy.IP("0.0.0.255"), ip_version=4
    )
    assert sorted(group_paths([path0, path1, path2, path3, path4])) == sorted(
        [[path0], [path1], [path2], [path3], [path4]]
    )


@pytest.mark.parametrize(
    "prefixes,test_input,expected_output",
    [
        (
            [IPy.IP("0.0.0.0/0")],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group3.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group1.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Inside  # noqa: E501
            ],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group3.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group1.4.1_1_100_0.1_1_101_0.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Inside  # noqa: E501
            ],
        ),
        (
            [IPy.IP("1.1.252.0/24"), IPy.IP("1.1.253.0/24")],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Another path in the group is inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Another path in the group is inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group3.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group1.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Partially Inside  # noqa: E501
            ],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Another path in the group is inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Another path in the group inside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Partially Inside  # noqa: E501
            ],
        ),
        (
            [IPy.IP("1.1.252.0/24")],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group3.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group1.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Partially Inside  # noqa: E501
            ],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Inside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Partially Inside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Partially Inside  # noqa: E501
            ],
        ),
        (
            [],
            [
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_0.1_1_252_12.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group1.4.1_1_252_64.1_1_252_127.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_253_1.1_1_253_8.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group2.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server1.range.custom_groups.group3.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group1.4.1_1_100_0.1_1_101_0.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group2.4.1_1_254_0.1_1_254_15.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server2.range.custom_groups.group3.4.1_1_253_1.1_1_253_8.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server3.range.custom_groups.group1.4.1_1_250_1.1_1_255_1.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server4.range.custom_groups.group1.4.1_1_253_1.1_1_255_1.foo",  # Outside  # noqa: E501
                "nav.dhcp.servers.server5.range.custom_groups.group1.4.1_1_250_1.1_1_253_1.foo",  # Outside  # noqa: E501
            ],
            [],
        ),
    ],
)
def test_drop_groups_not_in_prefixes_should_work_as_expected(
    prefixes, test_input, expected_output
):
    native_paths = [DhcpPath.from_graphite_path(path) for path in test_input]
    grouped_paths = group_paths(native_paths)
    remaining_grouped_paths = drop_groups_not_in_prefixes(grouped_paths, prefixes)
    remaining_graphite_paths = [
        path.to_graphite_path("foo")
        for path in chain.from_iterable(remaining_grouped_paths)
    ]
    assert sorted(remaining_graphite_paths) == sorted(expected_output)


@pytest.mark.parametrize(
    "path,log_pattern",
    [
        (
            "nav.dhcp.servers.kea-trd.range.custom_groups.staff.4.193_0_2_1.192_0_2_16",
            r"first_ip.{0,10}193\.0\.2\.1.{0,10}greater than.{0,10}last_ip.{0,10}192\.0\.2\.16",  # noqa: E501
        ),
        (
            "nav.dhcp.servers.kea-trd.Range.custom_groups.staff.4.192_0_2_1.192_0_2_16",
            r"allocation_type.{0,10}Range.{0,10}is not in.{0,30}range",
        ),
        (
            "nav.dhcp.servers.kea-trd.range.Custom_groups.staff.4.192_0_2_1.192_0_2_16",
            r"group_source_name.{0,10}Custom_groups.{0,10}is not.{0,50}custom_groups",
        ),
        (
            "nav.dhcp.servers.kea-trd.range.custom_groups.staff.6.192_0_2_1.192_0_2_16",
            r"expected ip_version.{0,3}6",
        ),
        (
            "nav.dhcp.servers.kea-trd.range.custom_groups.staff.6.0_0_0_0_c0_0_2_1.192_0_2_16",
            r"expected ip_version.{0,3}6|first_ip.{0,10}c0:0:2:1.{0,10}not.{0,10}same version as last_ip.{0,10}192\.0\.2\.16",  # noqa: E501
        ),
        (
            "nav.dhcp.servers.kea-trd.range.custom_groups.staff.6.192_0_2_1.0_0_0_0_c0_0_2_10",
            r"expected ip_version.{0,3}6|first_ip.{0,10}192\.0\.2\.1.{0,10}not.{0,10}same version as last_ip.{0,10}c0:0:2:10",  # noqa: E501
        ),
        (
            "dhcp.servers.kea-trd.range.custom_groups.staff.4.192_0_2_1.192_0_2_16",
            r"expected.{0,20}dhcp\.servers\.kea-trd\.range\.custom_groups\.staff\.4\.192_0_2_1\.192_0_2_16.{0,20}to have.{0,20}10.{0,20}segments",  # noqa: E501
        ),
    ],
)
def test_fetch_paths_from_graphite_should_warn_when_paths_from_graphite_are_bad(
    path, log_pattern, caplog, monkeypatch
):
    monkeypatch.setattr(
        "nav.dhcpstats.common.get_expanded_nodes", lambda *args, **kwargs: [path]
    )
    with caplog.at_level(logging.WARNING):
        fetch_paths_from_graphite()
        assert re.search(log_pattern, caplog.text, flags=re.IGNORECASE)


def test_range_str_should_use_cidr_notation_when_possible():
    r = random.Random()
    r.seed(1, version=2)
    for totalbits, ipversion in ((32, 4), (128, 6)):
        for i in range(128):
            base = r.randint(0, 2**totalbits - 1)
            hostbits = i % totalbits + 1
            netbits = totalbits - hostbits
            netmask = ((2**totalbits - 1) << hostbits) & (2**totalbits - 1)
            net = IPy.IP(base & netmask, ipversion=ipversion).make_net(netbits)
            assert range_str(net[0], net[-1]) == f"{net[0]}/{netbits}"


def test_range_str_output_should_represent_inputs():
    r = random.Random()
    r.seed(2, version=2)
    for totalbits, ipversion in ((32, 4), (128, 6)):
        for _ in range(128):
            ip1 = IPy.IP(r.randint(0, 2**totalbits - 1), ipversion=ipversion)
            ip2 = IPy.IP(r.randint(0, 2**totalbits - 1), ipversion=ipversion)
            ip1, ip2 = min(ip1, ip2), max(ip1, ip2)
            output = range_str(ip1, ip2)
            if "-" in output:
                actual_ip1, _, actual_ip2 = output.partition("-")
                actual_ip1 = IPy.IP(actual_ip1)
                actual_ip2 = IPy.IP(actual_ip2)
            else:
                temp = IPy.IP(output)
                actual_ip1, actual_ip2 = temp[0], temp[-1]
            assert (actual_ip1, actual_ip2) == (ip1, ip2)


def test_range_str_output_should_be_a_single_address_when_inputs_are_equal():
    r = random.Random()
    r.seed(3, version=2)
    for totalbits, ipversion in ((32, 4), (128, 6)):
        for _ in range(128):
            ip = IPy.IP(r.randint(0, 2**totalbits - 1), ipversion=ipversion)
            assert range_str(ip, ip) == str(ip)
