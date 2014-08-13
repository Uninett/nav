"""Mixin classes for netmap"""
from django.core.exceptions import PermissionDenied

from nav.django.utils import get_account
from nav.models.profiles import NetmapViewDefaultView, Account


class DefaultNetmapViewMixin(object):
    """
    Mixin for returning either a global or user specific
    default view
    """
    def get_context_data(self, user, **kwargs):
        netmap_views = NetmapViewDefaultView.objects.select_related(
            'view',
        )
        try:
            view = netmap_views.get(owner=user).view
        except NetmapViewDefaultView.DoesNotExist:
            try:
                view = netmap_views.get(owner=Account.DEFAULT_ACCOUNT).view
            except NetmapViewDefaultView.DoesNotExist:
                view = None
        return {'default_view': view.viewid if view else None}


class AdminRequiredMixin(object):
    """Mixin for limiting view access to an admin user"""
    def dispatch(self, request, *args, **kwargs):
        if not get_account(request).is_admin():
            raise PermissionDenied
        return super(AdminRequiredMixin, self).dispatch(
            request,
            *args,
            **kwargs
        )
