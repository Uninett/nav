# Copyright (C) 2006-2008, 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controller functions for Messages"""

import datetime

from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from nav.web.auth.utils import get_account
from nav.models.msgmaint import Message
from nav.web.messages.forms import MessageForm

# Navigation and tab management
NAVBAR = [('Home', '/'), ('Messages', None)]
ACTIVE_TITLE = 'NAV - Messages - Active'
PLANNED_TITLE = 'NAV - Messages - Scheduled'
HISTORIC_TITLE = 'NAV - Messages - Archive'
SAVE_TITLE = 'NAV - Messages - Save'
VIEW_TITLE = 'NAV - Messages - View message - '

ACTIVE_DEFAULTS = {
    'title': ACTIVE_TITLE,
    'navpath': NAVBAR,
    'active': {'active': True},
    'caption': 'Active',
}
PLANNED_DEFAULTS = {
    'title': PLANNED_TITLE,
    'navpath': NAVBAR,
    'active': {'scheduled': True},
    'caption': 'Scheduled',
}
HISTORIC_DEFAULTS = {
    'title': HISTORIC_TITLE,
    'navpath': NAVBAR,
    'active': {'archive': True},
    'caption': 'Archive',
}
SAVE_DEFAULTS = {'title': SAVE_TITLE, 'navpath': NAVBAR}
VIEW_DEFAULTS = {'title': VIEW_TITLE, 'navpath': NAVBAR}

EDIT = {'caption': 'Edit message'}
CREATE = {'caption': 'Create new message'}
FOLLOWUP = {'caption': 'Follow up message'}


def redirect_to_active(_request):
    """Redirect to main page for this tool"""
    return redirect(reverse('messages-home'))


def active(request):
    """Displays active messages that is not replaced"""
    active_messages = Message.objects.filter(
        publish_start__lte=datetime.datetime.now(),
        publish_end__gte=datetime.datetime.now(),
        replaced_by__isnull=True,
    )

    info_dict = {'messages': active_messages}
    info_dict.update(ACTIVE_DEFAULTS)

    return render(request, 'messages/list.html', info_dict)


def planned(request):
    """Displays messages that are planned in the future"""
    planned_messages = Message.objects.filter(
        publish_start__gte=datetime.datetime.now(),
        publish_end__gte=datetime.datetime.now(),
        replaced_by__isnull=True,
    )

    info_dict = {'messages': planned_messages}
    info_dict.update(PLANNED_DEFAULTS)

    return render(request, 'messages/list.html', info_dict)


def historic(request):
    """Displays ended or replaced messages"""
    historic_messages = Message.objects.filter(
        Q(publish_end__lt=datetime.datetime.now()) | Q(replaced_by__isnull=False)
    )

    info_dict = {'messages': historic_messages}
    info_dict.update(HISTORIC_DEFAULTS)

    return render(request, 'messages/list.html', info_dict)


def view(request, message_id):
    """Displays details about a single message"""
    message = get_object_or_404(Message, pk=message_id)

    info_dict = {'message': message, 'now': datetime.datetime.now()}
    info_dict.update(VIEW_DEFAULTS)
    info_dict['navpath'] = [
        NAVBAR[0],
        ('Messages', reverse('messages-home')),
        (message,),
    ]
    info_dict['title'] += message.title

    return render(request, 'messages/view.html', info_dict)


def expire(_request, message_id):
    """Expires a message. Sets the end date to now"""
    message = get_object_or_404(Message, pk=message_id)
    message.publish_end = datetime.datetime.now()
    message.save()

    return HttpResponseRedirect(reverse('messages-view', args=(message_id,)))


def followup(request, message_id):
    """
    Follow up means that you ought to replace a task for a new one.
    This method sends the object you are replacing to the
    same form that creates and edits.
    """
    replaces = get_object_or_404(Message, pk=message_id)
    return save(request, message_id, replaces)


def save(request, message_id=None, replaces=None):
    """Displays the form for create, edit and followup, and saves them"""
    account = get_account(request)
    info_dict = SAVE_DEFAULTS.copy()
    navpath = [NAVBAR[0], ('Messages', reverse('messages-home'))]

    # If it's an edit, load the initial data
    if message_id and not replaces:
        message = get_object_or_404(Message, pk=message_id)
        info_dict.update(EDIT)
        info_dict['message'] = message
        navpath += [("Edit %s" % message,)]
    else:
        message = Message()

        # If this is a replacement, load some initial data to a
        # clean object to help out
        if replaces:
            info_dict['message'] = replaces
            navpath += [("Replace %s" % replaces,)]
            message.title = replaces.title
            message.publish_start = replaces.publish_start
            message.publish_end = replaces.publish_end
            message.replaces_message = replaces
            info_dict.update(FOLLOWUP)
        else:
            info_dict.update(CREATE)
            navpath += [("Create message",)]

    form = MessageForm(instance=message)

    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.instance.author = account.login
            form.save()
            return HttpResponseRedirect(
                reverse('messages-view', args=(form.instance.id,))
            )

    info_dict.update({'form': form, 'navpath': navpath})

    # If replacement, add the object so we can view it
    if replaces:
        info_dict['replaces'] = replaces

    return render(request, 'messages/save.html', info_dict)
