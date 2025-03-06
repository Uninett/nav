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
"""Alert Profiles forms"""

from typing import Any

from django import forms
from django.db.models import Q

from nav.alertengine.dispatchers.email_dispatcher import Email
from nav.alertengine.dispatchers.slack_dispatcher import Slack
from nav.alertengine.dispatchers.sms_dispatcher import Sms
from nav.models.profiles import Expression, Filter, FilterGroup, MatchField, Operator
from nav.models.profiles import AlertProfile, TimePeriod, AlertSubscription
from nav.models.profiles import AlertAddress, AlertSender
from nav.util import is_valid_cidr, is_valid_ip
from nav.web.crispyforms import (
    set_flat_form_attributes,
    FormRow,
    FormColumn,
    HelpFormField,
    SubmitField,
)

_ = lambda a: a  # gettext variable (for future implementations)


class LanguageForm(forms.Form):
    """The language form is used to choose alert language"""

    language = forms.ChoiceField(choices=[('en', 'English'), ('no', 'Norwegian')])


class AlertProfileForm(forms.ModelForm):
    """Form for editing and creating alert profiles.

    The alert profile form enables the user to configure what alerts are sent at
    which times
    """

    id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(AlertProfileForm, self).__init__(*args, **kwargs)

        self.fields['daily_dispatch_time'].widget = forms.TimeInput(format='%H:%M')
        self.fields['weekly_dispatch_time'].widget = forms.TimeInput(format='%H:%M')
        self.fields['weekly_dispatch_day'].widget.attrs.update({'class': 'select2'})

        self.attrs = set_flat_form_attributes(
            form_fields=[
                self["id"],
                self["name"],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self["daily_dispatch_time"]],
                            css_classes="medium-4",
                        ),
                        FormColumn(
                            fields=[self["weekly_dispatch_time"]],
                            css_classes="medium-4",
                        ),
                        FormColumn(
                            fields=[self["weekly_dispatch_day"]],
                            css_classes="medium-4",
                        ),
                    ]
                ),
            ]
        )

    class Meta(object):
        model = AlertProfile
        exclude = ('account',)


class AlertAddressForm(forms.ModelForm):
    """Form for editing and creating alert addresses

    An alert address is where the alert is sent, and can be either
    email or slack in addition to sms.

    """

    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    address = forms.CharField(required=True)
    type = forms.ModelChoiceField(queryset=AlertSender.objects.filter(supported=True))

    def __init__(self, *args, **kwargs):
        super(AlertAddressForm, self).__init__(*args, **kwargs)
        self.fields['type'].widget.attrs.update({"class": "select2"})
        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['id'],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['type']],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[self['address']],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[],
                            css_classes='medium-4',
                        ),
                    ]
                ),
            ]
        )

    class Meta(object):
        model = AlertAddress
        exclude = ('account',)

    def clean(self):
        cleaned_data = self.cleaned_data
        type_ = cleaned_data.get('type')
        address = cleaned_data.get('address')
        if type_ and address:
            error = None
            if not type_.supported:
                error = "{} is no longer supported by NAV".format(type_.name)
            elif type_.handler == 'sms':
                if not Sms.is_valid_address(address):
                    error = 'Not a valid phone number.'
            elif type_.handler == 'email':
                if not Email.is_valid_address(address):
                    error = 'Not a valid email address.'
            elif type_.handler == 'slack':
                if not Slack.is_valid_address(address):
                    error = 'Not a valid absolute url.'

            if error:
                self._errors['address'] = self.error_class([error])
                del cleaned_data['address']

        return cleaned_data


class TimePeriodForm(forms.ModelForm):
    """Form for editing time periods"""

    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    profile = forms.ModelChoiceField(
        AlertProfile.objects.all(), widget=forms.HiddenInput
    )
    start = forms.TimeField(
        initial='08:00',
        input_formats=['%H:%M:%S', '%H:%M', '%H'],
        help_text=_('Valid time formats are HH:MM and HH'),
    )

    def __init__(self, *args, **kwargs):
        super(TimePeriodForm, self).__init__(*args, **kwargs)
        submit_text = 'Add'

        if self.instance and self.instance.id:
            self.fields['valid_during'].widget.attrs['disabled'] = 'disabled'
            submit_text = 'Save'

        self.fields['valid_during'].widget.attrs.update({"class": "select2"})
        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['id'],
                self['profile'],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['start']],
                            css_classes='medium-6',
                        ),
                        FormColumn(
                            fields=[self['valid_during']],
                            css_classes='medium-6',
                        ),
                    ]
                ),
                SubmitField(value=submit_text, css_classes='small'),
            ]
        )

    class Meta(object):
        model = TimePeriod
        fields = '__all__'

    def clean(self):
        ident = self.cleaned_data.get('id', None)
        profile = self.cleaned_data.get('profile', None)
        start_time = self.cleaned_data.get('start', None)
        valid_during = self.cleaned_data.get('valid_during', None)

        if valid_during == TimePeriod.ALL_WEEK:
            valid_during_choices = (
                TimePeriod.ALL_WEEK,
                TimePeriod.WEEKDAYS,
                TimePeriod.WEEKENDS,
            )
        elif valid_during == TimePeriod.WEEKDAYS:
            valid_during_choices = (TimePeriod.ALL_WEEK, TimePeriod.WEEKDAYS)
        else:
            valid_during_choices = (TimePeriod.ALL_WEEK, TimePeriod.WEEKENDS)

        time_periods = TimePeriod.objects.filter(
            ~Q(pk=ident),
            profile=profile,
            start=start_time,
            valid_during__in=valid_during_choices,
        )
        if time_periods:
            errors = [
                forms.ValidationError(
                    _(
                        """Collides with existing time period: %(start)s for
                    %(valid)s"""
                    ),
                    params={
                        'start': period.start,
                        'valid': period.get_valid_during_display(),
                    },
                    code='timeperiod-collide',
                )
                for period in time_periods
            ]
            raise forms.ValidationError(errors)
        else:
            return self.cleaned_data


class AlertSubscriptionForm(forms.ModelForm):
    """Form for editing an alert subscription"""

    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    alert_address = forms.ModelChoiceField(
        queryset=AlertAddress.objects.filter(type__supported=True)
    )

    class Meta(object):
        model = AlertSubscription
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        time_period = kwargs.pop('time_period', None)
        super(AlertSubscriptionForm, self).__init__(*args, **kwargs)

        hidden_fields = ['id']
        if isinstance(time_period, TimePeriod):
            self.fields['time_period'] = forms.ModelChoiceField(
                queryset=TimePeriod.objects.filter(id=time_period.id),
                widget=forms.HiddenInput,
                initial=time_period.id,
            )
            hidden_fields.append('time_period')
            # Get account
            account = time_period.profile.account

            addresses = AlertAddress.objects.filter(
                account=account, type__supported=True
            ).order_by('type', 'address')
            filter_groups = FilterGroup.objects.filter(
                Q(owner__isnull=True) | Q(owner__exact=account)
            ).order_by('owner', 'name')

            self.fields['alert_address'] = forms.ModelChoiceField(
                queryset=addresses,
                empty_label=None,
                error_messages={
                    'required': 'Alert address is a required field.',
                    'invalid_choice': (
                        'The selected alert address is an invalid choice.'
                    ),
                },
                label='Send alerts to',
                widget=forms.Select(attrs={'class': 'select2'}),
            )
            self.fields['filter_group'] = forms.ModelChoiceField(
                queryset=filter_groups,
                empty_label=None,
                error_messages={
                    'required': 'Filter group is a required field.',
                    'invalid_choice': (
                        'The selected filter group is an invalid choice.'
                    ),
                },
                label='Watch',
                widget=forms.Select(attrs={'class': 'select2'}),
            )
            self.fields['ignore_resolved_alerts'] = forms.BooleanField(
                required=False,
                widget=forms.CheckboxInput(attrs={'class': 'input-align'}),
            )
            self.fields['type'].label = 'When'
            self.fields['type'].widget.attrs.update({"class": "select2"})
            self.fields['type'].help_text = """
            <dl>
                <dt>Immediately</dt>
                <dd>Send the alert as soon as alertengine has processed it.</dd>

                <dt>Daily at predefined time</dt>
                <dd>Send all matched alerts at the specified daily
                    dispatch time.</dd>
                <dt>Weekly at predefined time</dt>
                <dd>Send all matched alerts at the specified weekly
                    dispatch time.</dd>
                <dt>At end of timeperiod</dt>
                <dd>Send all matched alerts when the current timeperiod is
                    over and a new one starts.</dd>
            </dl>
            """
        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['filter_group']],
                            css_classes='medium-3',
                        ),
                        FormColumn(
                            fields=[self['alert_address']],
                            css_classes='medium-3',
                        ),
                        FormColumn(
                            fields=[HelpFormField(self['type'])],
                            css_classes='medium-3',
                        ),
                        FormColumn(
                            fields=[self['ignore_resolved_alerts']],
                            css_classes='medium-3',
                        ),
                    ]
                ),
                *[self[field] for field in hidden_fields],
            ]
        )

    def clean(self):
        alert_address = self.cleaned_data.get('alert_address', None)
        time_period = self.cleaned_data.get('time_period', None)
        filter_group = self.cleaned_data.get('filter_group', None)
        subscription_type = self.cleaned_data.get('type', None)
        ignore = self.cleaned_data.get('ignore_resolved_alerts', False)
        ident = self.cleaned_data['id']

        errors = []

        existing_subscriptions = AlertSubscription.objects.filter(
            Q(alert_address=alert_address),
            Q(time_period=time_period),
            Q(filter_group=filter_group),
            ~Q(pk=ident),
        )

        for sub in existing_subscriptions:
            errors.append(
                forms.ValidationError(
                    _(
                        """Filter group and alert address must be unique for each
                    subscription. This one collides with group %(group)s
                    watched by %(address)s"""
                    ),
                    code='unique-group-and-address',
                    params={
                        'group': sub.filter_group.name,
                        'address': sub.alert_address.address,
                    },
                )
            )

        if subscription_type == AlertSubscription.NOW and ignore:
            errors.append(
                forms.ValidationError(
                    _(
                        """Resolved alerts cannot be ignored for immediate
                    subscriptions"""
                    ),
                    code='resolved-alert-cannot-be-ignored',
                )
            )

        if errors:
            raise forms.ValidationError(errors)

        return self.cleaned_data


class FilterGroupForm(forms.Form):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    owner = forms.BooleanField(
        required=False,
        label='Private',
        help_text=_('Uncheck to allow all users to use this filter group.'),
    )
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)

    class Meta(object):
        model = FilterGroup
        exclude = ('group_permissions',)

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        is_owner = kwargs.pop('is_owner', None)
        super(FilterGroupForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

        if not is_owner:
            for field in self.fields.values():
                field.widget.attrs['disabled'] = 'disabled'

        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['id'],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['name']],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[self['description']],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[self['owner']],
                            css_classes='medium-4',
                        ),
                    ]
                ),
            ]
        )


class FilterForm(forms.Form):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    owner = forms.BooleanField(
        required=False,
        label='Private',
        help_text=_('Uncheck to allow all users to use this filter.'),
    )
    name = forms.CharField(required=True)

    class Meta(object):
        model = Filter

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        is_owner = kwargs.pop('is_owner', None)
        super(FilterForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

        if not is_owner:
            for field in self.fields.values():
                field.widget.attrs['disabled'] = 'disabled'

        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['id'],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['name']],
                            css_classes='medium-6',
                        ),
                        FormColumn(
                            fields=[self['owner']],
                            css_classes='medium-6',
                        ),
                    ]
                ),
            ]
        )


class MatchFieldForm(forms.ModelForm):
    """Allows creation and editing of match fields

    A filter contains of match fields that should be some value. Match fields
    are normally not created or edited by other than users that are very
    confident in the NAV database layout.
    """

    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    list_limit = forms.ChoiceField(
        choices=(
            (100, 100),
            (200, 200),
            (300, 300),
            (500, 500),
            (1000, '1 000'),
            (10000, '10 000'),
        ),
        initial=300,
        help_text=_(
            'Only this many options will be available in the '
            'list. Only does something when "Show list" is '
            'checked.'
        ),
    )

    def __init__(self, *args, **kwargs):
        super(MatchFieldForm, self).__init__(*args, **kwargs)
        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['id'],
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[self['name']],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[self['description']],
                            css_classes='medium-8',
                        ),
                    ]
                ),
                HelpFormField(self['value_help']),
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[HelpFormField(self['value_id'])],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[HelpFormField(self['value_name'])],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[HelpFormField(self['value_sort'])],
                            css_classes='medium-4',
                        ),
                    ]
                ),
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[HelpFormField(self['list_limit'])],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[HelpFormField(self['data_type'])],
                            css_classes='medium-4',
                        ),
                        FormColumn(
                            fields=[HelpFormField(self['show_list'])],
                            css_classes='medium-4',
                        ),
                    ]
                ),
            ]
        )

    class Meta(object):
        model = MatchField
        fields = '__all__'

    @staticmethod
    def _get_field_not_same_model_error():
        return forms.ValidationError(
            _(
                """This field must be the same model as match field,
            or not set at all."""
            ),
            code='field_not_same_model',
        )

    def clean_value_name(self):
        """Cleans the field 'value_name'"""
        clean_value_name = self.cleaned_data['value_name']
        try:
            clean_value_id = self.cleaned_data['value_id']
        except KeyError:
            # value_id is not set. We pass and return clean_value_name.
            # value_id is required and will raise it's own ValidationErrors
            pass
        else:
            if clean_value_name:
                model, _attname = MatchField.MODEL_MAP[clean_value_id]
                name_model, _name_attname = MatchField.MODEL_MAP[
                    clean_value_name.split('|')[0]
                ]
                if not model == name_model:
                    raise self._get_field_not_same_model_error()
        return clean_value_name

    def clean_value_sort(self):
        """Cleans the field 'value_sort'"""
        clean_value_sort = self.cleaned_data['value_sort']
        try:
            clean_value_id = self.cleaned_data['value_id']
        except KeyError:
            # value_id is not set. We pass and return clean_value_name.
            # value_id is required and will raise it's own ValidationErrors
            pass
        else:
            if clean_value_sort:
                model, _attname = MatchField.MODEL_MAP[clean_value_id]
                sort_model, _sort_attname = MatchField.MODEL_MAP[clean_value_sort]
                if not model == sort_model:
                    raise self._get_field_not_same_model_error()
        return clean_value_sort


class ExpressionForm(forms.ModelForm):
    """Enables editing and creating expressions

    An expression ties together a match field with and operator and a value to
    create expressions that can be used in a filter.
    """

    filter = forms.ModelChoiceField(
        queryset=Filter.objects.all(), widget=forms.widgets.HiddenInput
    )
    match_field = forms.ModelChoiceField(
        queryset=MatchField.objects.all(), widget=forms.widgets.HiddenInput
    )

    class Meta(object):
        model = Expression
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        match_field = kwargs.pop('match_field', None)  # add_expression
        if not match_field:
            match_field = args[0].get('match_field', None)  # save_expression
        self.match_field = match_field
        super(ExpressionForm, self).__init__(*args, **kwargs)

        if not match_field:
            return

        if not isinstance(match_field, MatchField):
            match_field = MatchField.objects.get(pk=match_field)

        if True:  # maintain indent for the sake off smaller diff!
            # Get all operators and make a choice field
            operators = match_field.operators.all()
            self.fields['operator'] = forms.models.ChoiceField(
                choices=[(o.type, o) for o in operators]
            )

            if match_field.show_list:
                # Values are selected from a multiple choice list.
                # Populate that list with possible choices.

                # MatchField stores which table and column alert engine should
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
                    name_model, name_attname = MatchField.MODEL_MAP[
                        match_field.value_name.split('|')[0]
                    ]
                else:
                    name_model = None

                if match_field.value_sort:
                    order_model, order_attname = MatchField.MODEL_MAP[
                        match_field.value_sort
                    ]
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
                model_objects = model_objects[: match_field.list_limit]

                choices = []
                for obj in model_objects:
                    # ID is what is actually used in the expression that will
                    # be evaluated by alert engine
                    ident = getattr(obj, attname)

                    if model == name_model:
                        # name is just a "friendly" name, only used in the GUI
                        # to make it easier to add expressions. We only set it
                        # if the models for both id and name are the same.
                        name = getattr(obj, name_attname)

                        if name != ident:
                            # If id and name are not equal we make a nice
                            # string with both. If they are the same we only
                            # use id, as both would be redundant.
                            choices.append((ident, '%s: %s' % (ident, name)))
                            continue
                    choices.append((ident, ident))

                # At last we acctually add the multiple choice field.
                self.fields['value'] = forms.MultipleChoiceField(choices=choices)
                self.fields['value'].widget.attrs['class'] = 'select2'
            else:
                self.fields['value'] = forms.CharField(required=True)

    def clean(self) -> dict[str, Any]:
        validated_data = super().clean()

        match_field = validated_data["match_field"]
        operator_type = int(validated_data["operator"])
        value = validated_data["value"]

        if match_field.data_type == MatchField.IP:
            validated_data["value"] = self._clean_ip_addresses(
                operator_type=operator_type, value=value
            )
            return validated_data

        if operator_type == Operator.IN:
            validated_data["value"] = "|".join(value)
        elif operator_type == Operator.EQUALS and isinstance(value, list):
            validated_data["value"] = value[0]

        return validated_data

    def _clean_ip_addresses(self, operator_type, value):
        if operator_type == Operator.IN:
            ip_list = value.split()
        else:
            ip_list = [value]
        validated_ip_addresses = []
        for ip in ip_list:
            if not is_valid_ip(ip=ip, strict=True) and not is_valid_cidr(cidr=ip):
                self.add_error(
                    field="value",
                    error=forms.ValidationError(("Invalid IP address: %s" % ip)),
                )
            else:
                validated_ip_addresses.append(str(ip))

        return "|".join(validated_ip_addresses)
