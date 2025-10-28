import pytest
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.arnold import Justification, QuarantineVlan
from nav.models.fields import INFINITY
from nav.models.manage import Cam, Device, Interface, Module, Netbox


class TestManualDetention:
    def test_search_for_valid_ip_should_not_crash(self, client):
        url = reverse('arnold-manual-detention')

        response = client.post(
            url,
            follow=True,
            data={
                'submit': 'Find',
                'target': '10.0.0.1',
            },  # any address will do
        )

        assert response.status_code == 200

    def test_given_netbox_without_read_write_profile_blocking_should_show_error(
        self, client, cam_entry
    ):
        qvlan = QuarantineVlan.objects.create(vlan=1, description='')
        justification = Justification.objects.create(name='justification')

        url = reverse("arnold-manual-detention-step-two", args=(cam_entry.mac,))

        response = client.post(
            url,
            follow=True,
            data={
                "camtuple": str(cam_entry.pk),
                "target": cam_entry.mac,
                "method": "disable",
                "qvlan": str(qvlan.pk),
                "justification": str(justification.pk),
                "submit": "Detain",
            },
        )

        assert response.status_code == 200
        assert (
            str(response.context.get("error"))
            == "example-sw.example.org has no read-write management profile"
        )

    def test_given_netbox_without_read_write_profile_quarantining_should_show_error(
        self, client, cam_entry
    ):
        qvlan = QuarantineVlan.objects.create(vlan=1, description='')
        justification = Justification.objects.create(name='justification')

        url = reverse("arnold-manual-detention-step-two", args=(cam_entry.mac,))

        response = client.post(
            url,
            follow=True,
            data={
                "camtuple": str(cam_entry.pk),
                "target": cam_entry.mac,
                "method": "quarantine",
                "qvlan": str(qvlan.pk),
                "justification": str(justification.pk),
                "submit": "Detain",
            },
        )

        assert response.status_code == 200
        assert (
            str(response.context.get("error"))
            == "example-sw.example.org has no read-write management profile"
        )


class TestQuarantineVlan:
    def test_quarantine_vlan_twice_should_show_error_message(self, client):
        url = reverse('arnold-quarantinevlans')

        vlan_id = 1
        QuarantineVlan.objects.create(vlan=vlan_id, description='')

        response = client.post(
            url,
            follow=True,
            data={
                'vlan': vlan_id,
                'description': '',
                'qid': '',
                'submit': 'Add+vlan',
            },
        )

        assert response.status_code == 200
        assert "This vlan is already quarantined." in smart_str(response.content)


@pytest.fixture()
def cam_entry(db):
    box = Netbox(
        ip='10.254.254.254',
        sysname='example-sw.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SW',
    )
    box.save()

    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=box, name='Module 1', model='')
    module.save()

    interface = Interface(
        netbox=box,
        module=module,
        ifindex=1,
    )
    interface.save()

    cam = Cam.objects.create(
        netbox_id=box.id,
        mac='aa:aa:aa:aa:aa:aa',
        ifindex=interface.ifindex,
        end_time=INFINITY,
    )

    yield cam

    cam.delete()
    interface.delete()
    module.delete()
    device.delete()
    box.delete()
