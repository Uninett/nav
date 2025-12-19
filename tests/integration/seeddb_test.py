import io
from zipfile import ZipFile

from django.urls import reverse
from django.http import Http404
from django.test.client import RequestFactory
from mock import MagicMock

from django.utils.encoding import smart_str
from nav.models.manage import Interface, Netbox, NetboxInfo, Room
from nav.models.cabling import Cabling, Patch
from nav.web.auth.utils import set_account
from nav.web.seeddb.page.netbox.edit import netbox_edit, log_netbox_change
from nav.web.seeddb.utils.delete import dependencies

import pytest


@pytest.mark.parametrize(
    "endpoint",
    [
        'seeddb-room-edit',
        'seeddb-room-delete',
        'seeddb-location-edit',
        'seeddb-location-delete',
        'seeddb-organization-edit',
        'seeddb-organization-delete',
        'seeddb-usage-edit',
        'seeddb-usage-delete',
        'seeddb-netboxgroup-edit',
        'seeddb-netboxgroup-delete',
    ],
)
def test_urls_should_allow_name_with_slashes(db, endpoint):
    assert reverse(endpoint, args=("TEST/SLASH",))


def test_editing_deleted_netboxes_should_raise_404(admin_account):
    netboxid = 666  # Assuming no such netbox exists in test data set!
    factory = RequestFactory()
    url = reverse('seeddb-netbox-edit', args=(netboxid,))
    request = factory.get(url)
    request.session = MagicMock()
    set_account(request, admin_account, cycle_session_id=False)

    with pytest.raises(Http404):
        netbox_edit(request, netboxid)


def test_adding_netbox_with_invalid_ip_should_fail(db, client):
    url = reverse('seeddb-netbox-edit')
    ip = (
        "195.88.54.16'))) OR 2121=(SELECT COUNT(*) FROM GENERATE_SERIES(1,15000000)) "
        "AND ((('FRyc' LIKE 'FRyc"
    )

    response = client.post(
        url,
        follow=True,
        data={
            "ip": ip,
            "room": "myroom",
            "category": "GW",
            "organization": "myorg",
        },
    )

    assert response.status_code == 200
    assert 'Form was not valid' in smart_str(response.content)
    assert 'Could not resolve name' in smart_str(response.content)


def test_adding_netbox_with_invalid_profiles_should_fail(db, client):
    url = reverse('seeddb-netbox-edit')
    ip = "10.254.254.253"

    response = client.post(
        url,
        follow=True,
        data={
            "ip": ip,
            "room": "myroom",
            "category": "GW",
            "organization": "myorg",
            "profiles": "-5785')) ORDER BY 1-- qAPu",
        },
    )

    assert response.status_code == 200
    assert 'Form was not valid' in smart_str(response.content)
    assert not Netbox.objects.filter(ip=ip).exists()


@pytest.fixture()
def netbox(management_profile):
    box = Netbox(
        ip='10.254.254.254',
        sysname='downhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    yield box
    box.delete()


def test_dependencies(netbox):
    """Tests the related objects listed when deleting objects in seeddb"""
    qs = Room.objects.filter(pk='myroom')
    deps = dependencies(qs, [Netbox])
    assert 'myroom' in deps
    assert [netbox] == deps.get('myroom')


def test_dependencies_no_whitelist(netbox):
    """Tests the related objects listed when deleting objects in seeddb"""
    qs = Room.objects.filter(pk='myroom')
    deps = dependencies(qs, [])
    assert Netbox.objects.get(pk=netbox.pk)
    assert deps == {}


def test_log_netbox_change_should_not_crash(admin_account, netbox):
    """Regression test to ensure this function doesn't try to access removed or
    invalid attributes on Netbox.
    """
    old = Netbox.objects.get(id=netbox.id)
    new = netbox
    new.category_id = "OTHER"

    assert log_netbox_change(admin_account, old, new) is None


def test_empty_function_field_in_netbox_edit_form_should_delete_respective_netboxinfo_instance(  # noqa: E501
    netbox, db, client
):
    """
    Empty function fields in the webform should cause the function's
    corresponding NetboxInfo to be deleted; This is the correct thing
    to do because NAV prefills user forms with previously assigned
    values. Hence, if NAV receives a form with an empty function
    string, this means the user has explicitly cleared the function
    string.
    """
    url = reverse('seeddb-netbox-edit', args=(netbox.id,))

    def post(func):
        return client.post(
            url,
            follow=True,
            data={
                "ip": netbox.ip,
                "room": netbox.room_id,
                "category": netbox.category_id,
                "organization": netbox.organization_id,
                "function": func,
            },
        )

    assert len(NetboxInfo.objects.filter(netbox=netbox, variable='function')) == 0
    post("")
    assert len(NetboxInfo.objects.filter(netbox=netbox, variable='function')) == 0
    post("foo")
    assert (
        NetboxInfo.objects.filter(netbox=netbox, variable='function').get().value
        == 'foo'
    )
    post("")
    assert len(NetboxInfo.objects.filter(netbox=netbox, variable='function')) == 0


def test_generating_qr_codes_for_netboxes_should_succeed(client, netbox):
    url = reverse('seeddb-netbox')

    response = client.post(
        url,
        follow=True,
        data={
            "qr_code": "Generate+QR+codes+for+selected",
            "object": [netbox.id],
        },
    )

    # Check response headers
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert int(response.headers["Content-Length"]) > 0
    assert "attachment" in response.headers["Content-Disposition"]
    assert "qr_codes.zip" in response.headers["Content-Disposition"]

    # Check response content
    buf = io.BytesIO(b"".join(response.streaming_content))
    assert ZipFile(buf, "r").namelist() == [f"{netbox.sysname}.png"]


def test_generating_qr_codes_for_no_selected_netboxes_should_show_error(client, netbox):
    url = reverse('seeddb-netbox')

    response = client.post(
        url,
        follow=True,
        data={
            "qr_code": "Generate+QR+codes+for+selected",
        },
    )

    assert response.status_code == 200
    assert (
        'You need to select at least one object to generate QR codes for'
        in smart_str(response.content)
    )


def test_generating_qr_codes_for_rooms_should_succeed(client):
    url = reverse('seeddb-room')

    response = client.post(
        url,
        follow=True,
        data={
            "qr_code": "Generate+QR+codes+for+selected",
            "object": ["myroom"],
        },
    )

    # Check response headers
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert int(response.headers["Content-Length"]) > 0
    assert "attachment" in response.headers["Content-Disposition"]
    assert "qr_codes.zip" in response.headers["Content-Disposition"]

    # Check response content
    buf = io.BytesIO(b"".join(response.streaming_content))
    assert ZipFile(buf, "r").namelist() == ["myroom.png"]


def test_generating_qr_codes_for_no_selected_rooms_should_show_error(client, netbox):
    url = reverse('seeddb-room')

    response = client.post(
        url,
        follow=True,
        data={
            "qr_code": "Generate+QR+codes+for+selected",
        },
    )

    assert response.status_code == 200
    assert (
        'You need to select at least one object to generate QR codes for'
        in smart_str(response.content)
    )


class TestPatchModalViews:
    """Integration tests for showing add and remove patch modals"""

    def test_should_render_add_patch_modal(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=add'
        )
        response = client.get(url)
        assert response.status_code == 200
        assert 'Add patch' in smart_str(response.content)

    def test_add_patch_modal_should_include_interface_name(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=add'
        )
        response = client.get(url)
        assert interface.ifname in smart_str(response.content)
        assert interface.ifalias in smart_str(response.content)

    def test_add_patch_modal_should_include_interface_id(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=add'
        )
        response = client.get(url)
        assert f'value="{interface.id}"' in smart_str(response.content)

    def test_add_patch_modal_should_include_cable_search(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=add'
        )
        response = client.get(url)
        assert 'id="cable-search"' in smart_str(response.content)

    def test_add_patch_modal_should_include_cableid(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=add'
        )
        response = client.get(url)
        assert 'name="cableid"' in smart_str(response.content)

    def test_should_render_remove_patch_modal(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=remove'
        )
        response = client.get(url)
        assert response.status_code == 200
        assert 'Remove patch' in smart_str(response.content)

    def test_remove_patch_modal_should_include_interface_id(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=remove'
        )
        response = client.get(url)
        assert f'value="{interface.id}"' in smart_str(response.content)

    def test_remove_patch_modal_should_include_interface_name(self, client, interface):
        url = (
            reverse('seeddb-show-patch-modal')
            + f'?interfaceid={interface.id}&modal=remove'
        )
        response = client.get(url)
        assert interface.ifname in smart_str(response.content)
        assert interface.ifalias in smart_str(response.content)


class TestSavePatchView:
    """Integration tests for adding patches"""

    def test_given_valid_data_then_create_patch(self, client, interface, cable):
        url = reverse('seeddb-patch-save')
        data = {
            'interfaceid': interface.id,
            'cableid': cable.id,
        }
        response = client.post(url, data=data)
        assert response.status_code == 200
        assert Patch.objects.filter(interface=interface, cabling=cable).exists()

    def test_given_invalid_data_then_return_alert(self, client):
        url = reverse('seeddb-patch-save')
        data = {}
        response = client.post(url, data=data)
        assert 'patch-modal-alert' in smart_str(response.content)

    def test_given_valid_data_then_return_updated_patch_row(
        self, client, interface, cable
    ):
        url = reverse('seeddb-patch-save')
        data = {
            'interfaceid': interface.id,
            'cableid': cable.id,
        }
        response = client.post(url, data=data)
        assert response.status_code == 200
        assert f'tr data-interfaceid="{interface.pk}"' in smart_str(response.content)


class TestRemovePatchView:
    """Integration tests for removing patches"""

    def test_given_existing_patch_then_remove_from_interface(
        self, client, interface, cable
    ):
        # First create a patch to remove
        patch = Patch.objects.create(interface=interface, cabling=cable)

        url = reverse('seeddb-patch-remove')
        data = {
            'interfaceid': interface.id,
        }
        client.post(url, data=data)
        assert not Patch.objects.filter(id=patch.id).exists()

    def test_given_existing_patch_then_return_updated_patch_row(
        self, client, interface, cable
    ):
        Patch.objects.create(interface=interface, cabling=cable)

        url = reverse('seeddb-patch-remove')
        data = {
            'interfaceid': interface.id,
        }
        response = client.post(url, data=data)
        assert f'tr data-interfaceid="{interface.pk}"' in smart_str(response.content)

    # When removing a non-existing patch, the response should still be 200 OK
    # The test should return an updated patch row with an 'Add patch' button
    def test_given_non_existing_patch_then_return_add_patch_row(
        self, client, interface
    ):
        url = reverse('seeddb-patch-remove')
        data = {
            'interfaceid': interface.id,
        }
        response = client.post(url, data=data)
        assert f'tr data-interfaceid="{interface.pk}"' in smart_str(response.content)
        assert 'Add patch' in smart_str(response.content)


@pytest.fixture
def interface(localhost):
    """Create a test interface"""
    interface = Interface(
        netbox=localhost,
        ifname='GigabitEthernet0/1',
        ifalias='Test Interface',
        ifindex=1,
        iftype=6,
    )
    interface.save()
    yield interface
    interface.delete()


@pytest.fixture
def cable(localhost):
    """Create a test cable"""
    cable = Cabling(
        room=localhost.room,
        jack='sparrow',
        building='TestBuilding',
        target_room='TestTargetRoom',
        description='Test Cable',
    )
    cable.save()
    yield cable
    cable.delete()
