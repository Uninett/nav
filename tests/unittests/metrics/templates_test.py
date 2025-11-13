import pytest

from nav.metrics.names import safe_name
from nav.metrics.templates import metric_path_for_dhcp

@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            dict(
                allocation_type="range",
                ip_version=4,
                server_name="foo",
                group_name="bar",
                group_name_source="custom_groups",
                first_ip="192.0.2.0",
                last_ip="192.0.2.9",
                metric_name="baz",
            ),
            "nav.dhcp.4.foo.range.custom_groups.bar.192_0_2_0.192_0_2_9.baz",
        ),
        (
            dict(
                allocation_type="range",
                ip_version=4,
                server_name="foo",
                group_name="bar",
                group_name_source="custom_groups",
                first_ip=safe_name("192.0.2.0"),
                last_ip=safe_name("192.0.2.9"),
                metric_name="baz",
            ),
            "nav.dhcp.4.foo.range.custom_groups.bar.192.0.2.0.192.0.2.9.baz",
        ),
        (
            dict(
                allocation_type="range",
                ip_version=4,
                server_name="foo",
                group_name="bar",
                group_name_source="custom_groups",
                first_ip="*",
                last_ip="*",
                metric_name="baz",
            ),
            "nav.dhcp.4.foo.range.custom_groups.bar._._.baz",
        ),
        (
            dict(
                allocation_type="range",
                ip_version=4,
                server_name="foo",
                group_name="bar",
                group_name_source="custom_groups",
                first_ip=safe_name("*"),
                last_ip=safe_name("*"),
                metric_name="baz",
            ),
            "nav.dhcp.4.foo.range.custom_groups.bar.*.*.baz",
        ),
        (
            dict(
                allocation_type="range*",
                ip_version="4!",
                server_name="foo?",
                group_name="bar{",
                group_name_source="special_groups}",
                first_ip="*_*_0_0",
                last_ip="*.*.0.1",
                metric_name="baz baz!",
            ),
            "nav.dhcp.4_.foo_.range_.special_groups_.bar_.____0_0.____0_1.baz_baz_",
        ),
        (
            dict(
                allocation_type=safe_name("range*"),
                ip_version=safe_name("4!"),
                server_name=safe_name("foo?"),
                group_name=safe_name("bar{"),
                group_name_source=safe_name("special_groups}"),
                first_ip=safe_name("*_*_0_0"),
                last_ip=safe_name("*.*.0.1"),
                metric_name=safe_name("baz baz!"),
            ),
            "nav.dhcp.4!.foo?.range*.special_groups}.bar{.*_*_0_0.*.*.0.1.baz baz!",
        ),
    ]
)
def test_metric_path_for_dhcp(test_input, expected):
    assert metric_path_for_dhcp(**test_input) == expected
