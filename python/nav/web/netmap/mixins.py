from django.core.exceptions import PermissionDenied

from nav.django.utils import get_account
from nav.models.profiles import NetmapViewDefaultView, Account


class DefaultNetmapViewMixin(object):
    def get_context_data(self, **kwargs):
        try:
            view = NetmapViewDefaultView.objects.get(
                owner=self.account
            ).view
        except NetmapViewDefaultView.DoesNotExist:
            try:
                view = NetmapViewDefaultView.objects.get(
                    owner=Account.DEFAULT_ACCOUNT
                ).view
            except NetmapViewDefaultView.DoesNotExist:
                view = None
        return {'default_view': view.to_json_dict() if view else None}


class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not get_account(request).is_admin():
            raise PermissionDenied
        return super(AdminRequiredMixin, self).dispatch(
            request,
            *args,
            **kwargs
        )
