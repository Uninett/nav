# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Alert Profiles view functions"""

# TODO This module has crazy-many lines and should use class-based views

# TODO Check that functions that should require permission do require
# permission

# TODO Filter/filter_groups have owners, check that the account that performs
# the operation is the owner

from django.http import HttpResponseRedirect, QueryDict
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from nav.web.modals import render_modal
from nav.web.utils import SubListView

from nav.models.profiles import (
    Account,
    AccountGroup,
    AlertAddress,
    AlertPreference,
    AlertProfile,
    TimePeriod,
    AlertSubscription,
    FilterGroupContent,
    Operator,
    Expression,
    Filter,
    FilterGroup,
    MatchField,
    SMSQueue,
    AccountAlertQueue,
)
from nav.web.auth.utils import get_account
from nav.web.message import Messages, new_message

from nav.web.alertprofiles.forms import TimePeriodForm, LanguageForm
from nav.web.alertprofiles.forms import AlertProfileForm, AlertSubscriptionForm
from nav.web.alertprofiles.forms import AlertAddressForm, FilterForm
from nav.web.alertprofiles.forms import ExpressionForm, FilterGroupForm
from nav.web.alertprofiles.forms import MatchFieldForm

from nav.web.alertprofiles.utils import alert_subscriptions_table
from nav.web.alertprofiles.utils import read_time_period_templates
from nav.web.alertprofiles.utils import resolve_account_admin_and_owner
from nav.web.alertprofiles.utils import account_owns_filters
from nav.web.alertprofiles.utils import order_filter_group_content

from nav.web.alertprofiles.shortcuts import (
    alertprofiles_response_forbidden,
    alertprofiles_response_not_found,
    BASE_PATH,
)

from .decorators import requires_post

_ = lambda a: a

PAGINATE_BY = 25


def overview(request):
    """The Alert Profiles overview / index page"""
    account = get_account(request)

    # Get information about user
    active_profile = account.get_active_profile()

    if not active_profile:
        subscriptions = None
    else:
        periods = TimePeriod.objects.filter(profile=active_profile).order_by('start')
        subscriptions = alert_subscriptions_table(periods)

    info_dict = {
        'active': {'overview': True},
        'active_profile': active_profile,
        'alert_subscriptions': subscriptions,
        'navpath': [
            ('Home', '/'),
            ('Alert profiles', None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/account_detail.html', info_dict)


def groups_and_permissions_modal(request):
    """Render a modal with information about groups and permissions"""
    account = get_account(request)

    # Get information about user
    groups = account.groups.all()
    active_profile = account.get_active_profile()

    # Get information about users privileges
    sms_privilege = account.has_perm('alert_by', 'sms')
    filter_dict = {'group_permissions__in': [g.id for g in groups]}
    filter_groups = (
        FilterGroup.objects.filter(**filter_dict).distinct().order_by('name')
    )

    language = account.preferences.get(account.PREFERENCE_KEY_LANGUAGE, 'en')
    language_form = LanguageForm(initial={'language': language})

    return render_modal(
        request,
        'alertprofiles/_groups_and_permissions_modal.html',
        context={
            'active_profile': active_profile,
            'filter_groups': filter_groups,
            'groups': groups,
            'language_form': language_form,
            'sms_privilege': sms_privilege,
        },
        modal_id="groups-and-permissions",
        size="large",
    )


def show_profile(request):
    """Shows a single profile"""
    account = get_account(request)

    # Define valid options for ordering
    valid_ordering = ['name', '-name']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    active_profile = account.get_active_profile()

    if not active_profile:
        new_message(request, _('There\'s no active profile set.'), Messages.NOTICE)

    profiles = AlertProfile.objects.filter(account=account.pk).order_by(order_by)

    info_dict = {
        'active': {'profile': True},
        'subsection': {'list': True},
        'profiles': profiles,
        'active_profile': active_profile,
        'page_link': reverse('alertprofiles-profile'),
        'order_by': order_by,
        'navpath': BASE_PATH + [('Profiles', None)],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=profiles,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/profile.html',
        extra_context=info_dict,
    )(request)


def profile_show_form(
    request, profile_id=None, profile_form=None, time_period_form=None
):
    """Shows the profile edit form"""
    account = get_account(request)
    profile = None
    periods = []
    detail_id = None
    page_name = 'New profile'

    if profile_id:
        try:
            profile = AlertProfile.objects.get(pk=profile_id, account=account)
        except AlertProfile.DoesNotExist:
            new_message(
                request, _('The requested profile does not exist.'), Messages.ERROR
            )
            return HttpResponseRedirect(reverse('alertprofiles-profile'))

        detail_id = profile.id
        page_name = profile.name
        periods = TimePeriod.objects.filter(profile=profile).order_by('start')

        if not time_period_form:
            time_period_form = TimePeriodForm(initial={'profile': profile.id})

        if not profile_form:
            profile_form = AlertProfileForm(instance=profile)
    elif not profile_form:
        profile_form = AlertProfileForm()

    templates = None
    if not profile_id:
        templates = read_time_period_templates()
        subsection = {'new': True}
    else:
        subsection = {'detail': profile.id}

    info_dict = {
        'form': profile_form,
        'time_period_form': time_period_form,
        'detail_id': detail_id,
        'owner': True,
        'alert_subscriptions': alert_subscriptions_table(periods),
        'time_period_templates': templates,
        'active': {'profile': True},
        'subsection': subsection,
        'navpath': BASE_PATH
        + [('Profiles', reverse('alertprofiles-profile')), (page_name, None)],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/profile_detail.html', info_dict)


def profile_detail(request, profile_id=None):
    """Shows the profile form a specific profile"""
    return profile_show_form(request, profile_id)


def profile_new(request):
    """Shows an empty profile form"""
    return profile_show_form(request)


def set_active_profile(request, profile):
    """Set active profile to given profile"""
    account = get_account(request)
    preference, _created = AlertPreference.objects.get_or_create(
        account=account, defaults={'active_profile': profile}
    )
    preference.active_profile = profile
    preference.save()
    new_message(
        request,
        'Active profile automatically set to {}'.format(profile.name),
        Messages.NOTICE,
    )


def create_time_periods(request, profile):
    """Creates time periods for this profile based on template chosen"""
    templates = read_time_period_templates()
    template = templates.get(request.POST.get('template'), None)

    if template:
        # A template were selected. Loop through each subsection and make
        # periods if the title of the subsection is 'all_week', 'weekends'
        # or 'weekdays'.
        for key, value in template.items():
            periods = {}
            if key == 'all_week':
                valid_during = TimePeriod.ALL_WEEK
                periods = value
            elif key == 'weekdays':
                valid_during = TimePeriod.WEEKDAYS
                periods = value
            elif key == 'weekends':
                valid_during = TimePeriod.WEEKENDS
                periods = value

            # Make the time periods.
            for start_time in periods.values():
                period = TimePeriod(
                    profile=profile, start=start_time, valid_during=valid_during
                )
                period.save()


@requires_post('alertprofiles-profile')
def profile_save(request):
    """Saves profile data"""
    account = get_account(request)

    if request.POST.get('id'):
        try:
            profile = AlertProfile.objects.get(pk=request.POST.get('id'))
        except (ValueError, AlertProfile.DoesNotExist):
            return alertprofiles_response_not_found(
                request, 'Requested profile does not exist'
            )

        if profile.account != account:
            return alertprofiles_response_forbidden(
                request, 'You do not own this profile.'
            )
    else:
        profile = AlertProfile(account=account)

    profile_form = AlertProfileForm(request.POST, instance=profile)

    if not profile_form.is_valid():
        detail_id = request.POST.get('id') or None
        return profile_show_form(request, detail_id, profile_form)

    profile = profile_form.save()

    # No other profile, set active profile to this profile.
    if AlertProfile.objects.filter(account=account).count() == 1:
        set_active_profile(request, profile)

    # If the user has chosen a time period template, add that period to the
    # profile
    if 'template' in request.POST:
        create_time_periods(request, profile)

    new_message(request, 'Saved profile {}'.format(profile.name), Messages.SUCCESS)

    return HttpResponseRedirect(
        reverse('alertprofiles-profile-detail', args=(profile.id,))
    )


@requires_post('alertprofiles-profile')
def profile_remove(request):
    """Removes a profile"""
    post = request.POST.copy()
    for data in request.POST:
        if data.find("=") != -1:
            attr, value = data.split("=")
            del post[data]
            post[attr] = value
    request.POST = post

    if request.POST.get('activate'):
        return profile_activate(request)
    if request.POST.get('deactivate'):
        return profile_deactivate(request)

    account = get_account(request)
    if request.POST.get('confirm'):
        profiles = AlertProfile.objects.filter(pk__in=request.POST.getlist('element'))

        for profile in profiles:
            if profile.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this profile.')
                )

        profile_names = ', '.join([p.name for p in profiles])
        profiles.delete()

        new_message(
            request,
            _('Deleted profiles: %(profiles)s') % {'profiles': profile_names},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse('alertprofiles-profile'))
    else:
        try:
            active_profile = AlertPreference.objects.get(account=account).active_profile
        except AlertPreference.DoesNotExist:
            active_profile = None
        profiles = AlertProfile.objects.filter(pk__in=request.POST.getlist('profile'))

        if not profiles:
            new_message(request, _('No profiles were selected.'), Messages.NOTICE)
            HttpResponseRedirect(reverse('alertprofiles-profile'))

        elements = []
        for profile in profiles:
            warnings = []
            if profile.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this profile.')
                )
            if profile == active_profile:
                warnings.append({'message': 'This is the currently active profile.'})

            queued = AccountAlertQueue.objects.filter(
                subscription__time_period__profile=profile
            ).count()
            if queued > 0:
                warnings.append(
                    {
                        'message': "There are %(queued)s queued alerts on a "
                        "subscription under this profile. Deleting this"
                        " time period will delete those alerts as "
                        "well." % {'queued': queued}
                    }
                )

            elements.append(
                {
                    'id': profile.id,
                    'description': profile.name,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-profile-remove'),
            'active': {'profile': True},
            'subsection': {'list': True},
            'object_list': elements,
            'perform_on': None,
            'navpath': BASE_PATH
            + [
                ('Profiles', reverse('alertprofiles-profile')),
                ('Remove profiles', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


@requires_post('alertprofiles-profile', ('activate',))
def profile_activate(request):
    """Activates a profile"""
    account = get_account(request)

    try:
        profile = AlertProfile.objects.get(
            pk=request.POST.get('activate'), account=account
        )
    except AlertProfile.DoesNotExist:
        new_message(
            request,
            _('The profile you are trying to activate does not exist'),
            Messages.ERROR,
        )
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    try:
        preference = AlertPreference.objects.get(account=account)
    except AlertPreference.DoesNotExist:
        preference = AlertPreference(account=account)

    preference.active_profile = profile
    preference.save()

    new_message(
        request,
        _('Active profile set to %(profile)s') % {'profile': profile.name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(reverse('alertprofiles-profile'))


@requires_post('alertprofiles-profile')
def profile_deactivate(request):
    """Deactivates a profile"""
    account = get_account(request)

    try:
        preference = AlertPreference.objects.get(account=account)
    except AlertPreference.DoesNotExist:
        preference = AlertPreference(account=account)

    profile_name = preference.active_profile.name
    preference.active_profile = None
    preference.save()

    new_message(
        request,
        _('Active profile %(profile)s was deactivated.') % {'profile': profile_name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(reverse('alertprofiles-profile'))


def profile_time_period(request, time_period_id, time_period_form=None):
    """Shows a form to edit a timeperiod of a profile"""
    try:
        time_period = TimePeriod.objects.get(pk=time_period_id)
    except TimePeriod.DoesNotExist:
        return alertprofiles_response_not_found(
            request, message=_('Requested time period does not exist')
        )
    profile = time_period.profile

    if not time_period_form:
        time_period_form = TimePeriodForm(instance=time_period)

    info_dict = {
        'active': {'profile': True},
        'subsection': {'detail': time_period.profile.id, 'timeperiod': time_period.id},
        'time_period': time_period,
        'time_period_form': time_period_form,
        'navpath': BASE_PATH
        + [
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            ('Edit time period', None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/timeperiod_edit.html', info_dict)


@requires_post('alertprofiles-profile', ('profile',))
def profile_time_period_add(request):
    """Adds a new time period to a profile"""
    account = get_account(request)

    try:
        profile = AlertProfile.objects.get(pk=request.POST.get('profile'))
    except AlertProfile.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested profile does not exist.')
        )

    if profile.account != account:
        return alertprofiles_response_forbidden(
            request, _('You do not own this profile.')
        )

    time_period = None
    if request.POST.get('id'):
        time_period = TimePeriod.objects.get(pk=request.POST.get('id'))

    time_period_form = TimePeriodForm(
        request.POST,
        instance=time_period,
        initial={'profile': profile},
    )

    if not time_period_form.is_valid():
        if time_period:
            return profile_time_period(request, time_period.id, time_period_form)
        else:
            return profile_show_form(request, profile.id, None, time_period_form)

    time_period = time_period_form.save()
    new_message(
        request,
        _('Saved time period %(time)s for %(during)s to profile %(profile)s')
        % {
            'time': time_period.start,
            'during': time_period.get_valid_during_display(),
            'profile': profile.name,
        },
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-profile-detail', args=(profile.id,))
    )


@requires_post('alertprofiles-profile')
def profile_time_period_remove(request):
    """Removes a time period from a profile"""
    if request.POST.get('confirm'):
        account = get_account(request)
        elements = request.POST.getlist('element')

        time_periods = TimePeriod.objects.filter(pk__in=elements)
        first = True
        for period in time_periods:
            if first:
                # We only check profile once and assume it's the same for all.
                # It's only used to redirect the user after deleting all the
                # periods anyways.
                profile = period.profile
                first = False
            if period.profile.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this profile.')
                )

        time_periods_name = ', '.join(
            [
                '%s for %s' % (t.start, t.get_valid_during_display())
                for t in time_periods
            ]
        )
        time_periods.delete()

        new_message(
            request,
            'Removed time periods: %(names)s' % {'names': time_periods_name},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(
            reverse('alertprofiles-profile-detail', args=(profile.id,))
        )
    else:
        account = get_account(request)
        time_periods = TimePeriod.objects.filter(pk__in=request.POST.getlist('period'))
        profile = AlertProfile.objects.get(pk=request.POST.get('profile'))
        active_profile = account.get_active_profile()
        if active_profile and profile == active_profile:
            new_message(
                request,
                _(
                    "Time periods are used in profile %(profile)s, which "
                    "is the current active profile."
                )
                % {'profile': profile.name},
                Messages.WARNING,
            )

        if not time_periods:
            new_message(request, _('No time periods were selected.'), Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-profile-detail', args=(profile.id,))
            )

        elements = []
        for period in time_periods:
            if period.profile.account != account:
                # Even though we assume profile is the same for GUI-stuff, we
                # can't do that when it comes to permissions.
                return alertprofiles_response_forbidden(
                    request, _('You do not own this profile.')
                )
            description = _('From %(time)s for %(profile)s during %(valid_during)s') % {
                'time': period.start,
                'profile': period.profile.name,
                'valid_during': period.get_valid_during_display(),
            }

            queued = AccountAlertQueue.objects.filter(
                subscription__time_period=period
            ).count()
            warnings = []
            if queued > 0:
                warnings.append(
                    {
                        'message': "There are %(queued)s queued alerts on a "
                        "subscription under this time period. Deleting "
                        "this time period will delete those alerts as "
                        "well." % {'queued': queued}
                    }
                )
            elements.append(
                {
                    'id': period.id,
                    'description': description,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-profile-timeperiod-remove'),
            'active': {'profile': True},
            'subsection': {'detail': profile.id},
            'object_list': elements,
            'navpath': BASE_PATH
            + [
                ('Profiles', reverse('alertprofiles-profile')),
                (
                    profile.name,
                    reverse('alertprofiles-profile-detail', args=(profile.id,)),
                ),
                ('Remove time periods', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


def profile_time_period_setup(request, time_period_id=None):
    """Shows form to edit time periods of a profile"""
    if not time_period_id:
        new_message(request, _('No time period were specified'), Messages.ERROR)
        redirect_url = reverse('alertprofiles-profile')
        return HttpResponseRedirect(redirect_url)

    account = get_account(request)

    try:
        time_period = TimePeriod.objects.get(pk=time_period_id)
    except TimePeriod.DoesNotExist:
        return alertprofiles_response_not_found(
            request, message=_('Requested time period does not exist')
        )
    subscriptions = (
        AlertSubscription.objects.select_related('alert_address', 'filter_group')
        .filter(time_period=time_period)
        .order_by('alert_address', 'filter_group')
    )
    profile = time_period.profile

    if account != profile.account:
        return alertprofiles_response_forbidden(
            request, _('You do not have access to this profile.')
        )

    editing = False
    if request.method == 'POST' and request.POST.get('time_period'):
        time_period_form = AlertSubscriptionForm(request.POST, time_period=time_period)
        if request.POST.get('id'):
            editing = True
    else:
        time_period_form = AlertSubscriptionForm(time_period=time_period)

    time_period_form.is_valid()

    info_dict = {
        'form': time_period_form,
        'subscriptions': subscriptions,
        'time_period': time_period,
        'active': {'profile': True},
        'subsection': {'detail': profile.id, 'subscriptions': time_period.id},
        'editing': editing,
        'num_addresses': AlertAddress.objects.filter(account=account).count(),
        'num_filter_groups': FilterGroup.objects.filter(
            Q(owner=account) | Q(owner__isnull=True)
        ).count(),
        'navpath': BASE_PATH
        + [
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            (
                str(time_period.start) + ', ' + time_period.get_valid_during_display(),
                None,
            ),
        ],
        'title': 'NAV - Alert profiles',
        'profile': profile,
    }
    return render(request, 'alertprofiles/subscription_form.html', info_dict)


@requires_post('alertprofiles-profile')
def profile_time_period_subscription_add(request):
    """Adds a subscription to a timeperiod of a profile"""
    account = get_account(request)

    if request.POST.get('id'):
        existing_subscription = AlertSubscription.objects.get(pk=request.POST.get('id'))
        form = AlertSubscriptionForm(request.POST, instance=existing_subscription)
    else:
        form = AlertSubscriptionForm(request.POST)

    if not form.is_valid():
        time_period_id = request.POST.get('time_period')
        return profile_time_period_setup(request, time_period_id)

    time_period = form.cleaned_data['time_period']

    if time_period.profile.account != account:
        return alertprofiles_response_forbidden(
            request, _('You do not own this profile.')
        )

    subscription = form.save()

    new_message(
        request,
        _(
            'Saved alert subscription for filter group %(fg)s to period %(time)s '
            'for %(during)s'
        )
        % {
            'fg': subscription.filter_group.name,
            'time': time_period.start,
            'during': time_period.get_valid_during_display(),
        },
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-profile-timeperiod-setup', args=(time_period.id,))
    )


def profile_time_period_subscription_edit(request, subscription_id=None):
    """Shows the form to edit subscriptions of a time period of a profile"""
    if not subscription_id:
        new_message(request, _('No alert subscription specified'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofile-profile'))

    account = get_account(request)

    subscription = AlertSubscription.objects.select_related(
        'time_period', 'time_period__profile'
    ).get(pk=subscription_id)
    form = AlertSubscriptionForm(
        instance=subscription, time_period=subscription.time_period
    )
    profile = subscription.time_period.profile

    if account != profile.account:
        return alertprofiles_response_forbidden(
            request, _('You do not have access to this profile.')
        )

    info_dict = {
        'form': form,
        'active': {'profile': True},
        'subsection': {
            'detail': profile.id,
            'subscriptions': subscription.time_period.id,
            'subscription_detail': subscription.id,
        },
        'subscription': subscription,
        'editing': True,
        'num_addresses': AlertAddress.objects.filter(account=account).count(),
        'num_filter_groups': FilterGroup.objects.filter(
            Q(owner=account) | Q(owner__isnull=True)
        ).count(),
        'navpath': BASE_PATH
        + [
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            (
                str(subscription.time_period.start)
                + ', '
                + subscription.time_period.get_valid_during_display(),
                reverse(
                    'alertprofiles-profile-timeperiod-setup',
                    args=(subscription.time_period.id,),
                ),
            ),
            ('Edit subscription', None),
        ],
        'title': 'NAV - Alert profiles',
        'profile': profile,
    }
    return render(request, 'alertprofiles/subscription_form.html', info_dict)


@requires_post('alertprofiles-profile')
def profile_time_period_subscription_remove(request):
    """Removes a subscription from a time period"""
    if request.POST.get('confirm'):
        account = get_account(request)
        subscriptions = request.POST.getlist('element')

        try:
            period = TimePeriod.objects.get(pk=request.POST.get('perform_on'))
        except TimePeriod.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested time period does not exist')
            )

        if period.profile.account != account:
            return alertprofiles_response_forbidden(
                request, _('You do not own this profile.')
            )

        AlertSubscription.objects.filter(pk__in=subscriptions).delete()

        new_message(request, _('Removed alert subscriptions.'), Messages.SUCCESS)
        return HttpResponseRedirect(
            reverse('alertprofiles-profile-timeperiod-setup', args=(period.id,))
        )
    else:
        account = get_account(request)
        subscriptions = AlertSubscription.objects.filter(
            pk__in=request.POST.getlist('subscription')
        )

        try:
            period = TimePeriod.objects.get(pk=request.POST.get('id'))
        except TimePeriod.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested time period does not exist')
            )

        if period.profile.account != account:
            return alertprofiles_response_forbidden(
                request, _('You do not own this profile.')
            )

        if not subscriptions:
            new_message(
                request, _('No alert subscriptions were selected.'), Messages.NOTICE
            )
            return HttpResponseRedirect(
                reverse('alertprofiles-profile-timeperiod-setup', args=(period.id,))
            )

        # Make tuples, (id, description_string) for the confirmation page
        elements = []
        for sub in subscriptions:
            warnings = []
            queued = AccountAlertQueue.objects.filter(subscription=sub).count()
            if queued > 0:
                warnings.append(
                    {
                        'message': "There are %(queued)s queued alert(s) on this "
                        "subscription.  If you delete this "
                        "subscription, those alerts will be deleted as "
                        "well." % {'queued': queued},
                    }
                )

            description = _(
                "Watch %(fg)s, send to %(address)s %(dispatch)s, from "
                "%(time)s for %(profile)s during %(during)s"
            ) % {
                'fg': sub.filter_group.name,
                'address': sub.alert_address.address,
                'dispatch': sub.get_type_display(),
                'time': sub.time_period.start,
                'profile': sub.time_period.profile.name,
                'during': sub.time_period.get_valid_during_display(),
            }

            elements.append(
                {
                    'id': sub.id,
                    'description': description,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse(
                'alertprofiles-profile-timeperiod-subscription-remove'
            ),
            'active': {'profile': True},
            'subsection': {'detail': period.profile.id, 'subscriptions': period.id},
            'object_list': elements,
            'perform_on': period.id,
            'navpath': BASE_PATH
            + [
                ('Profiles', reverse('alertprofiles-profile')),
                (
                    period.profile.name,
                    reverse('alertprofiles-profile-detail', args=(period.profile.id,)),
                ),
                (
                    str(period.start) + ', ' + period.get_valid_during_display(),
                    reverse(
                        'alertprofiles-profile-timeperiod-setup', args=(period.id,)
                    ),
                ),
                ('Remove subscriptions', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


def address_list(request):
    """Lists out the user's registered alert addresses"""
    account = get_account(request)

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['address', '-address', 'type', '-type']
    order_by = request.GET.get('order_by', 'address').lower()
    if order_by not in valid_ordering:
        order_by = 'address'

    address = (
        AlertAddress.objects.select_related('type')
        .filter(account=account.pk)
        .order_by(order_by)
    )

    info_dict = {
        'page': page,
        'active': {'address': True},
        'subsection': {'list': True},
        'form_action': reverse('alertprofiles-address-remove'),
        'page_link': reverse('alertprofiles-address'),
        'order_by': order_by,
        'navpath': BASE_PATH + [('Address', None)],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=address,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/address_list.html',
        extra_context=info_dict,
    )(request)


def address_show_form(request, address_id=None, address_form=None):
    """Shows the form to edit an alert address"""
    account = get_account(request)
    page_name = 'New address'
    detail_id = None
    address = None

    if address_id:
        try:
            address = AlertAddress.objects.get(pk=address_id)
        except AlertAddress.DoesNotExist:
            return alertprofiles_response_not_found(
                request, 'The requested alert address does not exist.'
            )
        else:
            # Check if we really are the owner of the address
            if address.account != account:
                return alertprofiles_response_forbidden(
                    request, 'You do not have access to this alert address.'
                )

            page_name = address.address
            detail_id = address.id

    if not address_form:
        address_form = AlertAddressForm(instance=address)

    if not detail_id:
        subsection = {'new': True}
    else:
        subsection = {'detail': detail_id}

    info_dict = {
        'active': {'address': True},
        'subsection': subsection,
        'detail_id': detail_id,
        'form': address_form,
        'owner': True,
        'navpath': BASE_PATH
        + [
            ('Address', reverse('alertprofiles-address')),
            (page_name, None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/address_form.html', info_dict)


def address_detail(request, address_id=None):
    """Shows the form to edit an existing alert address"""
    return address_show_form(request, address_id)


@requires_post('alertprofiles-address')
def address_save(request):
    """Saves an alert address for a user"""
    account = get_account(request)
    address = None
    address_id = None

    if request.POST.get('id'):
        try:
            address = AlertAddress.objects.get(pk=request.POST.get('id'))
        except AlertAddress.DoesNotExist:
            address = None
        else:
            if address.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this address.')
                )
            else:
                address_id = address.id

    if not address:
        address = AlertAddress(account=account)

    address_form = AlertAddressForm(request.POST, instance=address)

    if not address_form.is_valid():
        return address_show_form(request, address_id, address_form)

    address = address_form.save()

    new_message(
        request,
        _('Saved address %(address)s') % {'address': address.address},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-address-detail', args=(address.id,))
    )


@requires_post('alertprofiles-address')
def address_remove(request):
    """Removes an alert address from a user"""
    account = get_account(request)
    if request.POST.get('confirm'):
        addresses = AlertAddress.objects.filter(pk__in=request.POST.getlist('element'))

        for addr in addresses:
            if addr.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this address.')
                )

        subscriptions = AlertSubscription.objects.filter(alert_address__in=addresses)
        if subscriptions:
            for sub in subscriptions:
                new_message(
                    request,
                    _(
                        "Address %(address)s were used in a subscription, "
                        "%(during)s from %(start)s watch %(fg)s for profile "
                        "%(profile)s.  The subscription were removed as a side "
                        "effect of deleting this address."
                    )
                    % {
                        'address': sub.alert_address.address,
                        'start': sub.time_period.start,
                        'during': sub.time_period.get_valid_during_display(),
                        'profile': sub.time_period.profile.name,
                        'fg': sub.filter_group.name,
                    },
                    Messages.NOTICE,
                )

        names = ', '.join([a.address for a in addresses])
        addresses.delete()

        new_message(
            request,
            _('Removed addresses: %(names)s') % {'names': names},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse('alertprofiles-address'))
    else:
        addresses = AlertAddress.objects.filter(pk__in=request.POST.getlist('address'))

        if not addresses:
            new_message(request, _('No addresses were selected'), Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-address'))

        elements = []
        for addr in addresses:
            if addr.account != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not own this address.')
                )

            warnings = []
            subscriptions = AlertSubscription.objects.filter(
                alert_address=addr
            ).select_related('filter_group', 'time_period', 'time_period__profile')
            for sub in subscriptions:
                warnings.append(
                    {
                        'message': 'Address used in subscription "watch %(fg)s '
                        'from %(time)s for profile %(profile)s".'
                        % {
                            'fg': sub.filter_group.name,
                            'time': sub.time_period.start,
                            'profile': sub.time_period.profile.name,
                        },
                        'link': reverse(
                            'alertprofiles-profile-detail',
                            args=(sub.time_period.profile.id,),
                        ),
                    }
                )

                queued = AccountAlertQueue.objects.filter(subscription=sub).count()
                if queued > 0:
                    warnings.append(
                        {
                            'message': "There are %(queued)s queued alerts on "
                            "this subscription. Deleting this time "
                            "period will delete those alerts as "
                            "well." % {'queued': queued}
                        }
                    )

            description = _('''%(type)s address %(address)s''') % {
                'type': addr.type.name,
                'address': addr.address,
            }

            elements.append(
                {
                    'id': addr.id,
                    'description': description,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-address-remove'),
            'active': {'address': True},
            'subsection': {'list': True},
            'object_list': elements,
            'perform_on': None,
            'navpath': BASE_PATH
            + [
                ('Address', reverse('alertprofiles-address')),
                ('Remove addresses', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


@requires_post('alertprofiles-profile', ('language',))
def language_save(request):
    """Saves the user's preferred language"""
    account = get_account(request)
    value = request.POST.get('language')
    account.preferences[account.PREFERENCE_KEY_LANGUAGE] = value
    account.save()

    new_message(request, 'Changed language', Messages.SUCCESS)
    return HttpResponseRedirect(reverse('alertprofiles-overview'))


def sms_list(request):
    """Lists SMS messages addressed to the current user"""
    account = get_account(request)
    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = [
        'time',
        '-time',
        'time_sent',
        '-time_sent',
        'phone',
        '-phone',
        'message',
        '-message',
        'severity',
        '-severity',
        'sent',
        '-sent',
    ]
    order_by = request.GET.get('order_by', '-time').lower()
    if order_by not in valid_ordering:
        order_by = '-time'

    # NOTE Old versions of alert engine may not have set account.
    sms = SMSQueue.objects.filter(account=account).order_by(order_by)

    info_dict = {
        'page': page,
        'active': {'sms': True},
        'page_link': reverse('alertprofiles-sms'),
        'order_by': order_by,
        'navpath': BASE_PATH + [('My SMS', None)],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=sms,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/sms_list.html',
        extra_context=info_dict,
    )(request)


def filter_list(request):
    """Lists all the filters"""
    account = get_account(request)
    admin = account.is_admin()

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'owner', '-owner']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    # Get all public filters, and private filters belonging to this user only
    filters = (
        Filter.objects.select_related('owner')
        .filter(Q(owner=account) | Q(owner__isnull=True))
        .order_by(order_by)
    )

    active = {'filters': True}
    info_dict = {
        'page': page,
        'active': active,
        'subsection': {'list': True},
        'admin': admin,
        'form_action': reverse('alertprofiles-filters-remove'),
        'page_link': reverse('alertprofiles-filters'),
        'order_by': order_by,
        'navpath': BASE_PATH + [('Filters', None)],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=filters,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/filter_list.html',
        extra_context=info_dict,
    )(request)


def filter_show_form(request, filter_id=None, filter_form=None):
    """Convenience method for showing the filter form"""
    active = {'filters': True}
    page_name = 'New filter'
    account = get_account(request)
    admin = account.is_admin()
    is_owner = True

    filtr = None
    expressions = None
    matchfields = None

    # We assume that if no filter_id is set this filter has not been saved
    if filter_id:
        try:
            filtr = Filter.objects.get(pk=filter_id)
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter does not exist.')
            )
        else:
            owner = filtr.owner
            if not owner:
                new_message(
                    request,
                    _(
                        "%(filter)s is a public filter and may be used by other "
                        "users than you."
                    )
                    % {'filter': filtr.name},
                    Messages.WARNING,
                )
                if not admin:
                    is_owner = False
            elif owner != account:
                return alertprofiles_response_forbidden(
                    request, _('You do not have acccess to the requested filter.')
                )

        matchfields = MatchField.objects.all().order_by('name')
        # Get all matchfields (many-to-many connection by table Expression)
        expressions = (
            Expression.objects.select_related('match_field')
            .filter(filter=filter_id)
            .order_by('match_field__name')
        )

        for expr in expressions:
            if expr.operator == Operator.IN:
                expr.value = expr.value.split("|")

        # Check if filter is used by any filter groups
        filter_groups = FilterGroupContent.objects.filter(filter=filtr)
        if filter_groups:
            fg_names = ', '.join([f.filter_group.name for f in filter_groups])
            new_message(
                request,
                _(
                    "%(filter)s is used in the filter groups: %(filter_groups)s. "
                    "Editing this filter will also change how those filter "
                    "groups work."
                )
                % {'filter': filtr.name, 'filter_groups': fg_names},
                Messages.WARNING,
            )

        page_name = filtr.name

    # If no form is supplied we must make one
    if not filter_form:
        if filter_id:
            data = {
                'id': filter_id,
                'owner': filtr.owner is not None,
                'name': filtr.name,
            }
            filter_form = FilterForm(data, admin=admin, is_owner=is_owner)
        else:
            filter_form = FilterForm(
                initial={'owner': account}, admin=admin, is_owner=is_owner
            )

    if filter_id:
        subsection = {'detail': filter_id}
    else:
        subsection = {'new': True}

    return render(
        request,
        'alertprofiles/filter_form.html',
        {
            'active': active,
            'subsection': subsection,
            'admin': admin,
            'owner': is_owner,
            'detail_id': filter_id,
            'form': filter_form,
            'matchfields': matchfields,
            'expressions': expressions,
            'navpath': BASE_PATH
            + [
                ('Filters', reverse('alertprofiles-filters')),
                (page_name, None),
            ],
            'title': 'NAV - Alert profiles',
        },
    )


def filter_detail(request, filter_id=None):
    """Shows the form to edit filters"""
    return filter_show_form(request, filter_id)


@requires_post('alertprofiles-filters')
def filter_save(request):
    """Saves a filter"""
    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filtr = None

    # Build a form. Different values depending on if we are updating or
    # making a new filter
    if request.POST.get('id'):
        try:
            filtr = Filter.objects.get(pk=request.POST.get('id'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter does not exist.')
            )

        if not account_owns_filters(account, filtr):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter.')
            )

    form = FilterForm(request.POST, admin=admin)

    # If there are some invalid values, return to form and show the errors
    if not form.is_valid():
        detail_id = request.POST.get('id') or None
        return filter_show_form(request, detail_id, form)

    # Set the fields in Filter to the submited values
    if request.POST.get('id'):
        filtr.name = request.POST.get('name')
        filtr.owner = owner
    else:
        filtr = Filter(name=request.POST.get('name'), owner=owner)

    # Save the filter
    filtr.save()

    new_message(
        request, _('Saved filter %(name)s') % {'name': filtr.name}, Messages.SUCCESS
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-filters-detail', args=(filtr.id,))
    )


@requires_post('alertprofiles-filters')
def filter_remove(request):
    """Deletes a filter"""
    if request.POST.get('confirm'):
        filters = Filter.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), *filters):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter.')
            )

        names = ', '.join([f.name for f in filters])
        filters.delete()

        new_message(
            request, 'Removed filters: %(names)s' % {'names': names}, Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-filters'))
    else:
        filters = Filter.objects.filter(pk__in=request.POST.getlist('filter'))

        if not account_owns_filters(get_account(request), *filters):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter.')
            )

        if not filters:
            new_message(request, _('No filters were selected.'), Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-filters'))

        elements = []
        for filtr in filters:
            warnings = []
            try:
                filtr.owner
            except Account.DoesNotExist:
                warnings.append(
                    {
                        'message': 'This filter is public. Deleting it will '
                        'make it unavailable for all users of this '
                        'system.'
                    }
                )

            filter_groups = FilterGroup.objects.filter(
                filter_group_contents__filter=filtr
            )
            for fgroup in filter_groups:
                warnings.append(
                    {
                        'message': 'Used in filter group %(name)s.'
                        % {'name': fgroup.name},
                        'link': reverse(
                            'alertprofiles-filter_groups-detail', args=(fgroup.id,)
                        ),
                    }
                )

            elements.append(
                {
                    'id': filtr.id,
                    'description': filtr.name,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-filters-remove'),
            'active': {'filters': True},
            'subsection': {'list': True},
            'object_list': elements,
            'perform_on': None,
            'navpath': BASE_PATH
            + [
                ('Filters', reverse('alertprofiles-filters')),
                ('Remove filters', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


@requires_post('alertprofiles-filters', ('id', 'matchfield'))
def filter_addexpression(request):
    """Shows the form to add an expression to a filter"""
    try:
        filtr = Filter.objects.get(pk=request.POST.get('id'))
    except Filter.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested filter does not exist')
        )

    try:
        matchfield = MatchField.objects.get(pk=request.POST.get('matchfield'))
    except MatchField.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested match field does not exist')
        )

    initial = {'filter': filtr.id, 'match_field': matchfield.id}
    form = ExpressionForm(match_field=matchfield, initial=initial)

    if not account_owns_filters(get_account(request), filtr):
        return alertprofiles_response_forbidden(
            request, _('You do not own this filter.')
        )

    # Check if there's more values than we can show in the list
    list_limited = False
    if matchfield.show_list and form.number_of_choices > matchfield.list_limit:
        list_limited = True

    active = {'filters': True}
    info_dict = {
        'form': form,
        'active': active,
        'subsection': {'detail': filtr.id},
        'filter': filtr,
        'matchfield': matchfield,
        'list_limited': list_limited,
        'navpath': BASE_PATH
        + [
            ('Filters', reverse('alertprofiles-filters')),
            (filtr.name, reverse('alertprofiles-filters-detail', args=(filtr.id,))),
            ('Add expression', None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/expression_form.html', info_dict)


def filter_addexpression_operator_help_modal(request):
    """Renders a modal with descriptions of all available operators"""
    return render_modal(
        request,
        'alertprofiles/_add_expression_operator_help_modal.html',
        modal_id='operator-help',
        size='large',
    )


@requires_post('alertprofiles-filters')
def filter_saveexpression(request):
    """Saves an expression to a filter"""
    if request.POST.get('id'):
        existing_expression = Expression.objects.get(pk=request.POST.get('id'))
        form = ExpressionForm(request.POST, instance=existing_expression)
    else:
        form = ExpressionForm(request.POST)

    if not form.is_valid():
        dictionary = {
            'id': str(form.cleaned_data["filter"].pk),
            'matchfield': str(form.cleaned_data["match_field"].pk),
        }
        qdict = QueryDict("", mutable=True)
        qdict.update(dictionary)
        request.POST = qdict
        new_message(
            request,
            form.errors,
            Messages.ERROR,
        )

        return filter_addexpression(request=request)

    filtr = form.cleaned_data['filter']

    if not account_owns_filters(get_account(request), filtr):
        return alertprofiles_response_forbidden(
            request, _('You do not own this filter.')
        )

    form.save()

    new_message(
        request,
        _('Added expression to filter %(name)s') % {'name': filtr.name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-filters-detail', args=(filtr.id,))
    )


@requires_post('alertprofiles-filters')
def filter_removeexpression(request):
    """Deletes an expression from a filter"""
    if request.POST.get('confirm'):
        expressions = request.POST.getlist('element')
        try:
            filtr = Filter.objects.get(pk=request.POST.get('perform_on'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter does not exist')
            )

        if not account_owns_filters(get_account(request), filtr):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter.')
            )

        Expression.objects.filter(pk__in=expressions).delete()

        new_message(request, _('Removed expressions'), Messages.SUCCESS)
        return HttpResponseRedirect(
            reverse('alertprofiles-filters-detail', args=(filtr.id,))
        )
    else:
        expressions = Expression.objects.filter(
            pk__in=request.POST.getlist('expression')
        )
        try:
            filtr = Filter.objects.get(pk=request.POST.get('id'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter does not exist')
            )

        if not account_owns_filters(get_account(request), filtr):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter.')
            )

        if not expressions:
            new_message(request, _('No expressions were selected'), Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-filters-detail', args=(filtr.id,))
            )

        elements = []
        for expr in expressions:
            description = _(
                "Expression, %(match_field)s %(operator)s %(value)s, used in "
                "filter %(filter)s"
            ) % {
                'match_field': expr.match_field.name,
                'operator': expr.get_operator_display(),
                'value': expr.value,
                'filter': expr.filter.name,
            }
            elements.append(
                {
                    'id': expr.id,
                    'description': description,
                    'warnings': [],
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-filters-removeexpression'),
            'active': {'filters': True},
            'subsection': {'detail': filtr.id},
            'object_list': elements,
            'perform_on': filtr.id,
            'navpath': BASE_PATH
            + [
                ('Filters', reverse('alertprofiles-filters')),
                (filtr.name, reverse('alertprofiles-filters-detail', args=(filtr.id,))),
                ('Remove expressions', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(request, 'alertprofiles/confirmation_list.html', info_dict)


def filter_group_list(request):
    """Lists the available filter groups"""
    account = get_account(request)
    admin = account.is_admin()

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'owner', '-owner', '-description', 'description']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    # Get all public filter_groups, and private filter_groups belonging to this
    # user only
    filter_groups = (
        FilterGroup.objects.select_related('owner')
        .filter(Q(owner__exact=account.pk) | Q(owner__isnull=True))
        .order_by(order_by)
    )

    active = {'filter_groups': True}
    info_dict = {
        'page': page,
        'active': active,
        'subsection': {'list': True},
        'admin': admin,
        'form_action': reverse('alertprofiles-filter_groups-remove'),
        'page_link': reverse('alertprofiles-filter_groups'),
        'order_by': order_by,
        'navpath': BASE_PATH + [('Filter groups', None)],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=filter_groups,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/filter_group_list.html',
        extra_context=info_dict,
    )(request)


def filter_group_show_form(request, filter_group_id=None, filter_group_form=None):
    """Convenience method for showing the filter group form"""
    active = {'filter_groups': True}
    page_name = 'New filter group'
    account = get_account(request)
    admin = account.is_admin()
    is_owner = True

    filter_group = None
    filter_groupcontent = None
    filters = None

    # If id is supplied we can assume that this is a already saved filter
    # group, and we can fetch it and get it's content and available filters
    if filter_group_id:
        try:
            filter_group = FilterGroup.objects.get(pk=filter_group_id)
        except FilterGroup.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter group does not exist.')
            )
        else:
            owner = filter_group.owner
            if not owner:
                new_message(
                    request,
                    _(
                        "%(fg)s is a public filter group and may be used by "
                        "other users than you."
                    )
                    % {'fg': filter_group.name},
                    Messages.WARNING,
                )
                if not admin:
                    is_owner = False
            elif owner != account:
                return alertprofiles_response_forbidden(
                    request, 'You do not have access to the requested filter group.'
                )

        filter_groupcontent = (
            FilterGroupContent.objects.select_related('filter')
            .filter(filter_group=filter_group.id)
            .order_by('priority')
        )

        filters = Filter.objects.filter(
            ~Q(pk__in=[f.filter.id for f in filter_groupcontent]),
            Q(owner__exact=account.pk) | Q(owner__isnull=True),
        ).order_by('owner', 'name')

        page_name = filter_group.name

        profiles = AlertProfile.objects.filter(
            time_periods__alert_subscriptions__filter_group=filter_group
        ).distinct()
        if profiles:
            names = ', '.join([p.name for p in profiles])
            new_message(
                request,
                _(
                    "Filter group is used in profiles: %(profiles)s. Editing "
                    "this filter group may alter those "
                    "profiles."
                )
                % {'profiles': names},
                Messages.WARNING,
            )

    # If no form is supplied we must make it
    if not filter_group_form:
        if filter_group_id:
            data = {
                'id': filter_group_id,
                'owner': filter_group.owner is not None,
                'name': filter_group.name,
                'description': filter_group.description,
            }
            filter_group_form = FilterGroupForm(data, admin=admin, is_owner=is_owner)
        else:
            filter_group_form = FilterGroupForm(
                initial={'owner': account}, admin=admin, is_owner=is_owner
            )

    if filter_group_id:
        subsection = {'detail': filter_group_id}
    else:
        subsection = {'new': True}

    info_dict = {
        'active': active,
        'subsection': subsection,
        'admin': admin,
        'owner': is_owner,
        'detail_id': filter_group_id,
        'filter_group_content': filter_groupcontent,
        'filters': filters,
        'form': filter_group_form,
        'navpath': BASE_PATH
        + [
            ('Filter groups', reverse('alertprofiles-filter_groups')),
            (page_name, None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render(request, 'alertprofiles/filter_group_form.html', info_dict)


def filter_group_detail(request, filter_group_id=None):
    """Shows the form to edit a filter group"""
    return filter_group_show_form(request, filter_group_id)


def filter_group_operator_help_modal(request):
    """Renders a modal with descriptions of all available operators"""
    return render_modal(
        request,
        'alertprofiles/_filter_group_operator_help_modal.html',
        modal_id='operator-help',
        size="large",
    )


@requires_post('alertprofiles-filter_groups')
def filter_group_save(request):
    """Saves a filter group"""
    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filter_group = None

    if request.POST.get('id'):
        try:
            filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
        except FilterGroup.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter group does not exist.')
            )

        if not account_owns_filters(account, filter_group):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter group.')
            )
    form = FilterGroupForm(request.POST, admin=admin)

    if not form.is_valid():
        detail_id = request.POST.get('id') or None
        return filter_group_show_form(request, detail_id, form)

    if request.POST.get('id'):
        filter_group.name = request.POST.get('name')
        filter_group.description = request.POST.get('description')
        filter_group.owner = owner
    else:
        filter_group = FilterGroup(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            owner=owner,
        )

    filter_group.save()
    new_message(
        request,
        _('Saved filter group %(name)s') % {'name': filter_group.name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
    )


@requires_post('alertprofiles-filters')
def filter_group_remove(request):
    """Deletes a filter group"""
    if request.POST.get('confirm'):
        filter_groups = FilterGroup.objects.filter(
            pk__in=request.POST.getlist('element')
        )

        if not account_owns_filters(get_account(request), *filter_groups):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter group.')
            )

        names = ', '.join([f.name for f in filter_groups])
        filter_groups.delete()

        new_message(
            request,
            _('Removed filter groups: %(names)s') % {'names': names},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))
    else:
        filter_groups = FilterGroup.objects.filter(
            pk__in=request.POST.getlist('filter_group')
        )

        if not account_owns_filters(get_account(request), *filter_groups):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter group.')
            )

        if not filter_groups:
            new_message(request, _('No filter groups were selected.'), Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

        elements = []
        for fgroup in filter_groups:
            subscriptions = AlertSubscription.objects.filter(filter_group=fgroup)
            time_periods = TimePeriod.objects.filter(
                alert_subscriptions__in=subscriptions
            )
            profiles = AlertProfile.objects.filter(time_periods__in=time_periods)
            warnings = []

            try:
                fgroup.owner
            except Account.DoesNotExist:
                warnings.append(
                    {
                        'message': "This is a public filter group. Deleting it "
                        "will make it unavailable for all other users "
                        "of this system.",
                    }
                )

            for profile in profiles:
                warnings.append(
                    {
                        'message': 'Used in profile %(name)s.' % {'name': profile.name},
                        'link': reverse(
                            'alertprofiles-profile-detail', args=(profile.id,)
                        ),
                    }
                )

            elements.append(
                {
                    'id': fgroup.id,
                    'description': fgroup.name,
                    'warnings': warnings,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-filter_groups-remove'),
            'active': {'filter_groups': True},
            'subsection': {'list': True},
            'object_list': elements,
            'perform_on': None,
            'navpath': BASE_PATH
            + [
                ('Filter groups', reverse('alertprofiles-filters')),
                ('Remove filter groups', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(
            request,
            'alertprofiles/confirmation_list.html',
            info_dict,
        )


@requires_post('alertprofiles-filter_groups', ('id', 'filter'))
def filter_group_addfilter(request):
    """Adds a filter to a filter group"""
    account = get_account(request)
    try:
        filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
    except FilterGroup.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested filter group does not exist.')
        )

    try:
        filtr = Filter.objects.get(pk=request.POST.get('filter'))
    except Filter.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested filter does not exist.')
        )

    operator = request.POST.get('operator')

    if not account_owns_filters(account, filter_group):
        return alertprofiles_response_forbidden(
            request, _('You do not own this filter group.')
        )

    if not operator or len(operator) != 2:
        return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filtr.id,))
        )

    # Operator is sent by POST data as a "bitfield" (it's really a string
    # pretending to be a bitfield) where position 0 represents 'include' and
    # position 1 represents 'positive'.
    include = False
    positive = False
    if operator[0] == '1':
        include = True
    if operator[1] == '1':
        positive = True

    # 'priority' is the order filters are considered when there's an alert.
    # We want to add new filters to filter_groupcontent with priority
    # incremented by one. Also double check that previously added filters
    # are ordered correctly, ie priority increments by one for each filter.
    last_priority = order_filter_group_content(filter_group)

    options = {
        'include': include,
        'positive': positive,
        'priority': last_priority + 1,
        'filter': filtr,
        'filter_group': filter_group,
    }
    new_filter = FilterGroupContent(**options)
    new_filter.save()

    new_message(
        request, _('Added filter %(name)s') % {'name': filtr.name}, Messages.SUCCESS
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
    )


@requires_post('alertprofiles-filter_groups')
def filter_group_remove_or_move_filter(request):
    """Deletes or moves around a filter within a filter group"""
    post = request.POST.copy()
    for name in request.POST:
        if name.find("=") != -1:
            attribute, value = name.split("=")
            del post[name]
            post[attribute] = value
    request.POST = post

    if request.POST.get('moveup') or request.POST.get('movedown'):
        return filter_group_movefilter(request)
    else:
        return filter_group_removefilter(request)


@requires_post('alertprofiles-filter_groups')
def filter_group_removefilter(request):
    """Removes a filter from a filter group"""
    # We are deleting filters. Show confirmation page or remove?
    if request.POST.get('confirm'):
        filter_group = FilterGroup.objects.get(pk=request.POST.get('perform_on'))
        fg_content = FilterGroupContent.objects.filter(
            pk__in=request.POST.getlist('element')
        )

        if not account_owns_filters(get_account(request), filter_group):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter group.')
            )

        filters = Filter.objects.filter(pk__in=[f.filter.id for f in fg_content])
        names = ', '.join([f.name for f in filters])
        fg_content.delete()

        # Rearrange filters
        order_filter_group_content(filter_group)

        new_message(
            request,
            _('Removed filters, %(names)s, from filter group %(fg)s.')
            % {'names': names, 'fg': filter_group.name},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
        )
    else:
        try:
            filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
        except FilterGroup.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested filter group does not exist')
            )

        filter_group_content = FilterGroupContent.objects.filter(
            pk__in=request.POST.getlist('filter'), filter_group=filter_group.id
        )

        if not account_owns_filters(get_account(request), filter_group):
            return alertprofiles_response_forbidden(
                request, _('You do not own this filter group.')
            )

        try:
            filter_group.owner
        except Account.DoesNotExist:
            new_message(
                request,
                _(
                    "You are now editing a public filter group. This will "
                    "affect all users who uses this filter group."
                ),
                Messages.WARNING,
            )

        if not filter_group_content:
            new_message(request, _('No filters were selected.'), Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
            )

        elements = []
        for content in filter_group_content:
            description = _('''Remove filter %(filter)s from %(fg)s.''') % {
                'filter': content.filter.name,
                'fg': content.filter_group.name,
            }

            elements.append(
                {
                    'id': content.id,
                    'description': description,
                }
            )

        info_dict = {
            'form_action': reverse('alertprofiles-filter_groups-removefilter'),
            'active': {'filter_groups': True},
            'subsection': {'detail': filter_group.id},
            'object_list': elements,
            'perform_on': filter_group.id,
            'navpath': BASE_PATH
            + [
                ('Filter groups', reverse('alertprofiles-filter_groups')),
                (
                    filter_group.name,
                    reverse(
                        'alertprofiles-filter_groups-detail', args=(filter_group.id,)
                    ),
                ),
                ('Remove filters', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(
            request,
            'alertprofiles/confirmation_list.html',
            info_dict,
        )


@requires_post('alertprofiles-filter_groups')
def filter_group_movefilter(request):
    """Moves a filter within a filter group"""
    account = get_account(request)

    filter_group_id = request.POST.get('id')
    try:
        filter_group = FilterGroup.objects.get(pk=filter_group_id)
    except FilterGroup.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested filter group does not exist.')
        )
    else:
        if filter_group.owner != account:
            return alertprofiles_response_forbidden(
                request, 'You do not have access to the requested filter group.'
            )

    if request.POST.get('moveup'):
        movement = -1
        direction = 'up'
        filter_id = request.POST.get('moveup')
    elif request.POST.get('movedown'):
        movement = 1
        direction = 'down'
        filter_id = request.POST.get('movedown')
    else:
        # No sensible input, just return to where we came from
        return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filter_group_id,))
        )

    try:
        filtr = FilterGroupContent.objects.get(pk=filter_id)
    except FilterGroupContent.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested filter group content does not exist.')
        )

    # Make sure content is ordered correct
    order_filter_group_content(filter_group)

    # Check if the filter we're going to swap places with exists
    try:
        other_filter = FilterGroupContent.objects.filter(
            filter_group=filter_group.id, priority=filtr.priority + movement
        )[0:1].get()
    except FilterGroupContent.DoesNotExist:
        return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
        )

    new_priority = other_filter.priority
    other_filter.priority = filtr.priority
    filtr.priority = new_priority

    other_filter.save()
    filtr.save()

    new_message(
        request,
        _('Moved filter %(filter)s %(direction)s')
        % {'direction': direction, 'filter': filtr.filter.name},
        Messages.SUCCESS,
    )

    return HttpResponseRedirect(
        reverse('alertprofiles-filter_groups-detail', args=(filter_group_id,))
    )


def matchfield_list(request):
    """Lists the available match fields"""
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )
    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'description', '-description']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    new_message(
        request,
        _(
            "Editing matchfields is black magic. Don't do it unless you know "
            "exactly what you are doing."
        ),
        Messages.ERROR,
    )

    # Get all matchfields aka. filter variables
    matchfields = MatchField.objects.all().order_by(order_by)
    info_dict = {
        'page': page,
        'active': {'matchfields': True},
        'subsection': {'list': True},
        'form_action': reverse('alertprofiles-matchfields-remove'),
        'order_by': order_by,
        'navpath': BASE_PATH
        + [
            ('Matchfields', None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return SubListView.as_view(
        queryset=matchfields,
        paginate_by=PAGINATE_BY,
        template_name='alertprofiles/matchfield_list.html',
        extra_context=info_dict,
    )(request)


def matchfield_show_form(request, matchfield_id=None, matchfield_form=None):
    """Shows the form to edit a match field"""
    active = {'matchfields': True}
    page_name = 'New matchfield'
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )

    try:
        matchfield = MatchField.objects.get(pk=matchfield_id)
    except MatchField.DoesNotExist:
        if not matchfield_form:
            matchfield_form = MatchFieldForm()
        matchfield_id = None
        matchfield_operators_id = []
    else:
        if not matchfield_form:
            matchfield_form = MatchFieldForm(instance=matchfield)
        matchfield_operators_id = [
            m_operator.type for m_operator in matchfield.operators.all()
        ]

        page_name = matchfield.name

        expressions = Expression.objects.filter(match_field=matchfield)
        filters = Filter.objects.filter(expressions__in=expressions)

        if filters:
            names = ', '.join([f.name for f in filters])
            new_message(
                request,
                _(
                    "Match field is in use in filters: %(filters)s. Editing "
                    "this match field may alter how those filters work."
                )
                % {'filters': names},
                Messages.WARNING,
            )

    operators = []
    for oper in Operator.OPERATOR_TYPES:
        selected = oper[0] in matchfield_operators_id
        operators.append({'id': oper[0], 'name': oper[1], 'selected': selected})

    if matchfield_id:
        subsection = {'detail': matchfield_id}
    else:
        subsection = {'new': True}

    new_message(
        request,
        _(
            "Editing matchfields is black magic. Don't do it unless you "
            "know exacly what you are doing."
        ),
        Messages.ERROR,
    )

    info_dict = {
        'active': active,
        'subsection': subsection,
        'detail_id': matchfield_id,
        'form': matchfield_form,
        'operators': operators,
        'owner': True,
        'navpath': BASE_PATH
        + [
            ('Matchfields', reverse('alertprofiles-matchfields')),
            (page_name, None),
        ],
        'title': 'NAV - Alert profiles',
    }

    return render(request, 'alertprofiles/matchfield_form.html', info_dict)


def matchfield_detail(request, matchfield_id=None):
    """Shows the form to edit a specific match field"""
    return matchfield_show_form(request, matchfield_id)


@requires_post('alertprofiles-matchfields')
def matchfield_save(request):
    """Saves a match field"""
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )

    try:
        if not request.POST.get('id'):
            raise MatchField.DoesNotExist
        matchfield = MatchField.objects.get(pk=request.POST.get('id'))
    except MatchField.DoesNotExist:
        form = MatchFieldForm(request.POST)
    else:
        form = MatchFieldForm(request.POST, instance=matchfield)

    # If there are some invalid values, return to form and show the errors
    if not form.is_valid():
        detail_id = request.POST.get('id') or None
        return matchfield_show_form(request, detail_id, form)

    matchfield = form.save()

    operators = []
    for oper in request.POST.getlist('operator'):
        operators.append(Operator(type=int(oper), match_field=matchfield))
    matchfield.operators.all().delete()
    matchfield.operators.add(*operators)

    new_message(
        request,
        _('Saved matchfield %(name)s') % {'name': matchfield.name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-matchfields-detail', args=(matchfield.id,))
    )


@requires_post('alertprofiles-filters')
def matchfield_remove(request):
    """Deletes a match field"""
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )

    if request.POST.get('confirm'):
        matchfields = MatchField.objects.filter(pk__in=request.POST.getlist('element'))
        names = ', '.join([m.name for m in matchfields])
        matchfields.delete()
        new_message(
            request,
            _('Removed matchfields: %(names)s') % {'names': names},
            Messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse('alertprofiles-matchfields'))
    else:
        matchfields = MatchField.objects.prefetch_related('expressions').filter(
            pk__in=request.POST.getlist('matchfield')
        )

        if not matchfields:
            new_message(request, _('No matchfields were selected'), Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-matchfields'))

        elements = []
        for match_field in matchfields:
            expressions = match_field.expressions.all()
            warnings = []
            for expr in expressions:
                warnings.append(
                    {
                        'message': 'Used in filter %(filter)s.'
                        % {'filter': expr.filter.name},
                        'link': reverse(
                            'alertprofiles-filters-detail', args=(expr.filter.id,)
                        ),
                    }
                )
            elements.append(
                {
                    'id': match_field.id,
                    'description': match_field.name,
                    'warnings': warnings,
                }
            )

        new_message(
            request,
            _(
                "It is strongly recomended that one do not remove one of the "
                "default match fields that comes preinstalled with NAV."
            ),
            Messages.NOTICE,
        )

        info_dict = {
            'form_action': reverse('alertprofiles-matchfields-remove'),
            'active': {'matchfields': True},
            'subsection': {'list': True},
            'object_list': elements,
            'perform_on': None,
            'navpath': BASE_PATH
            + [
                ('Matchfields', reverse('alertprofiles-matchfields')),
                ('Remove matchfields', None),
            ],
            'title': 'NAV - Alert profiles',
        }
        return render(
            request,
            'alertprofiles/confirmation_list.html',
            info_dict,
        )


def permission_list(request, group_id=None):
    """Lists the saved alert profiles permissions"""
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )

    groups = AccountGroup.objects.all().order_by('name')

    selected_group = None
    filter_groups = None
    permissions = None
    if group_id:
        filter_groups = FilterGroup.objects.filter(owner__isnull=True).order_by('name')
        try:
            selected_group = groups.get(pk=group_id)
        except AccountGroup.DoesNotExist:
            return alertprofiles_response_not_found(
                request, _('Requested account group does not exist.')
            )

        permissions = AccountGroup.objects.get(pk=group_id).filter_groups.all()

    active = {'permissions': True}
    info_dict = {
        'groups': groups,
        'selected_group': selected_group,
        'filter_groups': filter_groups,
        'permissions': permissions,
        'active': active,
        'navpath': BASE_PATH
        + [
            ('Permissions', None),
        ],
        'title': 'NAV - Alert profiles',
    }

    return render(request, 'alertprofiles/permissions.html', info_dict)


def permissions_help_modal(request):
    """Renders the permissions help modal"""
    return render_modal(
        request,
        'alertprofiles/_permissions_help_modal.html',
        modal_id="permissions-help",
        size="small",
    )


@requires_post('alertprofiles-permissions')
def permissions_save(request):
    """Saves an Alert Profiles permission"""
    account = get_account(request)
    if not account.is_admin():
        return alertprofiles_response_forbidden(
            request, 'Only admins can view this page.'
        )

    try:
        group = AccountGroup.objects.get(pk=request.POST.get('group'))
    except AccountGroup.DoesNotExist:
        return alertprofiles_response_not_found(
            request, _('Requested account group does not exist.')
        )

    filter_groups = FilterGroup.objects.filter(
        pk__in=request.POST.getlist('filter_group')
    )

    group.filter_groups.set(filter_groups)

    new_message(
        request,
        _('Saved permissions for group %(name)s') % {'name': group.name},
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(
        reverse('alertprofiles-permissions-detail', args=(group.id,))
    )
