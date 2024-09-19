class TestPrefixViewSet:
    def test_when_prefix_address_is_unknown_it_should_not_crash(self, client):
        response = client.get(
            "/ipam/api/",
            follow=True,
            data={
                "net_type": "all",
                "within": "192.168.42.0/24",
                "show_all": "True",
            },
        )
        assert response.status_code == 200
