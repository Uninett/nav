from dataclasses import dataclass

import IPy
import pytest

from nav.dhcpstats.common import DhcpPath
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
