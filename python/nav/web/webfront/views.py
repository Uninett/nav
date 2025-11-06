# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Navbar (tools, preferences) and login related controllers"""

import json
import logging
from datetime import datetime
from operator import attrgetter
from urllib.parse import quote as urlquote

from django.db import models
from django.db.models import Q
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponse,
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh

from nav.auditlog.models import LogEntry
from nav.models.profiles import (
    AccountDashboard,
    AccountDashboardSubscription,
    AccountNavlet,
    NavbarLink,
)
from nav.web import auth, webfrontConfig
from nav.web.auth import ldap
from nav.web.auth import logout as auth_logout
from nav.web.auth.utils import get_account, set_account
from nav.web.message import new_message, Messages
from nav.web.modals import render_modal, render_modal_alert
from nav.web.navlets import can_modify_navlet
from nav.web.utils import generate_qr_code_as_string
from nav.web.utils import require_param
from nav.web.webfront import (
    find_dashboard,
    get_dashboards_for_account,
    WELCOME_ANONYMOUS_PATH,
    WELCOME_REGISTERED_PATH,
)
from nav.web.webfront.forms import (
    LoginForm,
    NavbarLinkFormSet,
    ChangePasswordForm,
)
from nav.web.webfront.utils import quick_read, tool_list

_logger = logging.getLogger('nav.web.tools')


def index(request, did=None):
    """Controller for main page."""
    # Read files that will be displayed on front page
    account = get_account(request)
    if account.is_anonymous:
        welcome = quick_read(WELCOME_ANONYMOUS_PATH)
    else:
        welcome = quick_read(WELCOME_REGISTERED_PATH)

    dashboard = find_dashboard(account, did)
    dashboards = get_dashboards_for_account(account)

    dashboard_ids = [d.id for d in dashboards]
    if dashboard.id not in dashboard_ids:
        dashboards.append(dashboard)

    context = {
        'navpath': [('Home', '/')],
        'date_now': datetime.today(),
        'welcome': welcome,
        'dashboard': dashboard,
        'dashboards': dashboards,
        'can_edit': dashboard.can_edit(account),
        'is_subscribed': dashboard.is_subscribed(account),
        'title': 'NAV - {}'.format(dashboard.name),
    }

    return render(request, 'webfront/index.html', context)


@require_POST
def toggle_dashboard_shared(request, did):
    """Toggle shared status for this dashboard"""
    account = get_account(request)
    dashboard = get_object_or_404(AccountDashboard, pk=did, account=account)

    # Checkbox input returns 'on' if checked
    is_shared = request.POST.get('is_shared') == 'on'
    if is_shared == dashboard.is_shared:
        return _render_share_form_response(
            request,
            dashboard,
        )

    dashboard.is_shared = is_shared
    dashboard.save()

    if not is_shared:
        AccountDashboardSubscription.objects.filter(dashboard=dashboard).delete()

    return _render_share_form_response(
        request,
        dashboard,
        message="Dashboard sharing is now {}.".format(
            "enabled" if is_shared else "disabled"
        ),
    )


def _render_share_form_response(
    request, dashboard: AccountDashboard, message: str = None
):
    """Render the share dashboard form response."""
    return render(
        request,
        'webfront/_dashboard_settings_shared_form.html',
        {
            'dashboard': dashboard,
            'message': message,
            'changed': True,
        },
    )


@require_POST
def toggle_subscribe(request, did):
    """Toggle subscription status for this dashboard"""
    dashboard = get_object_or_404(AccountDashboard, pk=did, is_shared=True)
    account = get_account(request)
    if dashboard.is_subscribed(account):
        AccountDashboardSubscription.objects.filter(
            account=account, dashboard=dashboard
        ).delete()
    else:
        AccountDashboardSubscription(account=account, dashboard=dashboard).save()

    return HttpResponseClientRefresh()


@require_GET
def dashboard_search_modal(request):
    """Render the dashboard search modal dialog"""

    return render_modal(
        request,
        'webfront/_dashboard_search_form.html',
        modal_id='dashboard-search-form',
        size='small',
    )


@require_POST
def dashboard_search(request):
    """Search for shared dashboards"""
    raw_search = request.POST.get('search', '')
    search = raw_search.strip() if raw_search else ''
    if not search:
        return render(
            request,
            'webfront/_dashboard_search_results.html',
            {
                'dashboards': [],
                'search': search,
            },
        )

    account = get_account(request)
    dashboards = (
        AccountDashboard.objects.exclude(account=account)
        .filter(
            Q(name__icontains=search)
            | Q(account__login__icontains=search)
            | Q(account__name__icontains=search),
            is_shared=True,
        )
        .select_related('account')
        .annotate(
            is_subscribed=models.Exists(
                AccountDashboardSubscription.objects.filter(
                    dashboard=models.OuterRef('pk'), account=account
                )
            )
        )
    )

    return render(
        request,
        'webfront/_dashboard_search_results.html',
        {
            'dashboards': dashboards,
            'search': search,
        },
    )


def export_dashboard(request, did):
    """Export dashboard as JSON."""
    account = get_account(request)
    dashboard = find_dashboard(account, did)

    response = JsonResponse(dashboard.to_json_dict())
    response['Content-Disposition'] = 'attachment; filename={name}.json'.format(
        name=urlquote(dashboard.name)
    )
    return response


dashboard_fields = {
    'name': str,
    'num_columns': int,
    'widgets': list,
    'version': int,
}

widget_fields = {
    'navlet': str,
    'column': int,
    'preferences': dict,
    'order': int,
}


@require_POST
def import_dashboard(request):
    """Receive an uploaded dashboard file and store in database"""
    account = get_account(request)
    if not can_modify_navlet(account, request):
        return HttpResponseForbidden()

    if 'file' not in request.FILES:
        return render_modal_alert(
            request, "You need to provide a file", modal_id="import-dashboard-form"
        )

    try:
        # Ensure file is interpreted as utf-8 regardless of locale
        blob = request.FILES['file'].read()
        data = json.loads(blob.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError()
        for field, dtype in dashboard_fields.items():
            if field not in data:
                raise ValueError()
            if not isinstance(data[field], dtype):
                raise ValueError()
        dashboard = AccountDashboard(account=account, name=data['name'])
        dashboard.num_columns = data['num_columns']
        widgets = []
        for widget in data['widgets']:
            if not isinstance(widget, dict):
                raise ValueError()
            for field, dtype in widget_fields.items():
                if field not in widget:
                    raise ValueError()
                if not isinstance(widget[field], dtype):
                    raise ValueError()
                if widget['column'] > dashboard.num_columns:
                    raise ValueError()
            widget = {k: v for k, v in widget.items() if k in widget_fields}
            widgets.append(widget)
        dashboard.save()
        for widget in widgets:
            dashboard.widgets.create(account=account, **widget)
        dashboard.save()
        dashboard_url = reverse('dashboard-index-id', args=(dashboard.id,))
        return HttpResponseClientRedirect(dashboard_url)
    except ValueError:
        _logger.exception('Failed to parse dashboard file for import')
        return render_modal_alert(
            request,
            "File is not a valid dashboard file",
            modal_id="import-dashboard-form",
        )


def import_dashboard_modal(request):
    """Render the import dashboard modal dialog"""
    return render_modal(
        request,
        'webfront/_import_dashboard_form_modal.html',
        modal_id="import-dashboard-form",
        size="small",
    )


@sensitive_post_parameters('password')
def login(request):
    """Controller for the login page"""
    if request.method == 'POST':
        return do_login(request)

    origin = request.GET.get('origin', '').strip()
    if 'noaccess' in request.GET:
        account = get_account(request)
        if account.is_anonymous:
            errors = ['You need to log in to access this resource']
        else:
            errors = [
                'You have insufficient privileges to access this '
                'resource. Please log in as another user.'
            ]
    else:
        errors = []

    return render(
        request,
        'webfront/login.html',
        {
            'form': LoginForm(initial={'origin': origin}),
            'origin': origin,
            'errors': errors,
        },
    )


def audit_logging_modal(request):
    """Render the audit logging info modal"""
    return render_modal(
        request,
        'webfront/_about_audit_logging_modal.html',
        modal_id='about-audit-logging',
        size="small",
    )


@sensitive_variables('password')
def do_login(request: HttpRequest) -> HttpResponse:
    """Do a login based on post parameters"""
    errors = []
    form = LoginForm(request.POST)
    origin = request.POST.get('origin', '').strip()

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            account = auth.authenticate(username, password)
        except ldap.Error as error:
            errors.append('Error while talking to LDAP:\n%s' % error)
        else:
            if account:
                LogEntry.add_log_entry(
                    account, 'log-in', '{actor} logged in', before=account
                )
                set_account(request, account)
                _logger.info("%s successfully logged in", account.login)
                if not origin:
                    origin = reverse('webfront-index')
                return HttpResponseRedirect(origin)
            else:
                _logger.info("failed login: %r", username)
                errors.append(
                    'Username or password is incorrect, or the account is locked.'
                )

    # Something went wrong. Display login page with errors.
    return render(
        request,
        'webfront/login.html',
        {
            'form': form,
            'errors': errors,
            'origin': origin,
        },
    )


def logout(request: HttpRequest) -> HttpResponse:
    """Controller for doing a logout"""
    nexthop = auth_logout(request)
    return HttpResponseRedirect(nexthop)


def about(request):
    """Controller for the about page"""
    return render(
        request,
        'webfront/about.html',
        {
            'navpath': [('Home', '/'), ('About', None)],
            'title': 'About NAV',
        },
    )


def toolbox(request):
    """Render the toolbox"""
    account = get_account(request)
    tools = sorted(tool_list(account), key=attrgetter('name'))

    return render(
        request,
        'webfront/toolbox.html',
        {
            'navpath': [('Home', '/'), ('Toolbox', None)],
            'tools': tools,
            'title': 'NAV toolbox',
        },
    )


def _create_preference_context(request):
    """
    Creates a context used by different views for the multiform preference page
    """
    account = get_account(request)

    if account.ext_sync:
        password_form = None
    else:
        password_form = ChangePasswordForm()

    context = {
        'navpath': [('Home', '/'), ('Preferences', None)],
        'title': 'Personal NAV preferences',
        'password_form': password_form,
        'account': account,
        'tool': {
            'name': 'My account',
            'description': 'Edit my personal NAV account settings',
        },
        'navbar_formset': NavbarLinkFormSet(
            queryset=NavbarLink.objects.filter(account=account)
        ),
    }

    return context


def preferences(request):
    """My preferences"""
    context = _create_preference_context(request)

    return render(request, 'webfront/preferences.html', context)


def qr_code(request):
    """Render a model with a qr code linking to current page"""
    url = request.headers.get("referer")
    file_format = webfrontConfig.get("qr_codes", "file_format")
    qr_code = generate_qr_code_as_string(url=url, caption=url, file_format=file_format)

    return render_modal(
        request,
        'webfront/_qr_code.html',
        context={'qr_code': qr_code, 'file_format': file_format},
        modal_id='qr-code',
        size='small',
    )


@sensitive_post_parameters('old_password', 'new_password1', 'new_password2')
def change_password(request):
    """Handles POST requests to change a users password"""
    context = _create_preference_context(request)
    account = get_account(request)

    if account.is_anonymous:
        return render(request, 'useradmin/not-logged-in.html', {})

    if request.method == 'POST':
        password_form = ChangePasswordForm(request.POST, my_account=account)

        if password_form.is_valid():
            account.set_password(password_form.cleaned_data['new_password1'])
            account.save()
            new_message(
                request, 'Your password has been changed.', type=Messages.SUCCESS
            )
        else:
            context['password_form'] = password_form
            return render(request, 'webfront/preferences.html', context)

    return HttpResponseRedirect(reverse('webfront-preferences'))


def save_links(request):
    """Saves navigation preference links on a user"""
    account = get_account(request)
    context = _create_preference_context(request)

    if request.method == 'POST':
        formset = NavbarLinkFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.account = account
                instance.save()
            for form in formset.deleted_objects:
                instance = form.delete()
            new_message(request, 'Your links were updated.', type=Messages.SUCCESS)
        else:
            context['navbar_formset'] = formset

            return render(request, 'webfront/preferences.html', context)

    return HttpResponseRedirect(reverse('webfront-preferences'))


def set_account_preference(request):
    """Set account preference using url attributes"""
    account = get_account(request)
    account.preferences.update(request.GET.dict())
    account.save()
    return HttpResponse()


@require_POST
def set_default_dashboard(request, did):
    """Set the default dashboard for the user"""
    account = get_account(request)
    dash = get_object_or_404(AccountDashboard, pk=did, account=account)

    old_defaults = list(
        AccountDashboard.objects.filter(account=account, is_default=True)
    )
    for old_default in old_defaults:
        old_default.is_default = False

    dash.is_default = True

    AccountDashboard.objects.bulk_update(
        objs=old_defaults + [dash], fields=["is_default"]
    )

    return HttpResponse('Default dashboard set to «{}»'.format(dash.name))


@require_POST
def add_dashboard(request):
    """Add a new dashboard to this user"""
    name = request.POST.get('dashboard-name', 'New dashboard')
    account = get_account(request)
    dashboard = AccountDashboard(account=account, name=name)
    dashboard.save()
    return JsonResponse({'dashboard_id': dashboard.pk})


@require_POST
def delete_dashboard(request, did):
    """Delete this dashboard and all widgets on it, with confirmation modal"""
    account = get_account(request)
    dashboard = get_object_or_404(AccountDashboard, pk=did, account=account)

    is_last = AccountDashboard.objects.filter(account=account).count() == 1
    if is_last or dashboard.is_default:
        error_message = (
            "Cannot delete last dashboard"
            if is_last
            else "Cannot delete default dashboard"
        )
        return render_modal(
            request,
            'webfront/_dashboard_settings_delete_confirmation.html',
            context={'error_message': error_message},
            modal_id='delete-dashboard-confirmation',
            size='small',
        )

    confirm_delete = request.POST.get("confirm_delete", None) == "true"
    if confirm_delete:
        dashboard.delete()
        return HttpResponseClientRedirect(reverse('webfront-index'))

    subscribers_count = dashboard.subscribers.count()

    return render_modal(
        request,
        'webfront/_dashboard_settings_delete_confirmation.html',
        context={'dashboard': dashboard, 'subscribers_count': subscribers_count},
        modal_id='delete-dashboard-confirmation',
        size='small',
    )


@require_POST
def rename_dashboard(request, did):
    """Rename this dashboard"""
    account = get_account(request)
    dash = get_object_or_404(AccountDashboard, pk=did, account=account)
    dash.name = request.POST.get('dashboard-name', dash.name)
    dash.save()
    return HttpResponse('Dashboard renamed to «{}»'.format(dash.name))


@require_POST
def save_dashboard_columns(request, did):
    """Save the number of columns for this dashboard"""

    # Explicit fetch on account to prevent other people to change settings
    account = get_account(request)
    dashboard = get_object_or_404(AccountDashboard, pk=did, account=account)
    dashboard.num_columns = request.POST.get('num_columns', 3)
    dashboard.save()
    return HttpResponse()


@require_POST
@require_param('widget_id')
def moveto_dashboard(request, did):
    """Move a widget to this dashboard"""
    account = get_account(request)
    dashboard = get_object_or_404(AccountDashboard, account=account, pk=did)
    widget = get_object_or_404(
        AccountNavlet, account=account, pk=request.POST.get('widget_id')
    )
    widget.dashboard = dashboard
    widget.save()
    return HttpResponse('Widget moved to {}'.format(dashboard))
