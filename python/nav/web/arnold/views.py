#
# Copyright (C) 2012 (SD -311000) Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Views for Arnold"""

from datetime import datetime, timedelta
import logging

from IPy import IP
from django.shortcuts import render, redirect
from django.db.models import Q

from nav.arnold import (
    open_port,
    disable,
    quarantine,
    GeneralException,
    find_id_information,
    find_input_type,
    check_target,
)
from nav.models.arnold import Identity, Justification, QuarantineVlan, DetentionProfile
from nav.models.manage import Cam, Interface
from nav.web.auth.utils import get_account
from nav.web.arnold.forms import (
    SearchForm,
    HistorySearchForm,
    JustificationForm,
    ManualDetentionForm,
    ManualDetentionTargetForm,
    DetentionProfileForm,
    QuarantineVlanForm,
)
from nav.web.utils import create_title

NAVPATH = [('Home', '/'), ('Arnold', '/arnold')]

_logger = logging.getLogger(__name__)


def create_context(path, context):
    """Create a dictionary for use in context based on path"""
    navpath = NAVPATH + [(path,)]
    path_context = {'navpath': navpath, 'title': create_title(navpath)}
    path_context.update(context)
    return path_context


def render_history(request):
    """Controller for rendering arnold history"""
    days = 7
    if 'days' in request.GET:
        form = HistorySearchForm(request.GET)
        if form.is_valid():
            days = form.cleaned_data['days']

    form = HistorySearchForm(initial={'days': days})

    identities = Identity.objects.filter(
        last_changed__gte=datetime.now() - timedelta(days=days)
    )

    return render(
        request,
        'arnold/history.html',
        create_context(
            'History',
            {'active': {'history': True}, 'form': form, 'identities': identities},
        ),
    )


def render_detained_ports(request):
    """Controller for rendering detained ports"""
    identities = Identity.objects.filter(Q(status='disabled') | Q(status='quarantined'))

    return render(
        request,
        'arnold/detainedports.html',
        create_context(
            'Detentions', {'active': {'detentions': True}, 'identities': identities}
        ),
    )


def render_search(request):
    """Controller for rendering search"""
    search_result = []
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search_result = process_searchform(form)
    else:
        form = SearchForm(initial={'searchtype': 'ip', 'status': 'any', 'days': 7})

    return render(
        request,
        'arnold/search.html',
        create_context(
            'Search',
            {'form': form, 'search_result': search_result, 'active': {'search': True}},
        ),
    )


def process_searchform(form):
    """Get searchresults based on form data"""
    extra = {}
    kwargs = {
        'last_changed__gte': datetime.now() - timedelta(days=form.cleaned_data['days'])
    }

    if form.cleaned_data['searchtype'] == 'ip':
        ip = IP(form.cleaned_data['searchvalue'])
        if ip.len() == 1:
            kwargs['ip'] = str(ip)
        else:
            extra['where'] = ["ip << '%s'" % str(ip)]
    else:
        key = form.cleaned_data['searchtype'] + '__icontains'
        kwargs[key] = form.cleaned_data['searchvalue']

    if form.cleaned_data['status'] != 'any':
        kwargs['status'] = form.cleaned_data['status']

    return Identity.objects.filter(**kwargs).extra(**extra)


def render_justifications(request, jid=None):
    """Controller for rendering detention reasons"""
    if request.method == 'POST':
        form = JustificationForm(request.POST)
        if form.is_valid():
            process_justification_form(form)
            return redirect('arnold-justifications')
    elif jid:
        justification = Justification.objects.get(pk=jid)
        form = JustificationForm(
            initial={
                'justificationid': justification.id,
                'name': justification.name,
                'description': justification.description,
            }
        )
    else:
        form = JustificationForm()

    justifications = Justification.objects.all()
    for justification in justifications:
        justification.deletable = is_deletable(justification)

    return render(
        request,
        'arnold/justifications.html',
        create_context(
            'Justifications',
            {
                'active': {'justifications': True},
                'form': form,
                'justifications': justifications,
            },
        ),
    )


def is_deletable(justification):
    """Determines if a justification is deletable

    :param justification: The Justification to verify is deletable
    :type justification: Justification

    """
    is_in_detentionset = justification.detention_profiles.exists()
    has_been_used = justification.identities.exists()

    return not (has_been_used or is_in_detentionset)


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


def delete_justification(_request, jid):
    """Deletes a justification"""

    try:
        justification = Justification.objects.get(pk=jid)
    except Justification.DoesNotExist:
        # As this method is only called from ui on existing justifications
        # this should not happen. Just redirect to list again
        return redirect('arnold-justifications')
    else:
        justification.delete()

    return redirect('arnold-justifications')


def render_manual_detention_step_one(request):
    """Controller for rendering manual detention"""
    error = ""
    if request.method == 'POST':
        form = ManualDetentionTargetForm(request.POST)
        if form.is_valid():
            try:
                check_target(form.cleaned_data['target'], trunk_ok=True)
                return redirect(
                    'arnold-manual-detention-step-two', form.cleaned_data['target']
                )
            except GeneralException as err:
                error = err
    else:
        form = ManualDetentionTargetForm()

    return render(
        request,
        'arnold/manualdetain.html',
        create_context(
            'Manual detention',
            {'active': {'manualdetention': True}, 'form': form, 'error': error},
        ),
    )


def render_manual_detention_step_two(request, target):
    """Controller for rendering interface choices when manualy detaining"""

    error = ""
    candidates = find_id_information(target, 3, trunk_ok=True)
    camtuple_choices = [(x.camid, humanize(x)) for x in candidates]

    if request.method == 'POST':
        form = ManualDetentionForm(request.POST)
        form.fields['camtuple'].choices = camtuple_choices
        if form.is_valid():
            error = process_manual_detention_form(form, get_account(request))
            if not error:
                return redirect('arnold-detainedports')

    else:
        form = ManualDetentionForm(initial={'target': target})

    return render(
        request,
        'arnold/manualdetain-step2.html',
        create_context(
            'Manual detention',
            {
                'active': {'manualdetention': True},
                'target': target,
                'candidates': candidates,
                'form': form,
                'now': datetime.now(),
                'error': error,
            },
        ),
    )


def humanize(candidate):
    return '%s - %s' % (candidate.interface, get_last_seen(candidate.camid))


def get_last_seen(camid):
    cam = Cam.objects.get(pk=camid)
    if cam.end_time >= datetime.now():
        return 'still active'
    else:
        return 'last seen %s' % cam.end_time.strftime('%Y-%m-%d %H:%M:%S')


def process_manual_detention_form(form, account):
    """Execute a manual detention based on form data"""
    _logger.debug('process_manual_detention_form')

    target = form.cleaned_data['target']
    justification = Justification.objects.get(pk=form.cleaned_data['justification'])
    username = account.login
    comment = form.cleaned_data['comment']
    days = form.cleaned_data['days']
    camtuple = form.cleaned_data['camtuple']

    cam = Cam.objects.get(pk=camtuple)
    try:
        interface = Interface.objects.get(netbox=cam.netbox, ifindex=cam.ifindex)
    except Interface.DoesNotExist as error:
        return error

    identity = Identity()
    identity.interface = interface
    identity.mac = cam.mac
    if find_input_type(target) == 'IP':
        identity.ip = target

    if form.cleaned_data['method'] == 'disable':
        try:
            disable(
                identity, justification, username, comment=comment, autoenablestep=days
            )
        except Exception as error:  # noqa
            return error
    elif form.cleaned_data['method'] == 'quarantine':
        qvlan = QuarantineVlan.objects.get(pk=form.cleaned_data['qvlan'])
        try:
            quarantine(
                identity,
                qvlan,
                justification,
                username,
                comment=comment,
                autoenablestep=days,
            )
        except Exception as error:  # noqa
            return error


def choose_detentions(request, did):
    """Find all detentions for the mac-address in the given detention"""
    detention = Identity.objects.get(pk=did)
    detentions = Identity.objects.filter(
        mac=detention.mac, status__in=['disabled', 'quarantined']
    )

    return render(
        request,
        'arnold/choose_detentions.html',
        create_context('Enable', {'detentions': detentions}),
    )


def lift_detentions(request):
    """Lift all detentions given in form"""
    if request.method == 'POST':
        account = get_account(request)
        for detentionid in request.POST.getlist('detentions'):
            identity = Identity.objects.get(pk=detentionid)
            open_port(identity, account.login, 'Enabled from web')

    return redirect('arnold-detainedports')


def render_detention_profiles(request):
    """Controller for rendering predefined detentions"""
    profiles = DetentionProfile.objects.all()

    for profile in profiles:
        profile.active = True if profile.active == 'y' else False

    return render(
        request,
        'arnold/detention_profiles.html',
        create_context(
            'Detention Profiles',
            {'active': {'detentionprofiles': True}, 'profiles': profiles},
        ),
    )


def render_edit_detention_profile(request, did=None):
    """Controller for rendering edit of a detention profile"""
    profile = None

    if request.method == 'POST':
        form = DetentionProfileForm(request.POST)
        if form.is_valid():
            process_detention_profile_form(form, get_account(request))
            return redirect('arnold-detention-profiles')

    elif did:
        profile = DetentionProfile.objects.get(pk=did)

        active = True if profile.active == 'y' else False
        incremental = True if profile.incremental == 'y' else False
        qid = profile.quarantine_vlan.id if profile.quarantine_vlan else None

        form = DetentionProfileForm(
            initial={
                'detention_id': profile.id,
                'detention_type': profile.detention_type,
                'title': profile.name,
                'description': profile.description,
                'justification': profile.justification.id,
                'mail': profile.mailfile,
                'qvlan': qid,
                'keep_closed': profile.keep_closed,
                'exponential': incremental,
                'duration': profile.duration,
                'active_on_vlans': profile.active_on_vlans,
                'active': active,
            }
        )
    else:
        form = DetentionProfileForm()

    return render(
        request,
        'arnold/edit_detention_profile.html',
        create_context('Detention Profile', {'form': form, 'profile': profile}),
    )


def process_detention_profile_form(form, account):
    """Process add or edit of new form"""
    did = form.cleaned_data['detention_id']
    if did:
        profile = DetentionProfile.objects.get(pk=did)
    else:
        profile = DetentionProfile()

    profile.name = form.cleaned_data['title']
    profile.description = form.cleaned_data['description']
    profile.mailfile = form.cleaned_data['mail']
    profile.justification = Justification.objects.get(
        pk=form.cleaned_data['justification']
    )
    profile.keep_closed = form.cleaned_data['keep_closed']
    profile.incremental = 'y' if form.cleaned_data['exponential'] else 'n'
    profile.duration = form.cleaned_data['duration']
    profile.active = 'y' if form.cleaned_data['active'] else 'n'
    profile.last_edited = datetime.now()
    profile.edited_by = account.login
    profile.active_on_vlans = form.cleaned_data['active_on_vlans']
    profile.detention_type = form.cleaned_data['detention_type']
    if form.cleaned_data['qvlan']:
        profile.quarantine_vlan = QuarantineVlan.objects.get(
            pk=form.cleaned_data['qvlan']
        )

    profile.save()


def render_quarantine_vlans(request, qid=None):
    """Controller for rendering quarantine vlans"""
    if request.method == 'POST':
        form = QuarantineVlanForm(request.POST)
        if form.is_valid():
            process_quarantinevlan_form(form)
            return redirect('arnold-quarantinevlans')
    elif qid:
        qvlan = QuarantineVlan.objects.get(pk=qid)
        form = QuarantineVlanForm(
            initial={
                'qid': qvlan.id,
                'vlan': qvlan.vlan,
                'description': qvlan.description,
            }
        )
    else:
        form = QuarantineVlanForm()

    qvlans = QuarantineVlan.objects.all()

    return render(
        request,
        'arnold/quarantinevlans.html',
        create_context(
            'Quarantine Vlans',
            {'active': {'quarantinevlans': True}, 'form': form, 'qvlans': qvlans},
        ),
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


def render_details(request, did):
    """Controller for rendering details about an identity"""
    identity = Identity.objects.get(pk=did)

    error = ''
    try:
        identity.interface
    except Interface.DoesNotExist:
        error = "Could not find interface, maybe switch is replaced?"

    return render(
        request,
        'arnold/details.html',
        create_context('Details', {'identity': identity, 'error': error}),
    )
