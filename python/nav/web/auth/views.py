from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic import FormView

from social_django.models import Partial

from nav.models.profiles import Account


class PSASetPasswordFormView(FormView):
    login_required = False
    form_class = SetPasswordForm
    template_name = 'auth/require_password_form.html'

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "user_id" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain the 'user_id' parameter."
            )
        token = self.request.GET.get('partial_token', None)
        self.partial = self.get_partial(token)

        self.user = None
        if self.partial:
            self.user = self.get_user(self.partial.data["kwargs"]["user"])
        if self.user is not None:
            return super().dispatch(*args, **kwargs)

        return self.render_to_response(self.get_context_data())

    @method_decorator(requires_csrf_token)
    def post(self, request, *args, **kwargs):
        # Noop, page visited directly and not during login
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        context = {"token": self.partial.token}
        backend = self.partial.backend
        nexthop = reverse('social:complete', kwargs={"backend": backend})
        querystring = urlencode(context)
        return f'{nexthop}?{querystring}'

    #     def get(self, request, *args, **kwargs):
    #         token = self.request.GET.get('partial_token')
    #         self.partial = self.get_partial(token)
    #         assert False, self.partial.data
    #         return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = self.request.GET.get('partial_token')
        partial = self.get_partial(token)

        backend_name = partial.backend

        context['token'] = token
        if token:
            nexthop = 'social:complete'  # We're logging in!
        else:  # Direct access
            nexthop = 'psa-require-password'
        context['nexthop'] = reverse(nexthop, kwargs={"backend": backend_name})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.user
        return kwargs

    def get_partial(self, token):
        partial = get_object_or_404(Partial, token=token)
        return partial

    def get_user(self, uid):
        try:
            int(uid)
            user = Account._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            Account.DoesNotExist,
        ):
            user = None
        return user
