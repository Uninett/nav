"""Forms and view functions for editing services in SeedDB"""

#
# Copyright (C) 2011, 2013-2015 Uninett AS
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

from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.db import transaction
from django.urls import reverse

from nav.models.service import Service, ServiceProperty
from nav.models.manage import Netbox
from nav.web.crispyforms import (
    FlatFieldset,
    SubmitField,
    set_flat_form_attributes,
)
from nav.web.servicecheckers import get_description, load_checker_classes
from nav.web.message import new_message, Messages
from nav.web.seeddb.page.service import ServiceInfo


class ServiceChoiceForm(forms.Form):
    """Form for editing services"""

    def __init__(self, *args, **kwargs):
        super(ServiceChoiceForm, self).__init__(*args, **kwargs)
        # NB: Setting the TextInput to hidden is done to display the label.
        #     The HiddenInput widget will remove the label
        self.fields['netbox'] = forms.CharField(
            label='IP Device', widget=forms.TextInput(attrs={'type': 'hidden'})
        )
        self.fields['service'] = forms.ChoiceField(
            choices=sorted(self._build_checker_choices()),
            widget=forms.Select(attrs={'class': 'select2'}),
        )

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Add new service checker",
                    fields=[
                        self["netbox"],
                        self["service"],
                        SubmitField(value="Continue", css_classes='small'),
                    ],
                )
            ],
            form_id="service_checker_add_form",
        )

    @staticmethod
    def _build_checker_choices():
        checkers = load_checker_classes()
        choices = []
        for checker in checkers:
            name = checker.get_type()
            descr = []
            if checker.DESCRIPTION:
                descr.append(checker.DESCRIPTION)
            if not checker.IPV6_SUPPORT:
                descr.append("Not IPv6 compatible")
            descr = "; ".join(descr)
            descr = "%s (%s)" % (name, descr) if descr else name
            choices.append((name, descr))
        return choices

    @staticmethod
    def _build_netbox_choices():
        return [(n.id, n.sysname) for n in Netbox.objects.all().order_by('sysname')]


class ServiceForm(forms.Form):
    """Form for adding hidden fields to a service property edit"""

    service = forms.IntegerField(widget=forms.HiddenInput, required=False)
    handler = forms.CharField(widget=forms.HiddenInput)
    netbox = forms.IntegerField(widget=forms.HiddenInput)


class ServicePropertyForm(forms.Form):
    """Form for editing service properties"""

    def __init__(self, *args, **kwargs):
        service_description = kwargs.pop('service_args')
        super(ServicePropertyForm, self).__init__(*args, **kwargs)
        args = service_description.get('args')
        opt_args = service_description.get('optargs')

        if args:
            for arg, descr in args:
                self.fields[arg] = forms.CharField(required=True, help_text=descr)
        if opt_args:
            for arg, descr in opt_args:
                self.fields[arg] = forms.CharField(required=False, help_text=descr)


def service_edit(request, service_id=None):
    """Controller for editing services"""
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
            property_form = ServicePropertyForm(
                request.POST, service_args=get_description(handler)
            )
            if property_form.is_valid():
                return service_save(request, service_form, property_form)
    else:
        if not service_id:
            return service_add(request)
        else:
            handler = service.handler
            netbox = service.netbox
            service_prop = ServiceProperty.objects.filter(service=service)
            service_form = ServiceForm(
                initial={
                    'service': service.pk,
                    'netbox': netbox.pk,
                    'handler': handler,
                }
            )
            initial = {prop.property: prop.value for prop in service_prop}
            property_form = ServicePropertyForm(
                service_args=get_description(service.handler), initial=initial
            )

    info = ServiceInfo()
    context = info.template_context
    context.update(
        {
            'object': service,
            'handler': handler,
            'netbox': netbox,
            'sub_active': {'edit': True},
            'service_form': service_form,
            'property_form': property_form,
        }
    )
    return render(request, 'seeddb/service_property_form.html', context)


def service_add(request):
    """Controller for adding services"""
    info = ServiceInfo()
    if request.method == 'POST':
        choice_form = ServiceChoiceForm(request.POST)
        if choice_form.is_valid():
            cleaned_data = choice_form.cleaned_data
            service_id = cleaned_data['service']
            netbox_id = cleaned_data['netbox']
            netbox = Netbox.objects.get(pk=netbox_id)

            property_form = ServicePropertyForm(
                service_args=get_description(service_id)
            )
            service_form = ServiceForm(
                initial={
                    'netbox': netbox_id,
                    'handler': service_id,
                }
            )

            context = info.template_context
            context.update(
                {
                    'service_form': service_form,
                    'property_form': property_form,
                    'sub_active': {'add': True},
                    'handler': service_id,
                    'netbox': netbox,
                }
            )
            return render(request, 'seeddb/service_property_form.html', context)
    else:
        choice_form = ServiceChoiceForm()

    context = info.template_context
    context.update(
        {
            'choice_form': choice_form,
            'sub_active': {'add': True},
        }
    )
    return render(request, 'seeddb/service_netbox_form.html', context)


@transaction.atomic()
def service_save(request, service_form, property_form):
    """Saves a service based on two form inputs"""
    service_id = service_form.cleaned_data.get('service')
    if service_id:
        service = Service.objects.select_related('netbox').get(pk=service_id)
        ServiceProperty.objects.filter(service=service).delete()
        netbox = service.netbox
    else:
        netbox = Netbox.objects.get(pk=service_form.cleaned_data['netbox'])
        service = Service.objects.create(
            netbox=netbox, handler=service_form.cleaned_data['handler']
        )
    for prop, value in property_form.cleaned_data.items():
        if value:
            ServiceProperty.objects.create(service=service, property=prop, value=value)
    new_message(
        request,
        "Saved service for handler %s on %s" % (service.handler, netbox),
        Messages.SUCCESS,
    )
    return HttpResponseRedirect(reverse('seeddb-service'))
