# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

# TODO Check that functions that should require permission do require
# permission

# TODO Filter/filter_groups have owners, check that the account that performs
# the operation is the owner

from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list

from nav.models.profiles import Account, AccountGroup, AccountProperty, \
    AlertAddress, AlertPreference, AlertProfile, TimePeriod, \
    AlertSubscription, FilterGroupContent, Operator, Expression, \
    Filter, FilterGroup, MatchField, SMSQueue, AccountAlertQueue
from nav.django.utils import get_account, is_admin
from nav.web.templates.AlertProfilesTemplate import AlertProfilesTemplate
from nav.web.message import new_message, Messages

from nav.web.alertprofiles.forms import *
from nav.web.alertprofiles.utils import *
from nav.web.alertprofiles.shortcuts import alertprofiles_response_forbidden, \
    alertprofiles_response_not_found

_ = lambda a: a

BASE_PATH = [
    ('Home', '/'),
    ('Alert profiles', '/alertprofiles/'),
]

PAGINATE_BY = 25

def overview(request):
    account = get_account(request)

    # Get information about user
    groups = account.accountgroup_set.all()
    try:
        active_profile = account.get_active_profile()
    except ObjectDoesNotExist:
        active_profile = None

    if not active_profile:
        new_message(request, _('There\'s no active profile set.'), Messages.NOTICE)
        subscriptions = None
    else:
        periods = TimePeriod.objects.filter(profile=active_profile).order_by('start')
        subscriptions = alert_subscriptions_table(periods)

    # Get information about users privileges
    sms_privilege = account.has_perm('alert_by', 'sms')

    filter_dict = {'group_permissions__in': [g.id for g in groups]}
    filter_groups = FilterGroup.objects.filter(**filter_dict).order_by('name')

    try:
        language = AccountProperty.objects.get(
            account=account,
            property='language'
        )
    except AccountProperty.DoesNotExist:
        language = AccountProperty(account=account, property='language', value='en')

    language_form = AccountPropertyForm(
        instance=language,
        property='language',
        values=[('en', 'English'), ('no', 'Norwegian')]
    )

    info_dict = {
            'active': {'overview': True},
            'groups': groups,
            'active_profile': active_profile,
            'sms_privilege': sms_privilege,
            'filter_groups': filter_groups,
            'language_form': language_form,
            'alert_subscriptions': subscriptions,
            'navpath': [
                ('Home', '/'),
                ('Alert profiles', None),
            ],
            'title': 'NAV - Alert profiles',
        }
    return render_to_response(
            'alertprofiles/account_detail.html',
            info_dict,
            RequestContext(request),
        )

def profile(request):
    account = get_account(request)

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    try:
        active_profile = account.alertpreference.active_profile
    except:
        active_profile = None

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
            'navpath': BASE_PATH+[('Profiles', None)],
            'title': 'NAV - Alert profiles',
        }
    return object_list(
            request,
            queryset=profiles,
            paginate_by=PAGINATE_BY,
            page=page,
            template_name='alertprofiles/profile.html',
            extra_context=info_dict,
        )

def profile_show_form(request, profile_id=None, profile_form=None, time_period_form=None):
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
                request,
                _('The requested profile does not exist.'),
                Messages.ERROR
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
        'navpath': BASE_PATH+[
            ('Profiles', reverse('alertprofiles-profile')),
            (page_name, None)
        ],
        'title': 'NAV - Alert profiles',
    }
    return render_to_response(
        'alertprofiles/profile_detail.html',
        info_dict,
        RequestContext(request),
    )

def profile_detail(request, profile_id=None):
    return profile_show_form(request, profile_id)

def profile_new(request):
    return profile_show_form(request)

def profile_save(request):
    if not request.method == 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    messages = Messages(request)
    account = get_account(request)
    profile_form = None

    if request.POST.get('id'):
        try:
            profile = AlertProfile.objects.get(pk=request.POST.get('id'))
        except AlertProfile.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested profile does not exist'))

        if profile.account != account:
            return alertprofiles_response_forbidden(request, _('You do not own this profile.'))
    else:
        profile = AlertProfile(account=account)

    profile_form = AlertProfileForm(request.POST, instance=profile)

    if not profile_form.is_valid():
        detail_id = request.POST.get('id') or None
        return profile_show_form(request, detail_id, profile_form)

    profile = profile_form.save()

    if AlertProfile.objects.filter(account=account).count() == 1:
        # No other profile, might as well set active profile to this
        # profile.
        # A bit magic, but removes a step for the user to perform.
        try:
            preference = AlertPreference.objects.get(account=account)
        except AlertPreference.DoesNotExist:
            preference = AlertPreference(account=account, active_profile=profile)
        else:
            preference.active_profile = profile
        preference.save()
        messages.append({
            'message': _('''Active profile automatically set to %(profile)s''') % {
                'profile': profile.name,
            },
            'type': Messages.NOTICE,
        })

    # Should we make some time periods from a template?
    if 'template' in request.POST:
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

                # Make the time periods. We're only interested in the values of
                # the dictionary, not the keys.
                for start_time in periods.values():
                    p = TimePeriod(profile=profile, start=start_time,
                        valid_during=valid_during)
                    p.save()

    messages.append({
        'message': _('Saved profile %(profile)s') % {'profile': profile.name},
        'type': Messages.SUCCESS,
    })
    messages.save()
    return HttpResponseRedirect(reverse('alertprofiles-profile-detail', args=(profile.id,)))

def profile_remove(request):
    if not request.method == 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    post = request.POST.copy()
    for data in post:
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

        for p in profiles:
            if p.account != account:
                return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

        profile_names = ', '.join([p.name for p in profiles])
        profiles.delete()

        new_message(
            request,
            _('Deleted profiles: %(profiles)s') % {'profiles': profile_names},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-profile'))
    else:
        active_profile = AlertPreference.objects.get(account=account).active_profile
        profiles = AlertProfile.objects.filter(pk__in=request.POST.getlist('profile'))

        if len(profiles) == 0:
            new_message(
                request,
                _('No profiles were selected.'),
                Messages.NOTICE)
            HttpResponseRedirect(reverse('alertprofiles-profile'))

        elements = []
        for p in profiles:
            warnings = []
            if p.account != account:
                return alertprofiles_response_forbidden(request, _('You do not own this profile.'))
            if p == active_profile:
                warnings.append({'message': u'This is the currently active profile.'})

            queued = AccountAlertQueue.objects.filter(
                subscription__time_period__profile=p).count()
            if queued > 0:
                warnings.append({
                'message': u'''There are %(queued)s queued alerts on a
                    subscription under this profile. Deleting this time period
                    will delete those alerts as well.''' % {
                        'queued': queued,
                    }
                })

            elements.append({
                'id': p.id,
                'description': p.name,
                'warnings': warnings,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-profile-remove'),
                'active': {'profile': True},
                'subsection': {'list': True},
                'elements': elements,
                'perform_on': None,
                'navpath': BASE_PATH+[
                    ('Profiles', reverse('alertprofiles-profile')),
                    ('Remove profiles', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def profile_activate(request):
    if not request.method == 'POST' or not request.POST.get('activate'):
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    account = get_account(request)

    try:
        profile = AlertProfile.objects.get(
            pk=request.POST.get('activate'),
            account=account
        )
    except AlertProfile.DoesNotExist:
        new_message(
            request,
            _('The profile you are trying to activate does not exist'),
            Messages.ERROR
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
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-profile'))

def profile_deactivate(request):
    if request.method != 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

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
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-profile'))

def profile_time_period(request, time_period_id, time_period_form=None):
    time_period = TimePeriod.objects.get(pk=time_period_id)
    profile = time_period.profile

    if not time_period_form:
        time_period_form = TimePeriodForm(instance=time_period)

    info_dict = {
        'active': {'profile': True},
        'subsection': {'detail': time_period.profile.id, 'timeperiod': time_period.id},
        'time_period': time_period,
        'time_period_form': time_period_form,
        'navpath': BASE_PATH+[
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            ('Edit time period', None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render_to_response(
        'alertprofiles/timeperiod_edit.html',
        info_dict,
        RequestContext(request),
    )

def profile_time_period_add(request):
    if request.method != 'POST' or not request.POST.get('profile'):
        new_message(request, _('Required post data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    account = get_account(request)
    profile = None
    try:
        profile = AlertProfile.objects.get(pk=request.POST.get('profile'))
    except AlertProfile.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested profile does not exist.'))

    if profile.account != account:
        return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

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
        _('Saved time period %(time)s for %(during)s to profile %(profile)s') % {
            'time': time_period.start,
            'during': time_period.get_valid_during_display(),
            'profile': profile.name
        },
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(reverse('alertprofiles-profile-detail', args=(profile.id,)))

def profile_time_period_remove(request):
    if not request.method == 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    if request.POST.get('confirm'):
        account = get_account(request)
        elements = request.POST.getlist('element')

        time_periods = TimePeriod.objects.filter(pk__in=elements)
        first = True
        for t in time_periods:
            if first:
                # We only check profile once and assume it's the same for all.
                # It's only used to redirect the user after deleting all the
                # periods anyways.
                profile = t.profile
                first = False
            if t.profile.account != account:
                return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

        time_periods_name = ', '.join(['%s for %s' % (
                t.start, t.get_valid_during_display()
            ) for t in time_periods])
        time_periods.delete()

        new_message(
            request,
            'Removed time periods: %(names)s' % {'names': time_periods_name},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse(
            'alertprofiles-profile-detail',
            args=(profile.id,)
        ))
    else:
        account = get_account(request)
        time_periods = TimePeriod.objects.filter(pk__in=request.POST.getlist('period'))
        profile = AlertProfile.objects.get(pk=request.POST.get('profile'))
        try:
            active_profile = AlertPreference.objects.get(account=account).active_profile
        except:
            pass
        else:
            if profile == active_profile:
                new_message(
                    request,
                    _('''Time periods are used in profile %(profile)s,
                    which is the current active profile.''') % {
                        'profile': profile.name,
                    },
                    Messages.WARNING
                )

        if len(time_periods) == 0:
            new_message(
                request,
                _('No time periods were selected.'),
                Messages.NOTICE
            )
            return HttpResponseRedirect(
                reverse('alertprofiles-profile-detail', args=(profile.id,)))

        elements = []
        for t in time_periods:
            if t.profile.account != account:
                # Even though we assume profile is the same for GUI-stuff, we
                # can't do that when it comes to permissions.
                return alertprofiles_response_forbidden(request, _('You do not own this profile.'))
            description = _(u'From %(time)s for %(profile)s during %(valid_during)s') % {
                'time': t.start,
                'profile': t.profile.name,
                'valid_during': t.get_valid_during_display(),
            }

            queued = AccountAlertQueue.objects.filter(subscription__time_period=t).count()
            warnings = []
            if queued > 0:
                warnings.append({
                'message': u'''There are %(queued)s queued alerts on a
                    subscription under this time period. Deleting this time period
                    will delete those alerts as well.''' % {
                        'queued': queued,
                    }
                })
            elements.append({
                'id': t.id,
                'description': description,
                'warnings': warnings,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-profile-timeperiod-remove'),
                'active': {'profile': True},
                'subsection': {'detail': profile.id},
                'elements': elements,
                'navpath': BASE_PATH+[
                    ('Profiles', reverse('alertprofiles-profile')),
                    (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
                    ('Remove time periods', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def profile_time_period_setup(request, time_period_id=None):
    if not time_period_id:
        new_message(request, _('No time period were specified'), Messages.ERROR)
        redirect_url = reverse('alertprofiles-profile')
        return HttpResponseRedirect(redirect_url)

    account = get_account(request)

    time_period = TimePeriod.objects.get(pk=time_period_id)
    subscriptions = AlertSubscription.objects.select_related(
        'alert_address', 'filter_group'
    ).filter(time_period=time_period).order_by('alert_address', 'filter_group')
    profile = time_period.profile

    if account != profile.account:
        return alertprofiles_response_forbidden(request, _('You do not have access to this profile.'))

    editing = False
    if request.method == 'POST' and request.POST.get('time_period'):
        time_period_form = AlertSubscriptionForm(request.POST, time_period=time_period)
        if request.POST.get('id'):
            editing = True
    else:
        time_period_form = AlertSubscriptionForm(time_period=time_period)

    info_dict = {
        'form': time_period_form,
        'subscriptions': subscriptions,
        'time_period': time_period,
        'active': {'profile': True},
        'subsection': {'detail': profile.id, 'subscriptions': time_period.id},
        'editing': editing,
        'num_addresses': AlertAddress.objects.filter(account=account).count(),
        'num_filter_groups': FilterGroup.objects.filter(
            Q(owner=account) | Q(owner__isnull=True)).count(),
        'navpath': BASE_PATH+[
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            (unicode(time_period.start) + u', ' + time_period.get_valid_during_display(), None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render_to_response(
        'alertprofiles/subscription_form.html',
        info_dict,
        RequestContext(request),
    )

def profile_time_period_subscription_add(request):
    if request.method != 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

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
        return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

    subscription = form.save()

    new_message(
        request,
        _('Saved alert subscription for filter group %(fg)s to period %(time)s for %(during)s') % {
            'fg': subscription.filter_group.name,
            'time': time_period.start,
            'during': time_period.get_valid_during_display(),
        },
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(reverse(
        'alertprofiles-profile-timeperiod-setup',
        args=(time_period.id,)
    ))

def profile_time_period_subscription_edit(request, subscription_id=None):
    if not subscription_id:
        new_message(request, _('No alert subscription specified'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofile-profile'))

    account = get_account(request)

    subscription = AlertSubscription.objects.select_related(
        'time_period', 'time_period__profile'
    ).get(pk=subscription_id)
    form = AlertSubscriptionForm(instance=subscription, time_period=subscription.time_period)
    profile = subscription.time_period.profile

    if account != profile.account:
        return alertprofiles_response_forbidden(request, _('You do not have access to this profile.'))

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
            Q(owner=account) | Q(owner__isnull=True)).count(),
        'navpath': BASE_PATH+[
            ('Profiles', reverse('alertprofiles-profile')),
            (profile.name, reverse('alertprofiles-profile-detail', args=(profile.id,))),
            (
                unicode(subscription.time_period.start) + u', ' + subscription.time_period.get_valid_during_display(),
                reverse('alertprofiles-profile-timeperiod-setup', args=(subscription.time_period.id,))
            ),
            ('Edit subscription', None)
        ],
        'title': 'NAV - Alert profiles',
    }
    return render_to_response(
        'alertprofiles/subscription_form.html',
        info_dict,
        RequestContext(request),
    )

def profile_time_period_subscription_remove(request):
    if not request.method == 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    if request.POST.get('confirm'):
        account = get_account(request)
        subscriptions = request.POST.getlist('element')
        period = None

        try:
            period = TimePeriod.objects.get(pk=request.POST.get('perform_on'))
        except TimePeriod.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested time period does not exist'))

        if period.profile.account != account:
            return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

        AlertSubscription.objects.filter(pk__in=subscriptions).delete()

        new_message(request, _('Removed alert subscriptions.'), Messages.SUCCESS)
        return HttpResponseRedirect(reverse(
            'alertprofiles-profile-timeperiod-setup',
            args=(period.id,)
        ))
    else:
        account = get_account(request)
        subscriptions = AlertSubscription.objects.filter(pk__in=request.POST.getlist('subscription'))
        period = None

        try:
            period = TimePeriod.objects.get(pk=request.POST.get('id'))
        except TimePeriod.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested time period does not exist'))

        if period.profile.account != account:
            return alertprofiles_response_forbidden(request, _('You do not own this profile.'))

        if len(subscriptions) == 0:
            new_message(
                request,
                _('No alert subscriptions were selected.'),
                Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-profile-timeperiod-setup', args=(period.id,)))

        # Make tuples, (id, description_string) for the confirmation page
        elements = []
        for s in subscriptions:
            warnings = []
            queued = AccountAlertQueue.objects.filter(subscription=s).count()
            if queued > 0:
                warnings.append({
                    'message': u'''There are %(queued)s queued alert(s) on this
                        subscription.  If you delete this subscription, those
                        alerts will be deleted as well.''' % {
                            'queued': queued,
                        },
                })

            description = _(u'''Watch %(fg)s, send to %(address)s %(dispatch)s,
                from %(time)s for %(profile)s during %(during)s''') % {
                'fg': s.filter_group.name,
                'address': s.alert_address.address,
                'dispatch': s.get_type_display(),
                'time': s.time_period.start,
                'profile': s.time_period.profile.name,
                'during': s.time_period.get_valid_during_display(),
            }

            elements.append({
                'id': s.id,
                'description': description,
                'warnings': warnings,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-profile-timeperiod-subscription-remove'),
                'active': {'profile': True},
                'subsection': {'detail': period.profile.id, 'subscriptions': period.id},
                'elements': elements,
                'perform_on': period.id,
                'navpath': BASE_PATH+[
                    ('Profiles', reverse('alertprofiles-profile')),
                    (period.profile.name, reverse('alertprofiles-profile-detail', args=(period.profile.id,))),
                    (
                        unicode(period.start) + u', ' + period.get_valid_during_display(),
                        reverse('alertprofiles-profile-timeperiod-setup', args=(period.id,))
                    ),
                    ('Remove subscriptions', None)
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def address_list(request):
    account = get_account(request)

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['address', '-address', 'type', '-type']
    order_by = request.GET.get('order_by', 'address').lower()
    if order_by not in valid_ordering:
        order_by = 'address'

    address = AlertAddress.objects.select_related(
        'type'
    ).filter(account=account.pk).order_by(order_by)

    info_dict = {
            'active': {'address': True},
            'subsection': {'list': True},
            'form_action': reverse('alertprofiles-address-remove'),
            'page_link': reverse('alertprofiles-address'),
            'order_by': order_by,
            'navpath': BASE_PATH+[('Address', None)],
            'title': 'NAV - Alert profiles',
        }
    return object_list(
            request,
            queryset=address,
            paginate_by=PAGINATE_BY,
            page=page,
            template_name='alertprofiles/address_list.html',
            extra_context=info_dict,
        )

def address_show_form(request, address_id=None, address_form=None):
    account = get_account(request)
    page_name = 'New address'
    detail_id = None
    address = None

    if address_id:
        try:
            address = AlertAddress.objects.get(pk=address_id)
        except AlertAddress.DoesNotExist:
            return alertprofiles_response_not_found(
                request,
                'The requested alert address does not exist.'
            )
        else:
            # Check if we really are the owner of the address
            if address.account != account:
                return alertprofiles_response_forbidden(
                    request,
                    'You do not have access to this alert address.'
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
        'navpath': BASE_PATH+[
            ('Address', reverse('alertprofiles-address')),
            (page_name, None),
        ],
        'title': 'NAV - Alert profiles',
    }
    return render_to_response(
        'alertprofiles/address_form.html',
        info_dict,
        RequestContext(request),
    )

def address_detail(request, address_id=None):
    return address_show_form(request, address_id)

def address_save(request):
    if request.method != 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-address'))

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
                return alertprofiles_response_forbidden(request, _('You do not own this address.'))
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
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-address-detail', args=(address.id,)))

def address_remove(request):
    if not request.method == 'POST':
        new_message(request, _('There was no post-data'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-address'))

    account = get_account(request)
    if request.POST.get('confirm'):
        addresses = AlertAddress.objects.filter(pk__in=request.POST.getlist('element'))

        for a in addresses:
            if a.account != account:
                return alertprofiles_response_forbidden(request, _('You do not own this address.'))

        subscriptions = AlertSubscription.objects.filter(alert_address__in=addresses)
        if len(subscriptions) > 0:
            for s in subscriptions:
                new_message(
                    request,
                    _('''Address %(address)s were used in a subscription,
                    %(during)s from %(start)s watch %(fg)s for profile
                    %(profile)s.  The subscription were removed as a side
                    effect of deleting this address.''') % {
                        'address': s.alert_address.address,
                        'start': s.time_period.start,
                        'during': s.time_period.get_valid_during_display(),
                        'profile': s.time_period.profile.name,
                        'fg': s.filter_group.name,
                    },
                    Messages.NOTICE
                )

        names = ', '.join([a.address for a in addresses])
        addresses.delete()

        new_message(
            request,
            _('Removed addresses: %(names)s') % {'names': names},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-address'))
    else:
        addresses = AlertAddress.objects.filter(pk__in=request.POST.getlist('address'))

        if len(addresses) == 0:
            new_message(
                request,
                _('No addresses were selected'),
                Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-address'))

        elements = []
        for a in addresses:
            if a.account != account:
                return alertprofiles_response_forbidden(request, _('You do not own this address.'))

            warnings = []
            subscriptions = AlertSubscription.objects.filter(
                alert_address=a
            ).select_related('filter_group', 'time_period', 'time_period__profile')
            for s in subscriptions:
                warnings.append({
                    'message': u'''Address used in subscription "watch %(fg)s
                        from %(time)s for profile %(profile)s".''' % {
                            'fg': s.filter_group.name,
                            'time': s.time_period.start,
                            'profile': s.time_period.profile.name,
                        },
                    'link': reverse('alertprofiles-profile-detail', args=(s.time_period.profile.id,)),
                })

                queued = AccountAlertQueue.objects.filter(subscription=s).count()
                if queued > 0:
                    warnings.append({
                    'message': u'''There are %(queued)s queued alerts on this
                        subscription. Deleting this time period will delete
                        those alerts as well.''' % {
                            'queued': queued,
                        }
                    })

            description = _(u'''%(type)s address %(address)s''') % {
                'type': a.type.name,
                'address': a.address,
            }

            elements.append({
                'id': a.id,
                'description': description,
                'warnings': warnings,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-address-remove'),
                'active': {'address': True},
                'subsection': {'list': True},
                'elements': elements,
                'perform_on': None,
                'navpath': BASE_PATH+[
                    ('Address', reverse('alertprofiles-address')),
                    ('Remove addresses', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def language_save(request):
    if request.method != 'POST' or not request.POST.get('value'):
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-profile'))

    account = get_account(request)
    language = None

    # Try to fetch language property. If it doesn't exist we must make it.
    try:
        language = AccountProperty.objects.get(
            account=account,
            property='language'
        )
    except AccountProperty.DoesNotExist:
        language = AccountProperty(account=account, property='language', value='en')

    value = request.POST.get('value')
    language.value = value
    language.save()

    new_message(request, _('Changed language'), Messages.SUCCESS)
    return HttpResponseRedirect(reverse('alertprofiles-overview'))

def sms_list(request):
    account = get_account(request)
    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = [
        'time', '-time', 'time_sent', '-time_sent', 'phone', '-phone',
        'message', '-message', 'severity', '-severity', 'sent', '-sent',
    ]
    order_by = request.GET.get('order_by', 'time').lower()
    if order_by not in valid_ordering:
        order_by = 'time'

    # NOTE Old versions of alert engine may not have set account.
    sms = SMSQueue.objects.filter(account=account).order_by(order_by)

    info_dict = {
        'active': {'sms': True},
        'page_link': reverse('alertprofiles-sms'),
        'order_by': order_by,
        'natpath': BASE_PATH+[('SMS', None)],
        'title': 'NAV - Alert profiles',
    }
    return object_list(
        request,
        queryset=sms,
        paginate_by=PAGINATE_BY,
        page=page,
        template_name='alertprofiles/sms_list.html',
        extra_context=info_dict,
    )

def filter_list(request):
    account = get_account(request)
    admin = is_admin(account)

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'owner', '-owner']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    # Get all public filters, and private filters belonging to this user only
    filters = Filter.objects.select_related(
        'owner'
    ).filter(
        Q(owner=account) | Q(owner__isnull=True)
    ).order_by(order_by)

    active = {'filters': True}
    info_dict = {
            'active': active,
            'subsection': {'list': True},
            'admin': admin,
            'form_action': reverse('alertprofiles-filters-remove'),
            'page_link': reverse('alertprofiles-filters'),
            'order_by': order_by,
            'navpath': BASE_PATH+[('Filters', None)],
            'title': 'NAV - Alert profiles',
        }
    return object_list(
            request,
            queryset=filters,
            paginate_by=PAGINATE_BY,
            page=page,
            template_name='alertprofiles/filter_list.html',
            extra_context=info_dict,
        )

def filter_show_form(request, filter_id=None, filter_form=None):
    '''Convenience method for showing the filter form'''
    active = {'filters': True}
    page_name = 'New filter'
    account = get_account(request)
    admin = is_admin(account)
    is_owner = True

    filter = None
    expressions = None
    matchfields = None

    # We assume that if no filter_id is set this filter has not been saved
    if filter_id:
        try:
            filter = Filter.objects.get(pk=filter_id)
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(
                request,
                _('Requested filter does not exist.')
            )
        else:
            owner = filter.owner
            if not owner:
                new_message(
                    request,
                    _('''%(filter)s is a public filter and may be used by
                        other users than you.''') % {
                            'filter': filter.name,
                        },
                    Messages.WARNING,
                )
                if not admin:
                    is_owner = False
            elif owner != account:
                return alertprofiles_response_forbidden(
                    request,
                    _('You do not have acccess to the requested filter.')
                )

        matchfields = MatchField.objects.all().order_by('name')
        # Get all matchfields (many-to-many connection by table Expression)
        expressions = Expression.objects.select_related(
            'match_field'
        ).filter(filter=filter_id).order_by('match_field__name')

        for e in expressions:
            if e.operator == Operator.IN:
                e.value = e.value.split("|")

        # Check if filter is used by any filter groups
        filter_groups = FilterGroupContent.objects.filter(filter=filter)
        if len(filter_groups) > 0:
            fg_names = ', '.join([f.filter_group.name for f in filter_groups])
            new_message(
                request,
                _('''%(filter)s is used in the filter groups:
                %(filter_groups)s. Editing this filter will also change how those
                filter group works.''') % {
                    'filter': filter.name,
                    'filter_groups': fg_names
                },
                Messages.WARNING
            )

        page_name = filter.name

    # If no form is supplied we must make one
    if not filter_form:
        if filter_id:
            filter_form = FilterForm(instance=filter, admin=admin, is_owner=is_owner)
        else:
            filter_form = FilterForm(initial={'owner': account}, admin=admin, is_owner=is_owner)

    if filter_id:
        subsection = {'detail': filter_id}
    else:
        subsection = {'new': True}

    return render_to_response(
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
                'navpath': BASE_PATH+[
                    ('Filters', reverse('alertprofiles-filters')),
                    (page_name, None),
                ],
                'title': 'NAV - Alert profiles',
            },
            RequestContext(request),
        )

def filter_detail(request, filter_id=None):
    return filter_show_form(request, filter_id)

def filter_save(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filter = None

    # Build a form. Different values depending on if we are updating or
    # making a new filter
    if request.POST.get('id'):
        try:
            filter = Filter.objects.get(pk=request.POST.get('id'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested filter does not exist.'))

        if not account_owns_filters(account, filter):
            return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

        form = FilterForm(request.POST, instance=filter, admin=admin)
    else:
        form = FilterForm(request.POST, admin=admin)

    # If there are some invalid values, return to form and show the errors
    if not form.is_valid():
        detail_id = request.POST.get('id') or None
        return filter_show_form(request, detail_id, form)

    # Set the fields in Filter to the submited values
    if request.POST.get('id'):
        filter.name = request.POST.get('name')
        filter.owner = owner
    else:
        filter = Filter(name=request.POST.get('name'), owner=owner)

    # Save the filter
    filter.save()

    new_message(
        request,
        _('Saved filter %(name)s') % {'name': filter.name},
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))

def filter_remove(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        filters = Filter.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), *filters):
            return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

        names = ', '.join([f.name for f in filters])
        filters.delete()

        new_message(
            request,
            'Removed filters: %(names)s' % {'names': names},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-filters'))
    else:
        filters = Filter.objects.filter(pk__in=request.POST.getlist('filter'))

        if not account_owns_filters(get_account(request), *filters):
            return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

        if len(filters) == 0:
            new_message(
                request,
                _('No filters were selected.'),
                Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-filters'))

        elements = []
        for f in filters:
            warnings = []
            try:
                owner = f.owner
            except Account.DoesNotExist:
                warnings.append({'message': u'''This filter is public. Deleting
                    it will make it unavailable for all users of this system.'''})

            filter_groups = FilterGroup.objects.filter(filter_groupcontent__filter=f)
            for fg in filter_groups:
                warnings.append({
                    'message': u'Used in filter group %(name)s.' % {'name': fg.name},
                    'link': reverse('alertprofiles-filter_groups-detail', args=(fg.id,)),
                })

            elements.append({
                'id': f.id,
                'description': f.name,
                'warnings': warnings,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-filters-remove'),
                'active': {'filters': True},
                'subsection': {'list': True},
                'elements': elements,
                'perform_on': None,
                'navpath': BASE_PATH+[
                    ('Filters', reverse('alertprofiles-filters')),
                    ('Remove filters', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def filter_addexpression(request):
    if not request.method == 'POST' or not request.POST.get('id') or not request.POST.get('matchfield'):
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    filter = None
    try:
        filter = Filter.objects.get(pk=request.POST.get('id'))
    except Filter.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested filter does not exist'))

    matchfield = None
    try:
        matchfield = MatchField.objects.get(pk=request.POST.get('matchfield'))
    except MatchField.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested match field does not exist'))

    initial = {'filter': filter.id, 'match_field': matchfield.id}
    form = ExpressionForm(match_field=matchfield, initial=initial)

    if not account_owns_filters(get_account(request), filter):
        return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

    # Check if there's more values than we can show in the list
    list_limited = False
    if matchfield.show_list and form.number_of_choices > matchfield.list_limit:
        list_limited = True

    active = {'filters': True}
    info_dict = {
            'form': form,
            'active': active,
            'subsection': {'detail': filter.id},
            'filter': filter,
            'matchfield': matchfield,
            'list_limited': list_limited,
            'navpath': BASE_PATH+[
                ('Filters', reverse('alertprofiles-filters')),
                (filter.name, reverse('alertprofiles-filters-detail', args=(filter.id,))),
                ('Add expression', None)
            ],
            'title': 'NAV - Alert profiles',
        }
    return render_to_response(
            'alertprofiles/expression_form.html',
            info_dict,
            RequestContext(request),
        )

def filter_saveexpression(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    # Get the MatchField, Filter and Operator objects associated with the
    # input POST-data
    filter = Filter.objects.get(pk=request.POST.get('filter'))
    type = request.POST.get('operator')
    match_field = MatchField.objects.get(pk=request.POST.get('match_field'))
    operator = Operator.objects.get(type=type, match_field=match_field.pk)

    if not account_owns_filters(get_account(request), filter):
        return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

    # Get the value
    value = ""
    if operator.type == Operator.IN:
        # If input was a multiple choice list we have to join each option
        # in one string, where each option is separated by a | (pipe).
        # If input was a IP adress we should replace space with | (pipe).
        # FIXME We might want some data checks here
        if match_field.data_type == MatchField.IP:
            # FIXME We might want to check that it is a valid IP adress.
            # If we do so, we need to remember both IPv4 and IPv6
            value = request.POST.get('value').replace(' ', '|')
        else:
            value = "|".join([value for value in request.POST.getlist('value')])
    else:
        value = request.POST.get('value')

    expression = Expression(
            filter=filter,
            match_field=match_field,
            operator=operator.type,
            value=value,
        )
    expression.save()
    new_message(
        request,
        _('Added expression to filter %(name)s') % {'name': filter.name},
        Messages.SUCCESS
   )
    return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))

def filter_removeexpression(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        expressions = request.POST.getlist('element')
        filter = None
        try:
            filter = Filter.objects.get(pk=request.POST.get('perform_on'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested filter does not exist'))

        if not account_owns_filters(get_account(request), filter):
            return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

        Expression.objects.filter(pk__in=expressions).delete()

        new_message(request, _('Removed expressions'), Messages.SUCCESS)
        return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))
    else:
        expressions = Expression.objects.filter(pk__in=request.POST.getlist('expression'))
        filter = None
        try:
            filter = Filter.objects.get(pk=request.POST.get('id'))
        except Filter.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested filter does not exist'))

        if not account_owns_filters(get_account(request), filter):
            return alertprofiles_response_forbidden(request, _('You do not own this filter.'))

        if len(expressions) == 0:
            new_message(
                request,
                _('No expressions were selected'),
                Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-filters-detail', args=(filter.id,)))

        elements = []
        for e in expressions:
            description = _(u'''Expression, %(match_field)s %(operator)s
                %(value)s, used in filter %(filter)s''') % {
                'match_field': e.match_field.name,
                'operator': e.get_operator_display(),
                'value': e.value,
                'filter': e.filter.name,
            }

            elements.append({
                'id': e.id,
                'description': description,
                'warnings': [],
            })

        info_dict = {
                'form_action': reverse('alertprofiles-filters-removeexpression'),
                'active': {'filters': True},
                'subsection': {'detail': filter.id},
                'elements': elements,
                'perform_on': filter.id,
                'navpath': BASE_PATH+[
                    ('Filters', reverse('alertprofiles-filters')),
                    (filter.name, reverse('alertprofiles-filters-detail', args=(filter.id,))),
                    ('Remove expressions', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def filter_group_list(request):
    account = get_account(request)
    admin = is_admin(account)

    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'owner', '-owner', '-description', 'description']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    # Get all public filter_groups, and private filter_groups belonging to this
    # user only
    filter_groups = FilterGroup.objects.select_related(
        'owner'
    ).filter(
            Q(owner__exact=account.pk) | Q(owner__isnull=True)
    ).order_by(order_by)

    active = {'filter_groups': True}
    info_dict = {
            'active': active,
            'subsection': {'list': True},
            'admin': admin,
            'form_action': reverse('alertprofiles-filter_groups-remove'),
            'page_link': reverse('alertprofiles-filter_groups'),
            'order_by': order_by,
            'navpath': BASE_PATH+[
                ('Filter groups', None)
            ],
            'title': 'NAV - Alert profiles',
        }
    return object_list(
            request,
            queryset=filter_groups,
            paginate_by=PAGINATE_BY,
            page=page,
            template_name='alertprofiles/filter_group_list.html',
            extra_context=info_dict,
        )

def filter_group_show_form(request, filter_group_id=None, filter_group_form=None):
    '''Convenience method for showing the filter group form'''
    active = {'filter_groups': True}
    page_name = 'New filter group'
    account = get_account(request)
    admin = is_admin(account)
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
            return alertprofiles_response_not_found(request, _('Requested filter group does not exist.'))
        else:
            owner = filter_group.owner
            if not owner:
                new_message(
                    request,
                    _('''%(fg)s is a public filter group and may be used by other
                    users than you.''') % {
                        'fg': filter_group.name,
                    },
                    Messages.WARNING
                )
                if not admin:
                    is_owner = False
            elif owner != account:
                return alertprofiles_response_forbidden(
                    request,
                    'You do not have access to the requested filter group.'
                )

        filter_groupcontent = FilterGroupContent.objects.select_related(
            'filter'
        ).filter(
            filter_group=filter_group.id
        ).order_by('priority')

        filters = Filter.objects.filter(
            ~Q(pk__in=[f.filter.id for f in filter_groupcontent]),
            Q(owner__exact=account.pk) | Q(owner__isnull=True)
        ).order_by('owner', 'name')

        page_name = filter_group.name

        profiles = AlertProfile.objects.filter(
            timeperiod__alertsubscription__filter_group=filter_group
        ).distinct()
        if len(profiles) > 0:
            names = ', '.join([p.name for p in profiles])
            new_message(
                request,
                _('''Filter group is used in profiles: %(profiles)s. Editing
                this filter group may alter those profiles.''') % {
                    'profiles': names,
                },
                Messages.WARNING
            )

    # If no form is supplied we must make it
    if not filter_group_form:
        if filter_group_id:
            filter_group_form = FilterGroupForm(instance=filter_group, admin=admin, is_owner=is_owner)
        else:
            filter_group_form = FilterGroupForm(initial={'owner': account}, admin=admin, is_owner=is_owner)

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
            'navpath': BASE_PATH+[
                ('Filter groups', reverse('alertprofiles-filter_groups')),
                (page_name, None),
            ],
            'title': 'NAV - Alert profiles',
        }
    return render_to_response(
            'alertprofiles/filter_group_form.html',
            info_dict,
            RequestContext(request),
        )

def filter_group_detail(request, filter_group_id=None):
    return filter_group_show_form(request, filter_group_id)

def filter_group_save(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filter_group = None

    if request.POST.get('id'):
        try:
            filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
        except FilterGroup.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested filter group does not exist.'))

        if not account_owns_filters(account, filter_group):
            return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))
        form = FilterGroupForm(request.POST, instance=filter_group, admin=admin)
    else:
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
                owner=owner
            )

    filter_group.save()
    new_message(
        request,
        _('Saved filter group %(name)s') % {'name': filter_group.name},
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,)))

def filter_group_remove(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        filter_groups = FilterGroup.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), *filter_groups):
            return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))

        names = ', '.join([f.name for f in filter_groups])
        filter_groups.delete()

        new_message(
            request,
            _('Removed filter groups: %(names)s') % {'names': names},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))
    else:
        filter_groups = FilterGroup.objects.filter(pk__in=request.POST.getlist('filter_group'))

        if not account_owns_filters(get_account(request), *filter_groups):
            return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))

        if len(filter_groups) == 0:
            new_message(
                request,
                _('No filter groups were selected.'),
                Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

        elements = []
        for fg in filter_groups:
            subscriptions = AlertSubscription.objects.filter(filter_group=fg)
            time_periods = TimePeriod.objects.filter(alertsubscription__in=subscriptions)
            profiles = AlertProfile.objects.filter(timeperiod__in=time_periods)
            warnings = []

            try:
                owner = fg.owner
            except Account.DoesNotExist:
                warnings.append({
                    'message': u'''This is a public filter group. Deleting it
                        will make it unavailable for all other users of this
                        system.''',
                })

            for p in profiles:
                warnings.append({
                    'message': u'Used in profile %(name)s.' % {'name': p.name},
                    'link': reverse('alertprofiles-profile-detail', args=(p.id,)),
                })

            elements.append({
                'id': fg.id,
                'description': fg.name,
                'warnings': warnings,
            })


        info_dict = {
                'form_action': reverse('alertprofiles-filter_groups-remove'),
                'active': {'filter_groups': True},
                'subsection': {'list': True},
                'elements': elements,
                'perform_on': None,
                'navpath': BASE_PATH+[
                    ('Filter groups', reverse('alertprofiles-filters')),
                    ('Remove filter groups', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def filter_group_addfilter(request):
    if not request.method == 'POST' or not request.POST.get('id') or not request.POST.get('filter'):
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

    account = get_account(request)
    filter_group = None
    try:
        filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
    except FilterGroup.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested filter group does not exist.'))

    filter = None
    try:
        filter = Filter.objects.get(pk=request.POST.get('filter'))
    except Filter.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested filter does not exist.'))

    operator = request.POST.get('operator')

    if not account_owns_filters(account, filter_group):
        return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))

    if not operator or len(operator) != 2:
        return HttpResponseRedirect(
                reverse('alertprofiles-filter_groups-detail', attrs=(filter.id,))
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
            'filter': filter,
            'filter_group': filter_group,
        }
    new_filter = FilterGroupContent(**options)
    new_filter.save()

    new_message(
        request,
        _('Added filter %(name)s') % {'name': filter.name},
        Messages.SUCCESS
    )
    return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
        )

def filter_group_remove_or_move_filter(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

    post = request.POST.copy()
    for name in post:
        if name.find("=") != -1:
            attribute, value = name.split("=")
            del post[name]
            post[attribute] = value
    request.POST = post

    if request.POST.get('moveup') or request.POST.get('movedown'):
        return filter_group_movefilter(request)
    else:
        return filter_group_removefilter(request)

def filter_group_removefilter(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

    # We are deleting filters. Show confirmation page or remove?
    if request.POST.get('confirm'):
        filter_group = FilterGroup.objects.get(pk=request.POST.get('perform_on'))
        fg_content = FilterGroupContent.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), filter_group):
            return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))

        filters = Filter.objects.filter(pk__in=[f.filter.id for f in fg_content])
        names = ', '.join([f.name for f in filters])
        fg_content.delete()

        # Rearrange filters
        last_priority = order_filter_group_content(filter_group)

        new_message(
            request,
            _('Removed filters, %(names)s, from filter group %(fg)s.') % {
                'names': names,
                'fg': filter_group.name
            },
            Messages.SUCCESS
        )
        return HttpResponseRedirect(
                reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
            )
    else:
        filter_group = None
        try:
            filter_group = FilterGroup.objects.get(pk=request.POST.get('id'))
        except FilterGroup.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested filter group does not exist'))

        filter_group_content = FilterGroupContent.objects.filter(
                pk__in=request.POST.getlist('filter'),
                filter_group=filter_group.id
            )

        if not account_owns_filters(get_account(request), filter_group):
            return alertprofiles_response_forbidden(request, _('You do not own this filter group.'))

        try:
            owner = filter_group.owner
        except Account.DoesNotExist:
            new_message(
                request,
                _(u'''You are now editing a public filter group. This will
                affect all users who uses this filter group.'''),
                Messages.WARNING
            )

        if len(filter_group_content) == 0:
            new_message(
                request,
                _('No filters were selected.'),
                Messages.NOTICE)
            return HttpResponseRedirect(
                reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,)))

        elements = []
        for f in filter_group_content:
            warnings = []

            description = _('''Remove filter %(filter)s from %(fg)s.''') % {
                'filter': f.filter.name,
                'fg': f.filter_group.name,
            }

            elements.append({
                'id': f.id,
                'description': description,
            })

        info_dict = {
                'form_action': reverse('alertprofiles-filter_groups-removefilter'),
                'active': {'filter_groups': True},
                'subsection': {'detail': filter_group.id},
                'elements': elements,
                'perform_on': filter_group.id,
                'navpath': BASE_PATH+[
                    ('Filter groups', reverse('alertprofiles-filter_groups')),
                    (
                        filter_group.name,
                        reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
                    ),
                    ('Remove filters', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def filter_group_movefilter(request):
    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filter_groups'))

    account = get_account(request)

    filter_group_id = request.POST.get('id')
    filter_group = None
    try:
        filter_group = FilterGroup.objects.get(pk=filter_group_id)
    except FilterGroup.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested filter group does not exist.'))
    else:
        if filter_group.owner != account:
            return alertprofiles_response_forbidden(
                request,
                'You do not have access to the requested filter group.'
            )

    movement = 0
    filter = None

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

    filter = None
    try:
        filter = FilterGroupContent.objects.get(pk=filter_id)
    except FilterGroupContent.DoesNotExist:
        return alertprofiles_response_not_found(
            request,
            _('Requested filter group content does not exist.')
        )

    # Make sure content is ordered correct
    last_priority = order_filter_group_content(filter_group)

    # Check if the filter we're going to swap places with exists
    try:
        other_filter = FilterGroupContent.objects.filter(
                    filter_group=filter_group.id,
                    priority=filter.priority + movement
                )[0:1].get()
    except FilterGroupContent.DoesNotExist:
        return HttpResponseRedirect(
                reverse('alertprofiles-filter_groups-detail', args=(filter_group.id,))
            )

    new_priority = other_filter.priority
    other_filter.priority = filter.priority
    filter.priority = new_priority

    other_filter.save()
    filter.save()

    new_message(
        request,
        _('Moved filter %(filter)s %(direction)s') % {
            'direction': direction,
            'filter': filter.filter.name,
        },
        Messages.SUCCESS
    )

    return HttpResponseRedirect(
            reverse('alertprofiles-filter_groups-detail', args=(filter_group_id,))
        )

def matchfield_list(request):
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')
    page = request.GET.get('page', 1)

    # Define valid options for ordering
    valid_ordering = ['name', '-name', 'description', '-description']
    order_by = request.GET.get('order_by', 'name').lower()
    if order_by not in valid_ordering:
        order_by = 'name'

    new_message(
        request,
        _('''Editing matchfields is black magic. Don't do it unless you know
        exacly what you are doing.'''),
        Messages.NOTICE,
    )

    # Get all matchfields aka. filter variables
    matchfields = MatchField.objects.all().order_by(order_by)
    info_dict = {
            'active': {'matchfields': True},
            'subsection': {'list': True},
            'form_action': reverse('alertprofiles-matchfields-remove'),
            'order_by': order_by,
            'navpath': BASE_PATH+[
                ('Matchfields', None),
            ],
            'title': 'NAV - Alert profiles',
        }
    return object_list(
            request,
            queryset=matchfields,
            paginate_by=PAGINATE_BY,
            page=page,
            template_name='alertprofiles/matchfield_list.html',
            extra_context=info_dict,
        )

def matchfield_show_form(request, matchfield_id=None, matchfield_form=None):
    active = {'matchfields': True}
    page_name = 'New matchfield'
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')

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
        matchfield_operators_id = [m_operator.type for m_operator in matchfield.operator_set.all()]

        page_name = matchfield.name

        expressions = Expression.objects.filter(match_field=matchfield)
        filters = Filter.objects.filter(expression__in=expressions)

        if len(filters) > 0:
            names = ', '.join([f.name for f in filters])
            new_message(
                request,
                _('''Match field is in use in filters: %(filters)s. Editing
                this match field may alter how those filters work.''') % {
                    'filters': names,
                },
                Messages.WARNING
            )

    operators = []
    for o in Operator.OPERATOR_TYPES:
        selected = o[0] in matchfield_operators_id
        operators.append({'id': o[0], 'name': o[1], 'selected': selected})

    if matchfield_id:
        subsection = {'detail': matchfield_id}
    else:
        subsection = {'new': True}

    new_message(
        request,
        _('''Editing matchfields is black magic. Don't do it unless you know
        exacly what you are doing.'''),
        Messages.NOTICE,
    )

    info_dict = {
            'active': active,
            'subsection': subsection,
            'detail_id': matchfield_id,
            'form': matchfield_form,
            'operators': operators,
            'owner': True,
            'navpath': BASE_PATH+[
                ('Matchfields', reverse('alertprofiles-matchfields')),
                (page_name, None),
            ],
            'title': 'NAV - Alert profiles',
        }
    return render_to_response(
            'alertprofiles/matchfield_form.html',
            info_dict,
            RequestContext(request),
        )

def matchfield_detail(request, matchfield_id=None):
    return matchfield_show_form(request, matchfield_id)

def matchfield_save(request):
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')

    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-matchfields'))

    matchfield = None

    try:
        if not request.POST.get('id'):
            raise MatchField.DoesNotExist
        m = MatchField.objects.get(pk=request.POST.get('id'))
    except MatchField.DoesNotExist:
        form = MatchFieldForm(request.POST)
    else:
        form = MatchFieldForm(request.POST, instance=m)

    # If there are some invalid values, return to form and show the errors
    if not form.is_valid():
        detail_id = request.POST.get('id') or None
        return matchfield_show_form(request, detail_id, form)

    matchfield = form.save()

    operators = []
    for o in request.POST.getlist('operator'):
        operators.append(Operator(type=int(o), match_field=matchfield))
    matchfield.operator_set.all().delete()
    matchfield.operator_set.add(*operators)

    new_message(
        request,
        _('Saved matchfield %(name)s') % {'name': matchfield.name},
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-matchfields-detail', args=(matchfield.id,)))

def matchfield_remove(request):
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')

    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        matchfields = MatchField.objects.filter(pk__in=request.POST.getlist('element'))
        names = ', '.join([m.name for m in matchfields])
        matchfields.delete()
        new_message(
            request,
            _('Removed matchfields: %(names)s') % {'names': names},
            Messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('alertprofiles-matchfields'))
    else:
        matchfields = MatchField.objects.select_related(
            'expression'
        ).filter(pk__in=request.POST.getlist('matchfield'))

        if len(matchfields) == 0:
            new_message(
                request,
                _('No matchfields were selected'),
                Messages.NOTICE)
            return HttpResponseRedirect(reverse('alertprofiles-matchfields'))

        elements = []
        for m in matchfields:
            expressions = m.expression_set.all()
            warnings = []
            for e in expressions:
                warnings.append({
                    'message': 'Used in filter %(filter)s.' % {'filter': e.filter.name},
                    'link': reverse('alertprofiles-filters-detail', args=(e.filter.id,)),
                })
            elements.append({
                'id': m.id,
                'description': m.name,
                'warnings': warnings,
            })

        new_message(
            request,
            _('''It is strongly recomended that one do not remove one of the
            default match fields that comes preinstalled with NAV.'''),
            Messages.NOTICE
        )

        info_dict = {
                'form_action': reverse('alertprofiles-matchfields-remove'),
                'active': {'matchfields': True},
                'subsection': {'list': True},
                'elements': elements,
                'perform_on': None,
                'navpath': BASE_PATH+[
                    ('Matchfields', reverse('alertprofiles-matchfields')),
                    ('Remove matchfields', None),
                ],
                'title': 'NAV - Alert profiles',
            }
        return render_to_response(
                'alertprofiles/confirmation_list.html',
                info_dict,
                RequestContext(request),
            )

def permission_list(request, group_id=None):
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')

    groups = AccountGroup.objects.all().order_by('name')

    selected_group = None
    filter_groups = None
    permissions = None
    if group_id:
        filter_groups = FilterGroup.objects.filter(owner__isnull=True).order_by('name')
        try:
            selected_group = groups.get(pk=group_id)
        except AccountGroup.DoesNotExist:
            return alertprofiles_response_not_found(request, _('Requested account group does not exist.'))

        permissions = AccountGroup.objects.get(pk=group_id).filtergroup_set.all()

    active = {'permissions': True}
    info_dict = {
            'groups': groups,
            'selected_group': selected_group,
            'filter_groups': filter_groups,
            'permissions': permissions,
            'active': active,
            'navpath': BASE_PATH+[
                ('Permissions', None),
            ],
            'title': 'NAV - Alert profiles',
        }

    return render_to_response(
            'alertprofiles/permissions.html',
            info_dict,
            RequestContext(request),
        )

def permissions_save(request):
    account = get_account(request)
    if not is_admin(account):
        return alertprofiles_response_forbidden(request, 'Only admins can view this page.')

    if not request.method == 'POST':
        new_message(request, _('Required post-data were not supplied.'), Messages.ERROR)
        return HttpResponseRedirect(reverse('alertprofiles-permissions'))

    group = None
    try:
        group = AccountGroup.objects.get(pk=request.POST.get('group'))
    except AccountGroup.DoesNotExist:
        return alertprofiles_response_not_found(request, _('Requested account group does not exist.'))

    filter_groups = FilterGroup.objects.filter(pk__in=request.POST.getlist('filter_group'))

    group.filtergroup_set = filter_groups

    new_message(
        request,
        _('Saved permissions for group %(name)s') % {'name': group.name},
        Messages.SUCCESS
    )
    return HttpResponseRedirect(reverse('alertprofiles-permissions-detail', args=(group.id,)))
