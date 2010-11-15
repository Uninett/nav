# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.django.utils import get_verbose_name

from nav.web.message import new_message, Messages
from nav.web.seeddb.forms.move import MoveOperationForm

def move(request, model, form_model, redirect, title_attr='id', extra_context={}):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse(redirect))
    if not len(request.POST.getlist('object')):
        new_message(
            request._req,
            "You need to select at least one object to edit",
            Messages.ERROR)
        return HttpResponseRedirect(reverse(redirect))

    data = None
    confirm = False
    verbose_name = model._meta.verbose_name
    objects = model.objects.filter(id__in=request.POST.getlist('object'))
    try:
        step = int(request.POST.get('step', '0'))
    except ValueError:
        step = 0

    form = ''
    op_form = ''
    if step == 0:
        op_form = MoveOperationForm(form=form_model(), hidden=False)
        step = 1
    else:
        op_form = MoveOperationForm(
            request.POST, form=form_model(), hidden=True)
        if not op_form.is_valid():
            # Since the MoveOperationForm instance was made with hidden=True we
            # need to make it again (and validate it) if there was a error,
            # with hidden=False this time.
            op_form = MoveOperationForm(
                request.POST, form=form_model(), hidden=False)
            op_form.is_valid()
            step = 1
        else:
            if step == 1:
                form = form_model(operation_form=op_form)
                step = 2
            elif step == 2:
                form = form_model(request.POST, operation_form=op_form)
                if form.is_valid():
                    data = form.cleaned_data
                    confirm = True
                    step = 3
            elif step == 3:
                form = form_model(request.POST, operation_form=op_form)
                if form.is_valid():
                    foreign_keys = form.cleaned_data.keys()
                    data = dict([(key, form.cleaned_data[key]) for key in foreign_keys])
                    objects.update(**data)
                    foreign_key_string = ", ".join([get_verbose_name(model, key) for key in foreign_keys])
                    new_message(
                        request._req,
                        "Changed %s on %i %s models" % (foreign_key_string, len(objects), verbose_name),
                        Messages.SUCCESS)
                    return HttpResponseRedirect(reverse(redirect))

    # Form instances may be modified by the operation_form, so if we have a
    # specific instance we will use the fields from that one.
    if form:
        fields = form.fields.keys()
    else:
        fields = form_model().fields.keys()
    values = objects.values('pk', title_attr, *fields)
    object_list = _process_values(values, data, title_attr, fields)

    context = {
        'form': form,
        'operation_form': op_form,
        'objects': objects,
        'values': object_list,
        'data': data,
        'confirm': confirm,
        'active': {'list': True},
        'title': 'Move %s' % verbose_name,
        'step': step,
    }
    extra_context.update(context)
    return render_to_response('seeddb/move.html',
        extra_context, RequestContext(request))

def _process_values(values, data, title_attr, fields):
    object_list = []
    attr_list = [title_attr] + fields
    for obj in values:
        row = {
            'pk': obj['pk'],
            'values': [("Current %s" % attr, obj[attr]) for attr in attr_list],
        }
        if data:
            new_values = [("New %s" % attr, data[attr]) for attr in fields]
            row['values'].extend(new_values)
        object_list.append(row)
    return object_list
