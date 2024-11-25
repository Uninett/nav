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


from datetime import datetime
import json
import logging
from operator import attrgetter
from urllib.parse import quote as urlquote

from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponse,
    JsonResponse,
)
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from nav.auditlog.models import LogEntry
from nav.django.utils import get_account
from nav.models.profiles import NavbarLink, AccountDashboard, AccountNavlet
from nav.web.auth import logout as auth_logout
from nav.web import auth
from nav.web.auth import ldap
from nav.web.auth.utils import set_account
from nav.web.utils import require_param
from nav.web.webfront.utils import quick_read, tool_list
from nav.web.webfront.forms import (
    LoginForm,
    NavbarLinkFormSet,
    ChangePasswordForm,
    ColumnsForm,
)
from nav.web.navlets import list_navlets, can_modify_navlet
from nav.web.message import new_message, Messages
from nav.web.webfront import (
    get_widget_columns,
    find_dashboard,
    WELCOME_ANONYMOUS_PATH,
    WELCOME_REGISTERED_PATH,
)

_logger = logging.getLogger('nav.web.tools')


def index(request, did=None):
    """Controller for main page."""
    # Read files that will be displayed on front page
    if request.account.is_default_account():
        welcome = quick_read(WELCOME_ANONYMOUS_PATH)
    else:
        welcome = quick_read(WELCOME_REGISTERED_PATH)

    dashboard = find_dashboard(request.account, did)
    dashboards = AccountDashboard.objects.filter(account=request.account)

    context = {
        'navpath': [('Home', '/')],
        'date_now': datetime.today(),
        'welcome': welcome,
        'dashboard': dashboard,
        'dashboards': dashboards,
        'navlets': list_navlets(),
        'title': u'NAV - {}'.format(dashboard.name),
    }

    if dashboards.count() > 1:
        dashboard_ids = [d.pk for d in dashboards]
        current_index = dashboard_ids.index(dashboard.pk)
        previous_index = current_index - 1
        next_index = current_index + 1
        if current_index == len(dashboard_ids) - 1:
            next_index = 0
        context.update(
            {
                'previous_dashboard': dashboards.get(pk=dashboard_ids[previous_index]),
                'next_dashboard': dashboards.get(pk=dashboard_ids[next_index]),
            }
        )

    return render(request, 'webfront/index.html', context)


def export_dashboard(request, did):
    """Export dashboard as JSON."""
    dashboard = get_object_or_404(AccountDashboard, pk=did, account=request.account)

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
    if not can_modify_navlet(request.account, request):
        return HttpResponseForbidden()
    response = {}
    if 'file' in request.FILES:
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
            dashboard = AccountDashboard(account=request.account, name=data['name'])
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
                dashboard.widgets.create(account=request.account, **widget)
            dashboard.save()
            response['location'] = reverse('dashboard-index-id', args=(dashboard.id,))
        except ValueError:
            _logger.exception('Failed to parse dashboard file for import')
            return JsonResponse(
                {
                    'error': "File is not a valid dashboard file",
                },
                status=400,
            )
    else:
        return JsonResponse(
            {
                'error': "You need to provide a file",
            },
            status=400,
        )
    return JsonResponse(response)


@sensitive_post_parameters('password')
def login(request):
    """Controller for the login page"""
    if request.method == 'POST':
        return do_login(request)

    origin = request.GET.get('origin', '').strip()
    if 'noaccess' in request.GET:
        if request.account.is_default_account():
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


@sensitive_variables('password')
def do_login(request):
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
                    'Username or password is incorrect, or the ' 'account is locked.'
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


def logout(request):
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
    account = request.account
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
        'columns_form': ColumnsForm(
            initial={'num_columns': get_widget_columns(account)}
        ),
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


@sensitive_post_parameters('old_password', 'new_password1', 'new_password2')
def change_password(request):
    """Handles POST requests to change a users password"""
    context = _create_preference_context(request)
    account = get_account(request)

    if account.is_default_account():
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


def set_widget_columns(request):
    """Set the number of columns on the webfront"""
    if request.method == 'POST':
        form = ColumnsForm(request.POST)
        if form.is_valid():
            account = request.account
            num_columns = form.cleaned_data.get('num_columns')
            account.preferences[account.PREFERENCE_KEY_WIDGET_COLUMNS] = num_columns
            account.save()
            return HttpResponseRedirect(reverse('webfront-index'))
    return HttpResponseRedirect(reverse('webfront-preferences'))


def set_account_preference(request):
    """Set account preference using url attributes"""
    account = request.account
    account.preferences.update(request.GET.dict())
    account.save()
    return HttpResponse()


@require_POST
def set_default_dashboard(request, did):
    """Set the default dashboard for the user"""
    dash = get_object_or_404(AccountDashboard, pk=did, account=request.account)

    old_defaults = list(
        AccountDashboard.objects.filter(account=request.account, is_default=True)
    )
    for old_default in old_defaults:
        old_default.is_default = False

    dash.is_default = True

    AccountDashboard.objects.bulk_update(
        objs=old_defaults + [dash], fields=["is_default"]
    )

    return HttpResponse(u'Default dashboard set to «{}»'.format(dash.name))


@require_POST
def add_dashboard(request):
    """Add a new dashboard to this user"""
    name = request.POST.get('dashboard-name', 'New dashboard')
    dashboard = AccountDashboard(account=request.account, name=name)
    dashboard.save()
    return JsonResponse({'dashboard_id': dashboard.pk})


@require_POST
def delete_dashboard(request, did):
    """Delete this dashboard and all widgets on it"""
    is_last = AccountDashboard.objects.filter(account=request.account).count() == 1
    if is_last:
        return HttpResponseBadRequest('Cannot delete last dashboard')

    dash = get_object_or_404(AccountDashboard, pk=did, account=request.account)

    if dash.is_default:
        return HttpResponseBadRequest('Cannot delete default dashboard')

    dash.delete()

    return HttpResponse('Dashboard deleted')


@require_POST
def rename_dashboard(request, did):
    """Rename this dashboard"""
    dash = get_object_or_404(AccountDashboard, pk=did, account=request.account)
    dash.name = request.POST.get('dashboard-name', dash.name)
    dash.save()
    return HttpResponse(u'Dashboard renamed to «{}»'.format(dash.name))


@require_POST
def save_dashboard_columns(request, did):
    """Save the number of columns for this dashboard"""

    # Explicit fetch on account to prevent other people to change settings
    dashboard = get_object_or_404(AccountDashboard, pk=did, account=request.account)
    dashboard.num_columns = request.POST.get('num_columns', 3)
    dashboard.save()
    return HttpResponse()


@require_POST
@require_param('widget_id')
def moveto_dashboard(request, did):
    """Move a widget to this dashboard"""
    account = request.account
    dashboard = get_object_or_404(AccountDashboard, account=account, pk=did)
    widget = get_object_or_404(
        AccountNavlet, account=account, pk=request.POST.get('widget_id')
    )
    widget.dashboard = dashboard
    widget.save()
    return HttpResponse(u'Widget moved to {}'.format(dashboard))
