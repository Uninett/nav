import pytest
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Interface


class TestPortadminSearchViews:
    """Combined tests for all search view types"""

    @pytest.mark.parametrize(
        "url_name,fixture_attr,expected_status",
        [
            ("portadmin-interface", "interface.id", 200),
            ("portadmin-sysname", "configured_netbox.sysname", 200),
            ("portadmin-ip", "configured_netbox.ip", 200),
        ],
    )
    def test_when_resource_exists_then_return_200(
        self, client, request, url_name, fixture_attr, expected_status
    ):
        fixture_name, attr = fixture_attr.split('.')
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "url_name,arg,expected_error",
        [
            ("portadmin-interface", 9999, "Could not find interface"),
            ("portadmin-sysname", "nonexistent", "Could not find IP device"),
            ("portadmin-ip", "123.5.6.12", "Could not find IP device"),
        ],
    )
    def test_when_resource_does_not_exist_then_return_error(
        self, client, url_name, arg, expected_error
    ):
        url = reverse(url_name, args=[arg])
        response = client.get(url)
        assert expected_error in smart_str(response.content)

    @pytest.mark.parametrize(
        "url_name,fixture_name,attr_name",
        [
            ("portadmin-interface", "interface", "id"),
            ("portadmin-sysname", "configured_netbox", "sysname"),
            ("portadmin-ip", "configured_netbox", "ip"),
        ],
    )
    def test_when_resource_exists_then_return_correct_data_url(
        self, client, request, url_name, fixture_name, attr_name
    ):
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr_name)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        expected_url = reverse(url_name + '-data', args=[value])

        assert response.status_code == 200
        assert f'hx-get="{expected_url}"' in smart_str(response.content)

    @pytest.mark.parametrize(
        "url_name,fixture_name,attr_name,expected_error",
        [
            (
                "portadmin-sysname",
                "netbox_without_type",
                "sysname",
                "IP device found but has no type",
            ),
            (
                "portadmin-ip",
                "netbox_without_type",
                "ip",
                "IP device found but has no type",
            ),
            (
                "portadmin-sysname",
                "netbox_with_type",
                "sysname",
                "IP device has no ports",
            ),
            ("portadmin-ip", "netbox_with_type", "ip", "IP device has no ports"),
        ],
    )
    def test_netbox_error_conditions(
        self, client, request, url_name, fixture_name, attr_name, expected_error
    ):
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr_name)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        assert expected_error in smart_str(response.content)


# Keep your existing fixtures as they are
@pytest.fixture
def netbox_with_type(localhost, netbox_type):
    localhost.type = netbox_type
    localhost.save()
    yield localhost
    localhost.type = None
    localhost.save()


@pytest.fixture
def interface(netbox_with_type):
    interface = create_interface(netbox_with_type)
    interface.save()
    yield interface
    interface.delete()


@pytest.fixture
def configured_netbox(netbox_with_type):
    new_interface = create_interface(netbox_with_type)
    yield netbox_with_type
    new_interface.delete()


@pytest.fixture
def netbox_without_type(configured_netbox):
    configured_netbox.type = None
    configured_netbox.save()
    yield configured_netbox


def create_interface(netbox):
    interface = Interface(
        netbox=netbox,
        ifname='GigabitEthernet0/1',
        ifalias='Test Interface',
        ifindex=1,
        iftype=6,
        baseport=1,
    )
    interface.save()
    return interface
