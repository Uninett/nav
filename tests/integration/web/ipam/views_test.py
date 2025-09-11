from django.urls import reverse


class TestSubnetAllocatorHelpModal:
    def test_should_render_help_modal(self, client):
        url = reverse('ipam-subnet-allocator-help')
        response = client.get(url)
        assert response.status_code == 200
        assert b'How to use the subnet diagram' in response.content
