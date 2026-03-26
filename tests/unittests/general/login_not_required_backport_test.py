from django.test import RequestFactory

from nav.web.auth.middleware import AuthorizationMiddleware


class TestLoginNotRequiredBackport:
    def test_when_login_not_required_then_it_should_bypass_authorization(
        self,
    ):
        from allauth.account.internal.decorators import login_not_required

        @login_not_required
        def allauth_view(request):
            return None

        r = RequestFactory()
        fake_request = r.get('/accounts/dataporten/login/callback/')
        response = AuthorizationMiddleware(lambda x: x).process_view(
            fake_request,
            allauth_view,
            (),
            (),
        )
        assert response is None
