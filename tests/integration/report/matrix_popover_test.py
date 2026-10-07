"""Tests for the htmx popover fragments in the subnet matrix"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Prefix, Vlan

UNSAFE_NET_IDENT = "<script>alert('netident')</script>"


class TestMatrixPopover:
    def test_when_prefix_is_ipv4_it_should_show_usage_and_links(
        self, client, ipv4_prefix
    ):
        response = client.get(popover_url(ipv4_prefix), HTTP_HX_REQUEST="true")
        content = smart_str(response.content)

        assert response.status_code == 200
        assert "<h5>192.0.2.0/24</h5>" in content
        assert "(of max 254)" in content
        assert "Usage: 0.0%" in content
        assert "VLAN: 42" in content
        assert reverse('vlan-details', args=[ipv4_prefix.vlan.pk]) in content
        assert 'data-sparkline-url="' in content

    def test_when_prefix_is_ipv6_it_should_not_show_max_or_usage(
        self, client, ipv6_prefix
    ):
        response = client.get(popover_url(ipv6_prefix), HTTP_HX_REQUEST="true")
        content = smart_str(response.content)

        assert response.status_code == 200
        assert "<h5>2001:db8::/64</h5>" in content
        assert "of max" not in content
        assert "Usage:" not in content

    def test_it_should_render_only_the_popover_partial(self, client, ipv4_prefix):
        response = client.get(popover_url(ipv4_prefix), HTTP_HX_REQUEST="true")
        content = smart_str(response.content)

        assert "subnet-matrix" not in content
        assert "<html" not in content

    def test_given_net_ident_with_html_it_should_escape_it(self, client, ipv4_prefix):
        response = client.get(popover_url(ipv4_prefix), HTTP_HX_REQUEST="true")
        content = smart_str(response.content)

        assert UNSAFE_NET_IDENT not in content
        assert "&lt;script&gt;" in content

    def test_given_unknown_prefix_it_should_return_404(self, client, db):
        url = reverse('report-matrix-popover', args=[999999])
        response = client.get(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 404

    def test_given_too_small_prefix_it_should_return_404(self, client, small_prefix):
        response = client.get(popover_url(small_prefix), HTTP_HX_REQUEST="true")

        assert response.status_code == 404

    def test_given_anonymous_user_it_should_deny_access(self, ipv4_prefix):
        response = Client().get(popover_url(ipv4_prefix), HTTP_HX_REQUEST="true")

        assert response.status_code == 401


class TestMatrixPage:
    def test_given_scope_with_subnet_it_should_render_popover_trigger(
        self, client, scope_with_subnet
    ):
        scope, subnet = scope_with_subnet
        url = reverse('report-matrix-scope', args=[scope.net_address])
        response = client.get(url)
        content = smart_str(response.content)

        assert response.status_code == 200
        assert f'hx-get="{popover_url(subnet)}"' in content


def popover_url(prefix):
    return reverse('report-matrix-popover', args=[prefix.pk])


@pytest.fixture
def vlan(db):
    vlan = Vlan(vlan=42, net_type_id='lan', net_ident=UNSAFE_NET_IDENT)
    vlan.save()
    return vlan


@pytest.fixture
def ipv4_prefix(vlan):
    prefix = Prefix(net_address='192.0.2.0/24', vlan=vlan)
    prefix.save()
    return prefix


@pytest.fixture
def ipv6_prefix(vlan):
    prefix = Prefix(net_address='2001:db8::/64', vlan=vlan)
    prefix.save()
    return prefix


@pytest.fixture
def small_prefix(vlan):
    prefix = Prefix(net_address='192.0.2.4/31', vlan=vlan)
    prefix.save()
    return prefix


@pytest.fixture
def scope_with_subnet():
    # The matrix page reads prefixes through a legacy database connection, which
    # cannot see rows from the transaction of the db fixture
    scope_vlan = Vlan(net_type_id='scope', net_ident='matrix_scope')
    scope_vlan.save()
    scope = Prefix(net_address='198.51.0.0/16', vlan=scope_vlan)
    scope.save()
    subnet_vlan = Vlan(vlan=43, net_type_id='lan', net_ident='matrix_subnet')
    subnet_vlan.save()
    subnet = Prefix(net_address='198.51.100.0/24', vlan=subnet_vlan)
    subnet.save()
    yield scope, subnet
    scope_vlan.delete()
    subnet_vlan.delete()
