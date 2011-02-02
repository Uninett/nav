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

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import transaction

from nav.web.message import new_message, Messages
from nav.models.manage import Netbox
from nav.models.service import Service, ServiceProperty

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

