from nav.web.api.v1.auth import JWTPermission


class TestIsPathInEndpoints:
    def test_when_path_is_in_endpoints_then_it_should_return_true(self):
        path = '/api/1/room/'
        endpoints = [path]
        assert JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_path_is_not_in_endpoints_then_it_should_return_false(self):
        path = '/api/1/room/'
        endpoints = ['/api/1/netbox/']
        assert not JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_endpoint_matches_path_except_endpoint_lacks_trailing_slash_then_it_should_return_true(  # noqa: E501
        self,
    ):
        path = '/api/1/room/'
        endpoints = ['/api/1/room']
        assert JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_endpoint_matches_path_except_path_lacks_version_then_it_should_return_true(  # noqa: E501
        self,
    ):
        path = '/api/room/'
        endpoints = ['/api/1/room/']

        assert JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_path_is_in_list_with_multiple_endpoints_then_it_should_return_true(
        self,
    ):
        path = '/api/1/room/'
        endpoints = [
            '/api/1/room/',
            '/api/1/netbox/',
            '/api/1/account/',
        ]

        assert JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_path_is_not_in_list_with_multiple_endpoints_then_it_should_return_false(  # noqa: E501
        self,
    ):
        path = '/api/1/alert/'
        endpoints = [
            '/api/1/room/',
            '/api/1/netbox/',
            '/api/1/account/',
        ]

        assert not JWTPermission.is_path_in_endpoints(path, endpoints)

    def test_when_path_is_sub_endpoint_of_another_endpoint_then_it_should_return_true(
        self,
    ):
        path = '/api/1/prefix/usage/'
        endpoints = [
            '/api/1/prefix/',
        ]

        assert JWTPermission.is_path_in_endpoints(path, endpoints)
