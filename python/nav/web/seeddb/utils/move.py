# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from nav.django.utils import get_verbose_name

from nav.web.message import new_message, Messages

STEP_CHANGEVALUES = 0  # Dropdown boxes with new values
STEP_CONFIRM = 1  # What the objects will look like afterwards
STEP_SAVE = 2  # Update the objects


def move(request, model, form_model, redirect, title_attr='id', extra_context=None):
    if not extra_context:
        extra_context = {}

    # If no post or no objects selected, start over
    if request.method != 'POST':
        return HttpResponseRedirect(reverse(redirect))
    if not request.POST.getlist('object'):
        new_message(
            request, "You need to select at least one object to edit", Messages.ERROR
        )
        return HttpResponseRedirect(reverse(redirect))

    data = None
    confirm = False
    verbose_name = model._meta.verbose_name
    objects = model.objects.filter(id__in=request.POST.getlist('object'))

    # Find out what step we are on, or default to start of wizard
    try:
        step = int(request.POST.get('step', '0'))
    except ValueError:
        step = STEP_CHANGEVALUES

    # Choose new values to foreign keys
    if step == STEP_CHANGEVALUES:
        form = form_model()
        step = STEP_CONFIRM

    # Confirm the changes
    elif step == STEP_CONFIRM:
        form = form_model(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            confirm = True
            step = STEP_SAVE

    # Update the objects
    elif step == STEP_SAVE:
        form = form_model(request.POST)
        if form.is_valid():
            foreign_keys = form.cleaned_data.keys()
            data = dict()

            # If nothing is selected, don't update
            for key in foreign_keys:
                if form.cleaned_data[key] is not None:
                    data[key] = form.cleaned_data[key]

            # Update
            objects.update(**data)

            # Generate message based on what was changed and redirect back
            foreign_key_string = ", ".join(
                [get_verbose_name(model, key) for key in data]
            )

            if foreign_key_string == "":
                foreign_key_string = "nothing"

            new_message(
                request,
                "Changed %s on %i %s models"
                % (foreign_key_string, len(objects), verbose_name),
                Messages.SUCCESS,
            )

            return HttpResponseRedirect(reverse(redirect))

    # Keep values from the form and pass them as context
    fields = list(form.fields.keys() if form else form_model().fields.keys())

    values = objects.values('pk', title_attr, *fields)
    object_list = _parse_value_differences(values, data, title_attr, fields)

    context = {
        'form': form or '',
        'objects': objects,
        'values': object_list,
        'data': data,
        'confirm': confirm,
        'sub_active': {'list': True},
        'title': 'Move %s' % verbose_name,
        'step': step,
    }

    extra_context.update(context)

    return render(request, 'seeddb/move.html', extra_context)


def _parse_value_differences(values, data, title_attr, fields):
    """Creates a data structure describing the before/after values of a
    requested move operation.  Output can be used in templates to show a
    preview of the changes that will be made.

    """
    object_list = []
    attr_list = [title_attr] + fields

    for obj in values:
        row = {
            'pk': obj['pk'],
            'values': [("Current %s" % attr, obj[attr]) for attr in attr_list],
        }

        # If the form has data, format the fields with new values
        if data:
            new_values = []
            for attr in fields:
                if data[attr] is not None:
                    new_values.append(("New %s" % attr, data[attr]))
                else:
                    new_values.append(("New %s" % attr, obj[attr]))

            row['values'].extend(new_values)
        object_list.append(row)

    return object_list
