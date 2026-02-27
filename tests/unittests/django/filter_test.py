import pytest

from django.test import RequestFactory

from nav.django.filter import NAVExceptionReporterFilter


@pytest.fixture
def reporter_filter():
    return NAVExceptionReporterFilter()


class TestNAVExceptionReporterFilter:
    """Tests for NAVExceptionReporterFilter.get_post_parameters()"""

    def test_when_sensitive_post_parameters_not_used_then_password_should_still_be_masked(  # noqa: E501
        self, reporter_filter
    ):
        request = RequestFactory().post(
            '/', data={'username': 'admin', 'password': 's3cret'}
        )
        result = reporter_filter.get_post_parameters(request)
        assert result['password'] == reporter_filter.cleansed_substitute
        assert result['username'] == 'admin'

    def test_password_like_post_fields_should_be_masked(self, reporter_filter):
        request = RequestFactory().post(
            '/',
            data={
                'password': 's3cret',
                'old_password': 'old',
                'new_password1': 'new1',
                'new_password2': 'new2',
            },
        )
        result = reporter_filter.get_post_parameters(request)
        for key in ('password', 'old_password', 'new_password1', 'new_password2'):
            assert result[key] == reporter_filter.cleansed_substitute

    def test_non_password_fields_should_pass_through(self, reporter_filter):
        request = RequestFactory().post(
            '/', data={'username': 'admin', 'next': '/foo/'}
        )
        result = reporter_filter.get_post_parameters(request)
        assert result['username'] == 'admin'
        assert result['next'] == '/foo/'

    def test_when_sensitive_post_parameters_set_password_it_should_still_be_masked(
        self, reporter_filter
    ):
        request = RequestFactory().post(
            '/', data={'username': 'admin', 'password': 's3cret'}
        )
        request.sensitive_post_parameters = ('password',)
        result = reporter_filter.get_post_parameters(request)
        assert result['password'] == reporter_filter.cleansed_substitute
        assert result['username'] == 'admin'
