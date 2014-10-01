#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=E1101
"""Navlets - the NAV version of portlets

To use create a Navlet do the following:
- create a module in nav.web.navlets
- create a class in the module that inherits Navlet
  - add at least title and description
  - override at least the 'get_template_basename' method
- add the modulestring to settings.py
  - nav.web.navlets.<module>.<class>
- create a template for at least the view mode
  - it must be named <result_from_get_template_basename>_view.html

Context:
- context is added by overriding 'get_context_data'
  - remember to call super
  - remember to return the new context

If you want the navlet to have prefereneces:
- set class attribute is_editable to True in your class
- create a template for the edit mode that submits a form with the preferences
  - This form will be submitted by javascript, see below
- create at least a post method for storing the preferences
- the preferences are available as navlet.preferences in the template

Templates
- A form in editmode will be submitted automatically by javascript. Make sure
  to return a HttpResponse from the post method. This is done to
  allow reloading only the navlet to display the changes after the post

"""

NAVLET_MODE_VIEW = 'VIEW'
NAVLET_MODE_EDIT = 'EDIT'

NAVLET_COLUMN_1 = 1
NAVLET_COLUMN_2 = 2

REFRESH_INTERVAL = 'refresh_interval'
# These class members will be automatically added to preferences if they exist
DEFAULT_PREFERENCES = [REFRESH_INTERVAL]

import logging
import json
from collections import namedtuple
from operator import attrgetter

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.views.generic.base import TemplateView

from nav.models.profiles import AccountNavlet
from nav.django.auth import get_sudoer
from nav.django.utils import get_account

_logger = logging.getLogger(__name__)

NavletContainer = namedtuple('NavletContainer', 'identifier title description')


class Navlet(TemplateView):
    """Base class for navlets"""

    title = 'Navlet'
    description = 'No description'
    is_editable = False
    is_title_editable = False

    # Set to true if we are to reload only an image. This is useful for
    # loading charts that may take some time to display, thus making the
    # widget 'jump'. The image in question needs the attribute
    # 'data-image-reload'
    image_reload = False
    preferences = {}  # See DEFAULT PREFERENCES for adding default values here
    navlet_id = None
    highlight = None

    @property
    def mode(self):
        """Fetch the mode of this request"""
        return self.request.REQUEST.get('mode', NAVLET_MODE_VIEW)

    def get_template_basename(self):
        """Should return the base template name

        The full template name will be based on this on the following format:
        <template_base_name>_(edit|view).html
        """
        raise NotImplementedError

    def get_template_names(self):
        """Get template name based on navlet mode"""
        if self.mode == NAVLET_MODE_VIEW:
            return 'navlets/%s_view.html' % self.get_template_basename()
        elif self.mode == NAVLET_MODE_EDIT:
            return 'navlets/%s_edit.html' % self.get_template_basename()
        else:
            return 'navlets/%s_view.html' % self.get_template_basename()

    def get_context_data(self, **kwargs):
        context = super(Navlet, self).get_context_data(**kwargs)
        context['navlet'] = self
        return context


def list_navlets(_):
    """Gives a json-response with all navlets modulestring, title and desc"""
    return HttpResponse(json.dumps(get_navlets()))


def get_navlets():
    """Gets all installed navlet classes"""
    navlets = []

    for navletmodule in settings.NAVLETS:
        cls = get_navlet_from_name(navletmodule)
        if cls:
            navlets.append(NavletContainer(navletmodule,
                                           cls.title,
                                           cls.description))
    navlets = sorted(navlets, key=attrgetter('title'))
    return navlets


def get_navlet_from_name(navletmodule):
    """Returns the correct class based on the modulestring"""
    lastmod, clsname = navletmodule.split('.')[-2:]
    try:
        module = __import__(navletmodule[:navletmodule.rfind('.')],
                            fromlist=[lastmod])
        cls = getattr(module, clsname)
    except AttributeError:
        _logger.error('Could not import %s', navletmodule)
    else:
        return cls


def get_user_navlets(request):
    """Gets all navlets that this user subscribes to"""
    account = get_account(request)
    usernavlets = AccountNavlet.objects.filter(account=account)

    navlets = []
    for usernavlet in usernavlets:
        navlets.append(create_navlet_object(usernavlet))
    return HttpResponse(json.dumps(navlets),
                        content_type="application/json")


def create_navlet_object(usernavlet):
    """Create a structure suitable for json transfer of a navlet"""
    url = reverse('get-user-navlet', kwargs={'navlet_id': usernavlet.id})
    navlet_module = usernavlet.navlet
    navlet_class = get_navlet_from_name(navlet_module)
    highlight = navlet_class.highlight
    is_title_editable = navlet_class.is_title_editable
    image_reload = navlet_class.image_reload

    return {'id': usernavlet.id, 'url': url,
            'column': usernavlet.column,
            'preferences': usernavlet.preferences,
            'highlight': highlight,
            'navlet_class': navlet_module.split('.')[-1],
            'image_reload': image_reload,
            'is_title_editable': is_title_editable}


def dispatcher(request, navlet_id):
    """Dispatch the correct navlet based on navlet_id

    The as_view method takes any attribute and adds it to the instance
    as long as it is defined on the Navlet class
    """
    account = request.account
    try:
        account_navlet = AccountNavlet.objects.get(
            account=account, pk=navlet_id)
    except AccountNavlet.DoesNotExist, error:
        _logger.error('%s tried to fetch widget with id %s: %s',
                      account, navlet_id, error)
        return HttpResponse(status=404)
    else:
        cls = get_navlet_from_name(account_navlet.navlet)
        view = cls.as_view(preferences=account_navlet.preferences,
                           navlet_id=navlet_id)
        return view(request)


def add_user_navlet(request):
    """Add a navlet subscription to this user"""
    if request.method == 'POST' and 'navlet' in request.POST:
        account = get_account(request)

        if can_modify_navlet(account, request):
            navlet_class = request.POST.get('navlet')
            navlet = add_navlet(account, navlet_class)
            return HttpResponse(json.dumps(create_navlet_object(navlet)),
                                content_type="application/json")

    return HttpResponse(status=400)


def add_navlet(account, navlet, preferences=None):
    """Create new accountnavlet based on request data"""
    if preferences is None:
        preferences = {}
    accountnavlet = AccountNavlet(account=account, navlet=navlet)
    accountnavlet.column, accountnavlet.order = find_new_placement(account)

    default_preferences = get_default_preferences(
        get_navlet_from_name(navlet)) or {}
    accountnavlet.preferences = dict(preferences.items() +
                                     default_preferences.items())
    accountnavlet.save()
    return accountnavlet


def get_default_preferences(navlet):
    """Check if navlet has predetermined preferences that must be applied"""
    preferences = {}
    for preference in DEFAULT_PREFERENCES:
        if hasattr(navlet, preference):
            preferences[preference] = getattr(navlet, preference)

    if preferences:
        return preferences


def find_new_placement(account):
    """Determines the best placement for a new account navlet"""
    colcount1 = account.accountnavlet_set.filter(
        column=NAVLET_COLUMN_1).count()
    colcount2 = account.accountnavlet_set.filter(
        column=NAVLET_COLUMN_2).count()

    if colcount1 <= colcount2:
        column = 1
        order = colcount1 + 1
    else:
        column = 2
        order = colcount2 + 1

    return column, order


def can_modify_navlet(account, request):
    """Determine if this account can modify navlets"""
    return not (account.is_default_account() and not get_sudoer(request))


def modify_navlet(func, account, request, error_message):
    """Modify the navlet using func"""
    if can_modify_navlet(account, request):
        try:
            func(account, request)
        except AccountNavlet.DoesNotExist:
            return HttpResponse(content=error_message, status=500)
        else:
            return HttpResponse()
    else:
        return HttpResponse(status=403)


def remove_user_navlet(request):
    """Remove a navlet-subscription from this user"""
    if request.method == 'POST' and 'navletid' in request.POST:
        account = get_account(request)
        return modify_navlet(remove_navlet, account, request,
                             "Error removing Navlet")

    return HttpResponse(status=400)


def remove_navlet(account, request):
    """Remove accountnavlet based on request data"""
    navlet_id = int(request.POST.get('navletid'))
    accountnavlet = AccountNavlet(pk=navlet_id, account=account)
    accountnavlet.delete()


def save_navlet_order(request):
    """Save the order of the navlets after a sort"""
    if request.method == 'POST':
        account = get_account(request)
        return modify_navlet(save_order, account, request,
                             "Error saving order")

    return HttpResponse(status=400)


def save_order(account, request):
    """Update navlets with new placement data"""
    orders = json.loads(request.body)
    for key, value in orders['column1'].items():
        update_navlet(account, key, value, NAVLET_COLUMN_1)
    for key, value in orders['column2'].items():
        update_navlet(account, key, value, NAVLET_COLUMN_2)


def update_navlet(account, key, value, column):
    """Save the column and order of an account navlet"""
    key = int(key)
    navlet = AccountNavlet.objects.get(account=account, pk=key)
    navlet.order = value
    navlet.column = column
    navlet.save()


def render_base_template(request):
    """Render only base template with navlet info

    This is used to render only buttons and title of the navlet,
    and is used when an error occured rendering the whole navlet. See
    doc in navlet_controller.js for more info

    """
    try:
        navlet_id = int(request.REQUEST.get('id'))
    except (ValueError, TypeError):
        # We're fucked
        return HttpResponse(status=400)
    else:
        account = get_account(request)
        accountnavlet = get_object_or_404(AccountNavlet,
                                          account=account, pk=navlet_id)
        _logger.error(accountnavlet)
        cls = get_navlet_from_name(accountnavlet.navlet)
        return render_to_response('navlets/base.html', {'navlet': cls},
                                  RequestContext(request))


def add_user_navlet_graph(request):
    """Add a Graph Widget with url set to user dashboard"""
    if request.method == 'POST':
        url = request.POST.get('url')
        target = request.POST.get('target')
        if url:
            add_navlet(request.account, 'nav.web.navlets.graph.GraphWidget',
                       {'url': url, 'target': target})
            return HttpResponse(status=200)

    return HttpResponse(status=400)


def set_navlet_preferences(request):
    """Set preferences for a NAvlet"""
    if request.method == 'POST':
        try:
            preferences = json.loads(request.POST.get('preferences'))
            navletid = request.POST.get('id')
            navlet = AccountNavlet.objects.get(pk=navletid,
                                               account=request.account)
        except AccountNavlet.DoesNotExist:
            return HttpResponse(status=400)
        else:
            for key, value in preferences.items():
                navlet.preferences[key] = value
            navlet.save()
            return HttpResponse()

    return HttpResponse(status=400)
