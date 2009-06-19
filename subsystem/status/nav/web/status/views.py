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
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Views for status tool"""

from django.template import RequestContext
from django.forms.models import modelformset_factory, inlineformset_factory
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from nav.web.templates.StatusTemplate import StatusTemplate
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.profiles import StatusPreference, Account
from nav.web.message import Messages, new_message

from nav.web.status.sections import get_user_sections
from nav.web.status.forms import SectionForm
from nav.web.status.utils import extract_post, order_status_preferences

def status(request):
    '''Main status view.'''
    pass

def preferences(request):
    '''Allows user customization of the status page.'''
    if request.method == 'POST':
        request.POST = extract_post(request.POST.copy())
        if request.POST.get('moveup') or request.POST.get('movedown'):
            return move_section(request)
        else:
            return save_preferences(request)

    account = get_account(request)
    SectionFormSet = inlineformset_factory(
        Account,
        StatusPreference,
        extra=0,
        form=SectionForm)
    formset = SectionFormSet(instance=account)
    return render_to_response(
        StatusTemplate,
        'status/preferences.html',
        {
            'formset': formset,
        },
        RequestContext(request)
    )

def save_preferences(request):
    pass

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
        section = StatusPreference.objects.get(id=section_id)
    except StatusPreference.DoesNotExist:
        new_message(
            request,
            'Could not find selected filter',
            Messages.Error
        )
        return HttpResponseRedirect(reverse('status-preferences'))

    # Find the section we should swap places with.
    # If it's not found we're trying to move the first section up or the last
    # section down.
    try:
        other_section = StatusPreference.objects.get(position=section.position + movement)
    except StatusPreference.DoesNotExist:
        new_message(
            request,
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

    new_message(
        request,
        'Moved section "%(section)s" %(direction)s' % {
            'section': section.name,
            'direction': direction,
        },
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('status-preferences'))
