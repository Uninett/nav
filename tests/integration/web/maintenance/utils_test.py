from nav.models.manage import Netbox, Room
from nav.web.maintenance.utils import prefetch_and_group_components


class TestPrefetchAndGroupComponents:
    def test_should_return_list_of_tuples(self):
        netbox_query = Netbox.objects.all()
        results = prefetch_and_group_components(Netbox, netbox_query, Room)
        assert results and all(isinstance(item, tuple) for item in results), (
            "Results should be tuples."
        )

    def test_should_group_by_room(self):
        netbox = Netbox.objects.first()
        netbox_query = Netbox.objects.filter(id=netbox.id)
        results = prefetch_and_group_components(Netbox, netbox_query, Room)
        room_name, netbox_list = results[0]
        assert room_name == str(netbox.room) and netbox.id == netbox_list[0].id, (
            "Room name and Netbox ID do not match expected values."
        )

    def test_when_group_by_is_none_it_should_return_flat_list(self):
        netbox_query = Netbox.objects.all()
        results = prefetch_and_group_components(Netbox, netbox_query, None)
        assert all(isinstance(item, Netbox) for item in results), (
            "Results should be Netbox instances."
        )
