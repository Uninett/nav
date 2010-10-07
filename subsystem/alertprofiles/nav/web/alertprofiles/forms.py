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

from django import forms
from django.db.models import Q

from nav.models.profiles import MatchField, Filter, Expression, Operator, \
    FilterGroup, AlertProfile, TimePeriod, AlertSubscription, AlertAddress, \
    AccountProperty

_ = lambda a: a

class AccountPropertyForm(forms.ModelForm):

    class Meta:
        model = AccountProperty
        exclude = ('account',)

    def __init__(self, *args, **kwargs):
        property = kwargs.pop('property', None)
        values = kwargs.pop('values', None)

        super(AccountPropertyForm, self).__init__(*args, **kwargs)

        self.fields['property'] = forms.CharField(widget=forms.widgets.HiddenInput, initial=property)
        self.fields['value'] = forms.ChoiceField(choices=values)

class AlertProfileForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    name = forms.CharField(required=True)
    daily_dispatch_time = forms.TimeField(
        initial='08:00',
        input_formats=['%H:%M:%S', '%H:%M', '%H'],
        help_text=_(u'Valid time formats are HH:MM:SS, HH:MM and HH')
    )
    weekly_dispatch_time = forms.TimeField(
        initial='08:00',
        input_formats=['%H:%M:%S', '%H:%M', '%H'],
        help_text=_(u'Valid time formats are HH:MM:SS, HH:MM and HH')
    )

    class Meta:
        model = AlertProfile
        exclude = ('account',)

class AlertAddressForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    address = forms.CharField(required=True)

    class Meta:
        model = AlertAddress
        exclude = ('account',)

class TimePeriodForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    profile = forms.ModelChoiceField(
        AlertProfile.objects.all(),
        widget=forms.widgets.HiddenInput
    )
    start = forms.TimeField(
        initial='08:00',
        input_formats=['%H:%M:%S', '%H:%M', '%H'],
        help_text=_(u'Valid time formats are HH:MM:SS, HH:MM and HH')
    )

    class Meta:
        model = TimePeriod

    def clean(self):
        id = self.cleaned_data.get('id', None)
        profile = self.cleaned_data.get('profile', None)
        start_time = self.cleaned_data.get('start', None)
        valid_during = self.cleaned_data.get('valid_during', None)

        valid_during_choices = None
        if valid_during == TimePeriod.ALL_WEEK:
            valid_during_choices = (TimePeriod.ALL_WEEK, TimePeriod.WEEKDAYS, TimePeriod.WEEKENDS)
        elif valid_during == TimePeriod.WEEKDAYS:
            valid_during_choices = (TimePeriod.ALL_WEEK, TimePeriod.WEEKDAYS)
        else:
            valid_during_choices = (TimePeriod.ALL_WEEK, TimePeriod.WEEKENDS)

        time_periods = TimePeriod.objects.filter(
            ~Q(pk=id),
            profile=profile,
            start=start_time,
            valid_during__in=valid_during_choices
        )
        if len(time_periods) > 0:
            error_msg = []
            for t in time_periods:
                error_msg.append(
                    u'Collides with existing time period: %s for %s' % (t.start, t.get_valid_during_display())
                )
            raise forms.util.ValidationError(error_msg)
        else:
            return self.cleaned_data

class AlertSubscriptionForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    class Meta:
        model = AlertSubscription

    def __init__(self, *args, **kwargs):
        time_period = kwargs.pop('time_period', None)
        super(AlertSubscriptionForm, self).__init__(*args, **kwargs)

        if isinstance(time_period, TimePeriod):
            self.fields['time_period'] = forms.IntegerField(
                    widget=forms.widgets.HiddenInput,
                    initial=time_period.id
                )
            # Get account
            account = time_period.profile.account

            addresses = AlertAddress.objects.filter(account=account).order_by('type', 'address')
            filter_groups = FilterGroup.objects.filter(
                Q(owner__isnull=True) | Q(owner__exact=account)).order_by('owner', 'name')

            address_choices = [(a.id, a.address) for a in addresses]
            filter_group_choices = [(f.id, f.name) for f in filter_groups]

            self.fields['alert_address'] = forms.ChoiceField(
                    choices=address_choices,
                    error_messages={
                        'required': 'Alert address is a required field.',
                        'invalid_choice': 'The selected alert address is a invalid choice.',
                    }
                )
            self.fields['filter_group'] = forms.ChoiceField(
                    choices=filter_group_choices,
                    error_messages={
                        'required': 'Filter group is a required field.',
                        'invalid_choice': 'The selected filter group is a invalid choice.',
                    }
                )

    def clean(self):
        alert_address = self.cleaned_data.get('alert_address', None)
        time_period = self.cleaned_data.get('time_period', None)
        filter_group = self.cleaned_data.get('filter_group', None)
        subscription_type = self.cleaned_data.get('type', None)
        ignore = self.cleaned_data.get('ignore_resolved_alerts', False)
        id = self.cleaned_data['id']

        error_msg = []

        existing_subscriptions = AlertSubscription.objects.filter(
                Q(alert_address=alert_address),
                Q(time_period=time_period),
                Q(filter_group=filter_group),
                ~Q(pk=id)
            )

        for e in existing_subscriptions:
            error_msg.append(
                u'''Filter group and alert address must be unique for each
                subscription. This one collides with group %s watched by %s
                ''' % (e.filter_group.name, e.alert_address.address)
            )

        if subscription_type == AlertSubscription.NOW and ignore:
            error_msg.append(u'Resolved alerts can not be ignored ' +
                'for now subscriptions')

        if error_msg:
            raise forms.util.ValidationError(error_msg)

        return self.cleaned_data

class FilterGroupForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    owner = forms.BooleanField(required=False, label='Private',
        help_text=_(u'Uncheck to allow all users to use this filter group.'))
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)

    class Meta:
        model = FilterGroup
        exclude = ('group_permissions',)

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        is_owner = kwargs.pop('is_owner', None)
        super(FilterGroupForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

        if not is_owner:
            for f in self.fields.itervalues():
                f.widget.attrs['disabled'] = 'disabled'

class FilterForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    owner = forms.BooleanField(required=False, label=u'Private',
        help_text=_(u'Uncheck to allow all users to use this filter.'))
    name = forms.CharField(required=True)

    class Meta:
        model = Filter

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        is_owner = kwargs.pop('is_owner', None)
        super(FilterForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

        if not is_owner:
            for f in self.fields.itervalues():
                f.widget.attrs['disabled'] = 'disabled'

class MatchFieldForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    list_limit = forms.ChoiceField(
            choices=((100,100),(200,200),(300,300),(500,500),(1000,'1 000'),(10000,'10 000')),
            initial=300,
            help_text=_(u'Only this many options will be available in the list. Only does something when "Show list" is checked.'),
        )

    class Meta:
        model = MatchField

    def clean_value_name(self):
        clean_value_name = self.cleaned_data['value_name']
        try:
            clean_value_id = self.cleaned_data['value_id']
        except:
            # value_id is not set. We pass and return clean_value_name.
            # value_id is required and will raise it's own ValidationErrors
            pass
        else:
            if clean_value_name:
                model, attname = MatchField.MODEL_MAP[clean_value_id]
                name_model, name_attname = MatchField.MODEL_MAP[clean_value_name.split('|')[0]]
                if not model == name_model:
                    raise forms.util.ValidationError(u'This field must be the same model as match field, or not set at all.')
        return clean_value_name


    def clean_value_sort(self):
        clean_value_sort = self.cleaned_data['value_sort']
        try:
            clean_value_id = self.cleaned_data['value_id']
        except:
            # value_id is not set. We pass and return clean_value_name.
            # value_id is required and will raise it's own ValidationErrors
            pass
        else:
            if clean_value_sort:
                model, attname = MatchField.MODEL_MAP[clean_value_id]
                sort_model, sort_attname = MatchField.MODEL_MAP[clean_value_sort]
                if not model == sort_model:
                    raise forms.util.ValidationError(u'This field must be the same model as match field, or not set at all.')
        return clean_value_sort

class ExpressionForm(forms.ModelForm):
    filter = forms.IntegerField(widget=forms.widgets.HiddenInput)
    match_field = forms.IntegerField(widget=forms.widgets.HiddenInput)

    class Meta:
        model = Expression

    def __init__(self, *args, **kwargs):
        match_field = kwargs.pop('match_field', None)
        super(ExpressionForm, self).__init__(*args, **kwargs)

        if isinstance(match_field, MatchField):
            # Get all operators and make a choice field
            operators = match_field.operator_set.all()
            self.fields['operator'] = forms.models.ChoiceField([(o.type, o) for o in operators])

            if match_field.show_list:
                # Values are selected from a multiple choice list.
                # Populate that list with possible choices.

                # MatcField stores which table and column alert engine should
                # watch, as well as a table and column for "friendly" names in
                # the GUI and how we should sort the fields in the GUI (if we
                # are displaying a list)
                #
                # Here we map those table and column names to django models and
                # attribute names.
                #
                # FIXME If value_id is not set we should display an error
                # message telling that this match field won't work and should
                # be fixed ASAP
                model, attname = MatchField.MODEL_MAP[match_field.value_id]

                if match_field.value_name:
                    name_model, name_attname = MatchField.MODEL_MAP[match_field.value_name.split('|')[0]]
                else:
                    name_model = None

                if match_field.value_sort:
                    order_model, order_attname = MatchField.MODEL_MAP[match_field.value_sort]
                else:
                    order_model = None
                
                self.number_of_choices = model.objects.count()

                # First we say we want all the objects, unordered
                model_objects = model.objects.all()

                if model == order_model:
                    # If order is specified, and it's from the same model as
                    # the selected objects, we order by the specified attribute
                    # ...
                    model_objects = model_objects.order_by(order_attname)
                else:
                    # ... if not, we order by the primary key
                    model_objects = model_objects.order_by('pk')

                # Last we limit the objects
                model_objects = model_objects[:match_field.list_limit]

                choices = []
                for a in model_objects:
                    # ID is what is acctually used in the expression that will
                    # be evaluted by alert engine
                    id = getattr(a, attname)

                    if model == name_model:
                        # name is just a "friendly" name, only used in the GUI
                        # to make it easier to add expressions. We only set it
                        # if the models for both id and name are the same.
                        name = getattr(a, name_attname)

                        if name != id:
                            # If id and name are not equal we make a nice
                            # string with both. If they are the same we only
                            # use id, as both would be redundant.
                            choices.append((id, '%s: %s' % (id, name)))
                            continue
                    choices.append((id,id))

                # At last we acctually add the multiple choice field.
                self.fields['value'] = forms.MultipleChoiceField(choices=choices)
