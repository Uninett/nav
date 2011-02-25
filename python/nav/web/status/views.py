# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""Views for status tool"""

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from nav.django.utils import get_account
from nav.models.profiles import StatusPreference
from nav.models.manage import Organization, Category
from nav.web.message import Messages, new_message

from nav.web.status.sections import get_user_sections
from nav.web.status.forms import AddSectionForm
from nav.web.status.utils import extract_post, order_status_preferences
from nav.web.status.utils import make_default_preferences, get_form_for_section

SERVICE_SECTIONS = (
    StatusPreference.SECTION_SERVICE,
    StatusPreference.SECTION_SERVICE_MAINTENANCE
)

def status(request):
    '''Main status view.'''
    account = get_account(request)
    sections = get_user_sections(account)

    if not sections:
        make_default_preferences(account)
        sections = get_user_sections(account)

    return render_to_response(
        'status/status.html',
        {
            'active': {'status': True},
            'sections': sections,
            'title': 'NAV - Status',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )

def preferences(request):
    '''Allows user customization of the status page.'''
    if request.method == 'POST':
        request.POST = extract_post(request.POST.copy())
        if request.POST.get('moveup') or request.POST.get('movedown'):
            return move_section(request)
        elif request.POST.get('delete'):
            return delete_section(request)

    account = get_account(request)
    sections = StatusPreference.objects.filter(account=account)

    return render_to_response(
        'status/preferences.html',
        {
            'active': {'preferences': True},
            'sections': sections,
            'add_section': AddSectionForm(),
            'title': 'Nav - Status preferences',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )

def edit_preferences(request, section_id):
    if request.method == 'POST':
        return save_preferences(request)

    account = get_account(request)
    try:
        section = StatusPreference.objects.get(
            id=section_id,
            account=account,
        )
    except StatusPreference.DoesNotExist:
        # FIXME Maybe send a message as well?
        return HttpResponseRedirect(reverse('status-preferences'))

    data = {
        'id': section.id,
        'name': section.name,
        'type': section.type,
        'organizations': list(section.organizations.values_list(
                'id', flat=True)) or [''],
    }
    if section.type == StatusPreference.SECTION_THRESHOLD:
        data['categories'] = list(section.categories.values_list(
                'id', flat=True)) or ['']
    elif section.type in SERVICE_SECTIONS:
        data['services'] = section.services.split(",") or ['']
        data['states'] = section.states.split(",")
    else:
        data['categories'] = list(section.categories.values_list(
                'id', flat=True)) or ['']
        data['states'] = section.states.split(",")
    form_model = get_form_for_section(section.type)
    form = form_model(data)

    return render_to_response(
        'status/edit_preferences.html',
        {
            'active': {'preferences': True},
            'name': section.name,
            'type': section.readable_type(),
            'section_form': form,
            'title': 'NAV - Edit status preference section',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )

def add_section(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))
    elif 'save' in request.POST:
        return save_preferences(request)

    section_type = request.POST.get('section', None)
    name = StatusPreference.lookup_readable_type(section_type)
    initial = {'name': name, 'type': section_type}
    form_model = get_form_for_section(section_type)
    form = form_model(initial=initial)

    return render_to_response(
        'status/edit_preferences.html',
        {
            'active': {'preferences': True},
            'name': name,
            'section_form': form,
            'title': 'NAV - Add new status section',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request),
    )

def save_preferences(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))

    account = get_account(request)

    type = request.POST.get('type', None)
    form_model = get_form_for_section(type)
    form = form_model(request.POST)

    if type and form.is_valid():
        try:
            section = StatusPreference.objects.get(id=form.cleaned_data['id'])
            type = section.type
        except StatusPreference.DoesNotExist:
            section = StatusPreference()
            section.position = StatusPreference.objects.count()
            type = form.cleaned_data['type']
            section.type = type

        section.name = form.cleaned_data['name']
        section.account = account
        if type != StatusPreference.SECTION_THRESHOLD:
            section.states = ",".join(form.cleaned_data['states'])
        if type in SERVICE_SECTIONS:
            section.services = ",".join(form.cleaned_data['services'])

        section.save()

        section.organizations = Organization.objects.filter(
            id__in=form.cleaned_data['organizations'])

        if type not in SERVICE_SECTIONS:
            section.categories = Category.objects.filter(
                id__in=form.cleaned_data['categories'])

        new_message(request._req,
            'Saved preferences',
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('status-preferences'))
    else:
        if 'id' in request.POST and request.POST.get('id'):
            section = StatusPreference.objects.get(id=request.POST.get('id'))
            name = section.name
            type = section.type
        elif 'type' in request.POST and request.POST.get('type'):
            name = StatusPreference.lookup_readable_type(
                request.POST.get('type'))
            type = None

        new_message(request._req,
            'There were errors in the form below.',
            Messages.ERROR,
        )
        return render_to_response(
            'status/edit_preferences.html',
            {
                'active': {'preferences': True},
                'title': 'NAV - Add new status section',
                'navpath': [('Home', '/'), ('Status', '')],
                'section_form': form,
                'name': name,
                'type': type,
            },
            RequestContext(request)
        )

def move_section(request):
    account = get_account(request)

    # Moving up, or moving down?
    if request.POST.get('moveup'):
        movement = -1
        section_id = request.POST.get('moveup')
        direction = 'up'
    elif request.POST.get('movedown'):
        movement = 1
        section_id = request.POST.get('movedown')
        direction = 'down'
    else:
        return HttpResponseRedirect(reverse('status-preferences'))

    # Make sure the ordering is correct before we try to move around
    order_status_preferences(account)

    # Find the section we want to move
    try:
        section = StatusPreference.objects.get(
            id=section_id,
            account=account,
        )
    except StatusPreference.DoesNotExist:
        new_message(request._req,
            'Could not find selected filter',
            Messages.ERROR
        )
        return HttpResponseRedirect(reverse('status-preferences'))

    # Find the section we should swap places with.
    # If it's not found we're trying to move the first section up or the last
    # section down.
    try:
        other_section = StatusPreference.objects.get(
            position=section.position + movement,
            account=account,
        )
    except StatusPreference.DoesNotExist:
        new_message(request._req,
            'New position is out of bounds.',
            Messages.ERROR
        )
        return HttpResponseRedirect(reverse('status-preferences'))

    # Swap places
    new_position = other_section.position
    other_section.position = section.position
    section.position = new_position

    other_section.save()
    section.save()

    new_message(request._req,
        'Moved section "%(section)s" %(direction)s' % {
            'section': section.name,
            'direction': direction,
        },
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('status-preferences'))

def delete_section(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))

    account = get_account(request)
    section_ids = request.POST.getlist('delete_checkbox')

    sections = StatusPreference.objects.filter(
        pk__in=section_ids,
        account=account,
    ).delete()

    new_message(request._req,
        'Deleted selected sections',
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('status-preferences'))
