"""NAV web common package."""

import os

from django.db.models import Count, Q
from django.http import Http404

from nav.config import find_config_file
from nav.models.profiles import AccountDashboard

WELCOME_ANONYMOUS_PATH = find_config_file(
    os.path.join("webfront", "welcome-anonymous.txt")
)
WELCOME_REGISTERED_PATH = find_config_file(
    os.path.join("webfront", "welcome-registered.txt")
)
NAV_LINKS_PATH = find_config_file(os.path.join("webfront", "nav-links.conf"))


def find_dashboard(account, dashboard_id=None):
    """Find a dashboard for this account

    Either find a specific one or the default one. If none of those exist we
    find the one with the most widgets.
    """
    kwargs = {'pk': dashboard_id} if dashboard_id else {'is_default': True}
    try:
        dashboard = AccountDashboard.objects.get(
            (Q(account=account) | Q(is_shared=True)), **kwargs
        )
        dashboard.shared_by_other = dashboard.is_shared and dashboard.account != account

    except AccountDashboard.DoesNotExist:
        if dashboard_id:
            raise Http404

        # Do we have a dashboard at all?
        dashboards = AccountDashboard.objects.filter(account=account)
        if dashboards.count() == 0:
            raise Http404

        # No default dashboard? Find the one with the most widgets
        dashboard = dashboards.annotate(Count('widgets')).order_by('-widgets__count')[0]
    except AccountDashboard.MultipleObjectsReturned:
        # Grab the first one
        dashboard = AccountDashboard.objects.filter(account=account, **kwargs)[0]

    return dashboard


def get_dashboards_for_account(account) -> list[AccountDashboard]:
    """
    Returns a queryset of dashboards for the given account,
    including those the account subscribes to.
    """
    dashboards = (
        AccountDashboard.objects.filter(
            Q(account=account) | Q(subscribers__account=account)
        )
        .select_related('account')
        .distinct()
    )
    for dash in dashboards:
        dash.can_edit = dash.can_edit(account)
        dash.shared_by_other = dash.is_shared and dash.account_id != account.id

    return list(dashboards)
