#
# Copyright (C) 2012 (SD -311000) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Views for Arnold"""

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.db.models import Q

from datetime import datetime, timedelta

from nav.models.arnold import Identity, Justification, QuarantineVlan
from nav.web.arnold.forms import (JustificationForm, HistorySearchForm,
                                  QuarantineVlanForm)
from nav.web.utils import create_title

NAVPATH = [('Home', '/'), ('Arnold', '/arnold')]


def create_context(path, context):
    """Create a dictionary for use in context based on path"""
    navpath = NAVPATH + [(path,)]
    path_context = {
        'navpath': navpath,
        'title': create_title(navpath)
    }
    return dict(path_context.items() + context.items())


def render_history(request):
    """Controller for rendering arnold history"""
    days = 7
    if 'days' in request.GET:
        form = HistorySearchForm(request.GET)
        if form.is_valid():
            days = form.cleaned_data['days']

    form = HistorySearchForm(initial={'days': days})

    identities = Identity.objects.filter(
        last_changed__gte=datetime.now() - timedelta(days=days))

    return render_to_response(
        'arnold/history.html',
        create_context('History',
                       {'active': {'history': True},
                        'form': form,
                        'identities': identities}),
        context_instance=RequestContext(request)
    )


def render_detained_ports(request):
    """Controller for rendering detained ports"""
    identities = Identity.objects.filter(
        Q(status='disabled') | Q(status='quarantined'))

    return render_to_response(
        'arnold/detainedports.html',
        create_context('Detentions',
                       {'active': {'detentions': True},
                        'identities': identities}),
        context_instance=RequestContext(request)
    )


def render_search(request):
    """Controller for rendering search"""
    pass


def render_justifications(request, jid=None):
    """Controller for rendering detention reasons"""
    if request.method == 'POST':
        form = JustificationForm(request.POST)
        if form.is_valid():
            process_justification_form(form)
            return redirect('arnold-justificatons')
    elif jid:
        justification = Justification.objects.get(pk=jid)
        form = JustificationForm(initial={
            'justificationid': justification.id,
            'name': justification.name,
            'description': justification.description
        })
    else:
        form = JustificationForm()

    justifications = Justification.objects.all()

    return render_to_response(
        'arnold/justifications.html',
        create_context('Justifications',
                       {'active': {'justifications': True},
                        'form': form,
                        'justifications': justifications}),
        context_instance=RequestContext(request)
    )


def process_justification_form(form):
    """Add new justification based on form data"""
    name = form.cleaned_data['name']
    desc = form.cleaned_data['description']
    justificationid = form.cleaned_data['justificationid']

    if justificationid:
        justification = Justification.objects.get(pk=justificationid)
    else:
        justification = Justification()

    justification.name = name
    justification.description = desc

    justification.save()


def render_manual_detention(request):
    """Controller for rendering manual detention"""
    pass


def render_predefined_detentions(request):
    """Controller for rendering predefined detentions"""
    pass


def render_quarantine_vlans(request, qid=None):
    """Controller for rendering quarantine vlans"""
    if request.method == 'POST':
        form = QuarantineVlanForm(request.POST)
        if form.is_valid():
            process_quarantinevlan_form(form)
            return redirect('arnold-quarantinevlans')
    elif qid:
        qvlan = QuarantineVlan.objects.get(pk=qid)
        form = QuarantineVlanForm(initial={
            'qid': qvlan.id,
            'vlan': qvlan.vlan,
            'description': qvlan.description
        })
    else:
        form = QuarantineVlanForm()

    qvlans = QuarantineVlan.objects.all()

    return render_to_response(
        'arnold/quarantinevlans.html',
        create_context('Quarantine Vlans',
                       {'active': {'quarantinevlans': True},
                        'form': form,
                        'qvlans': qvlans}),
        context_instance=RequestContext(request)
    )


def process_quarantinevlan_form(form):
    """Add new quarantine vlan based on form data"""
    vlan = form.cleaned_data['vlan']
    desc = form.cleaned_data['description']
    qid = form.cleaned_data['qid']

    if qid:
        qvlan = QuarantineVlan.objects.get(pk=qid)
    else:
        qvlan = QuarantineVlan()

    qvlan.vlan = vlan
    qvlan.description = desc

    qvlan.save()

