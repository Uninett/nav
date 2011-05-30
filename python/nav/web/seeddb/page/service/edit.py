# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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

from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.db import transaction

from nav.models.service import Service, ServiceProperty
from nav.models.manage import Netbox
from nav.web.serviceHelper import getCheckers, getDescription
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect

from nav.web.seeddb.page.service import ServiceInfo

class ServiceChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ServiceChoiceForm, self).__init__(*args, **kwargs)
        checkers = [(service, service) for service in getCheckers()]
        checkers.sort()
        self.fields['service'] = forms.ChoiceField(
            choices=checkers)

class ServiceForm(forms.Form):
    service = forms.IntegerField(
        widget=forms.HiddenInput, required=False)
    handler = forms.CharField(
        widget=forms.HiddenInput)
    netbox = forms.IntegerField(
        widget=forms.HiddenInput)

class ServicePropertyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        service_description = kwargs.pop('service_args')
        super(ServicePropertyForm, self).__init__(*args, **kwargs)
        args = service_description.get('args')
        opt_args = service_description.get('optargs')

        if args:
            for arg in args:
                self.fields[arg] = forms.CharField(required=True)
        if opt_args:
            for arg in opt_args:
                self.fields[arg] = forms.CharField(required=False)

def service_edit(request, service_id=None):
    service = None
    netbox = None
    service_form = None
    property_form = None
    if service_id:
        service = Service.objects.get(pk=service_id)

    if request.method == 'POST' and 'save' in request.POST:
        service_form = ServiceForm(request.POST)
        if service_form.is_valid():
            handler = service_form.cleaned_data['handler']
            property_form = ServicePropertyForm(request.POST,
                service_args=getDescription(handler))
            if property_form.is_valid():
                return service_save(request, service_form, property_form)
    else:
        if not service_id:
            return service_add(request)
        else:
            handler = service.handler
            netbox = service.netbox
            service_prop = ServiceProperty.objects.filter(service=service)
            service_form = ServiceForm(initial={
                'service': service.pk,
                'netbox': netbox.pk,
                'handler': handler,
            })
            initial = dict(
                [(prop.property, prop.value) for prop in service_prop])
            property_form = ServicePropertyForm(
                service_args=getDescription(service.handler),
                initial=initial)

    info = ServiceInfo()
    context = info.template_context
    context.update({
        'object': service,
        'handler': handler,
        'netbox': netbox,
        'sub_active': {'edit': True},
        'service_form': service_form,
        'property_form': property_form,
    })
    return render_to_response('seeddb/service_property_form.html',
        context, RequestContext(request))

def service_add(request):
    info = ServiceInfo()
    box_select = QuickSelect(
        location=False,
        room=False,
        netbox=True,
        netbox_multiple=False)
    if request.method == 'POST':
        choice_form = ServiceChoiceForm(request.POST)
        netbox_id = request.POST.get('netbox')
        try:
            netbox = Netbox.objects.get(pk=netbox_id)
        except Netbox.DoesNotExist:
            new_message(
                request._req,
                "Netbox does not exist in database",
                Messages.ERROR)
        else:
            if choice_form.is_valid():
                property_form = ServicePropertyForm(
                    service_args=getDescription(
                        choice_form.cleaned_data['service']
                    ))
                service_form = ServiceForm(initial={
                    'netbox': netbox.pk,
                    'handler': choice_form.cleaned_data['service'],
                })
                context = info.template_context
                context.update({
                    'service_form': service_form,
                    'property_form': property_form,
                    'sub_active': {'add': True},
                    'handler': choice_form.cleaned_data['service'],
                    'netbox': netbox,
                })
                return render_to_response('seeddb/service_property_form.html',
                    context, RequestContext(request))
    else:
        choice_form = ServiceChoiceForm()

    context = info.template_context
    context.update({
        'box_select': box_select,
        'choice_form': choice_form,
        'sub_active': {'add': True},
    })
    return render_to_response('seeddb/service_netbox_form.html',
        context, RequestContext(request))

@transaction.commit_on_success
def service_save(request, service_form, property_form):
    service_id = service_form.cleaned_data.get('service')
    if service_id:
        service = Service.objects.select_related(
            'netbox').get(pk=service_id)
        ServiceProperty.objects.filter(service=service).delete()
        netbox = service.netbox
    else:
        netbox = Netbox.objects.get(pk=service_form.cleaned_data['netbox'])
        service = Service.objects.create(
            netbox=netbox,
            handler=service_form.cleaned_data['handler']
        )
    for (prop, value) in property_form.cleaned_data.items():
        if value:
            ServiceProperty.objects.create(
                service=service,
                property=prop,
                value=value
            )
    new_message(
        request._req,
        "Saved service for handler %s on %s" % (service.handler, netbox),
        Messages.SUCCESS)
    return HttpResponseRedirect(reverse('seeddb-service'))
