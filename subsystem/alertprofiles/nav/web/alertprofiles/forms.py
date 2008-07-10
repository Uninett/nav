# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from django import newforms as forms

from nav.models.profiles import MatchField, Filter, Expresion, Operator, FilterGroup

class FilterGroupForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    owner = forms.BooleanField(required=False, label='Private')
    description = forms.CharField(required=False)

    class Meta:
        model = FilterGroup
        exclude = ('group_permisions',)

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        super(FilterGroupForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

class FilterForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    owner = forms.BooleanField(required=False, label=u'Private',
        help_text=u'Uncheck to allow all users to use this filter.')

    class Meta:
        model = Filter

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)
        super(FilterForm, self).__init__(*args, **kwargs)

        if not admin:
            self.fields['owner'].widget.attrs['disabled'] = 'disabled'

class MatchFieldForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)
    list_limit = forms.ChoiceField(
            choices=((100,100),(200,200),(300,300),(500,500),(1000,'1 000'),(10000,'10 000')),
            initial=300,
            help_text=u'Only this many options will be available in the list. Only does something when "Show list" is checked.',
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

class ExpresionForm(forms.ModelForm):
    filter = forms.IntegerField(widget=forms.widgets.HiddenInput)
    match_field = forms.IntegerField(widget=forms.widgets.HiddenInput)

    class Meta:
        model = Expresion

    def __init__(self, *args, **kwargs):
        match_field = kwargs.pop('match_field', None)
        super(ExpresionForm, self).__init__(*args, **kwargs)

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
