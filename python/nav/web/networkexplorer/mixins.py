import json
import socket
from datetime import datetime as dt

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.forms.models import model_to_dict

from nav import natsort
from nav.models.manage import Cam, Arp, GwPortPrefix, Netbox, SwPortVlan


class JSONResponseMixin(object):
    """A mixin that lets class-based views return JSON

    More or less identical to the JSONResponseMixin in
    the django-braces project

    TODO: Refactor out for reusability
    """

    content_type = "application/json"
    json_dumps_kwargs = {'indent': 2}

    def get_json_dumps_kwargs(self):
        if self.json_dumps_kwargs is None:
            self.json_dumps_kwargs = {}
        self.json_dumps_kwargs.setdefault('ensure_ascii', False)
        return self.json_dumps_kwargs

    def render_json_response(self, context_dict, status=200):
        """
        Limited serialization for shipping plain data. Do not use for models
        or other complex or custom objects.
        """
        json_context = json.dumps(
            context_dict, cls=DjangoJSONEncoder, **self.get_json_dumps_kwargs()
        )
        return HttpResponse(json_context, content_type=self.content_type, status=status)

    def render_json_object_response(self, objects, **kwargs):
        """
        Serializes objects using Django's builtin JSON serializer. Additional
        kwargs can be used the same way for django.core.serializers.serialize.
        """
        json_data = serializers.serialize('json', objects, **kwargs)
        return HttpResponse(json_data, content_type=self.content_type)


class GetRoutersMixin(object):
    """Fetches all the routers on the network"""

    model = Netbox

    def get_queryset(self):
        queryset = super(GetRoutersMixin, self).get_queryset()
        return queryset.filter(category__in=['GW', 'GSW'])

    def get_context_data(self, **kwargs):
        context = [
            {
                'pk': router.pk,
                'type': 'router',
                'expandable': router.get_gwports().count() > 0,
                'fields': model_to_dict(router, fields=('sysname',)),
            }
            for router in kwargs.pop('object_list', self.object_list)
        ]
        return context


class ExpandRouterContextMixin(object):
    """
    A mixin to 'hide away' the ugly legacy logic of
    expand_router
    """

    def get_context_data(self, **kwargs):
        router = kwargs.pop('object')
        gwports = router.get_gwports().select_related('to_netbox', 'to_interface')
        sorted_ports = sorted(gwports, key=lambda p: natsort.split(p.ifname))
        context = []
        for gwport in sorted_ports:
            c = {
                'pk': gwport.pk,
                'sysname': router.sysname,
                'type': 'gwport',
                'fields': model_to_dict(gwport),
            }
            if gwport.to_netbox:
                c.update(
                    {
                        'netbox_sysname': gwport.to_netbox.sysname,
                        'trunk_port': (
                            gwport.to_interface.trunk if gwport.to_interface else None
                        ),
                    }
                )
            c.update(self._get_expandable(gwport))
            context.append(c)

        return context

    @staticmethod
    def _get_expandable(gwport):
        gwport_prefixes = []
        has_children = False

        prefixes = (
            GwPortPrefix.objects.select_related(
                'prefix__vlan',
                'interface',
            )
            .filter(interface_id=gwport.id)
            .exclude(prefix__vlan__net_type='static')
        )
        for prefix in prefixes:
            netmask_pos = prefix.prefix.net_address.rfind('/')
            netmask = prefix.prefix.net_address[netmask_pos:]
            p = {
                'display_addr': prefix.gw_ip + netmask,
                'net_type': str(prefix.prefix.vlan.net_type),
                'net_ident': str(prefix.prefix.vlan.net_ident),
            }
            gwport_prefixes.append(p)

            vlans = prefix.prefix.vlan.swport_vlans.exclude(
                vlan__net_type='static'
            ).filter(interface__netbox=gwport.netbox)
            for vlan in vlans:
                if not vlan.interface.blocked_swports.filter(
                    vlan=vlan.vlan.vlan
                ).count():
                    has_children = True
                    break
        gwport_prefixes.sort(key=lambda d: d['display_addr'])

        if not gwport.to_netbox and gwport.to_interface:
            gwport.to_netbox = gwport.to_interface.netbox

        return {'prefixes': gwport_prefixes, 'expandable': has_children}


class ExpandGWPortMixin(object):
    """
    A mixin to 'hide away' the even uglier legacy
    logic of expand_gwport
    """

    def get_context_data(self, **kwargs):
        gwport = kwargs.pop('object')
        prefixes = gwport.gwport_prefixes.select_related(
            'prefix__vlan',
        ).exclude(prefix__vlan__net_type='static')

        vlans = []
        vlans_found = set()
        for prefix in prefixes:
            for vlan in (
                prefix.prefix.vlan.swport_vlans.select_related(
                    'interface__to_interface__netbox',
                    'interface__netbox',
                    'vlan',
                )
                .filter(interface__netbox=gwport.netbox)
                .order_by('interface__ifname')
            ):
                # Check if port is spanningtreeblocked
                if vlan.interface.blocked_swports.filter(
                    vlan=vlan.vlan.vlan  # really!
                ).count():
                    continue

                elif vlan and vlan.pk not in vlans_found:
                    vlans_found.add(vlan.pk)
                    interface = vlan.interface
                    vlan_context = {
                        'pk': interface.pk,
                        'type': 'swport',
                        'interface': model_to_dict(interface),
                        'netbox_sysname': interface.netbox.sysname,
                        'module_netbox_sysname': (
                            interface.module.netbox.sysname if interface.module else ''
                        ),
                        'subheader_vlan': str(vlan.vlan.vlan),
                        'subheader_netbox': str(interface.netbox),
                    }
                    # Check for children, services and connection
                    # to switches
                    vlan_context.update(self._get_expandable(vlan))
                    vlan_context.update(_get_connected_sysname(interface))
                    vlans.append(vlan_context)
        sorted_vlans = sorted(
            vlans, key=lambda vlan: natsort.split(vlan['interface']['ifname'])
        )
        return sorted_vlans

    @staticmethod
    def _get_expandable(vlan):
        has_children = False
        has_services = False
        connected_to_switch = False
        interface = vlan.interface
        connected_interface = interface.to_interface
        c = {}

        if interface.to_netbox and interface.to_netbox.services.count():
            has_children = True
            has_services = True

        if connected_interface and connected_interface.netbox.category.id in (
            'SW',
            'GSW',
            'EDGE',
        ):
            has_children = True
            connected_to_switch = True
            c.update({'switch_id': interface.to_netbox.id, 'vlan_id': vlan.vlan.id})

        if not has_children:
            if connected_interface and connected_interface.netbox.services.count():
                has_children = True

            elif Cam.objects.filter(
                netbox=interface.netbox, ifindex=interface.ifindex, end_time__gt=dt.max
            ).count():
                has_children = True

            elif (
                connected_interface
                and Cam.objects.filter(
                    netbox=connected_interface.netbox,
                    ifindex=connected_interface.ifindex,
                    end_time__gt=dt.max,
                ).count()
            ):
                has_children = True

        c.update(
            {
                'expandable': has_children,
                'has_services': has_services,
                'connected_to_switch': connected_to_switch,
            }
        )
        return c


class ExpandSwitchContextMixin(object):
    """Mixin implementing the logic for expanding a swport"""

    def get_context_data(self, **kwargs):
        switch = kwargs.pop('object')
        vlan_id = self.kwargs.pop('vlan_id', None)
        swports = switch.get_swports()
        swport_vlans = SwPortVlan.objects.filter(
            interface__in=swports, vlan__id=vlan_id
        )
        switch_has_services = switch.services.all().count()

        context = []

        for vlan in swport_vlans:
            interface = vlan.interface
            c = {
                'pk': vlan.interface.pk,
                'type': 'switch',
                'expandable': False,
                'interface': model_to_dict(interface),
                'interface_netbox_sysname': interface.netbox.sysname,
                'interface_netbox_sysname_short': str(interface.netbox.sysname),
            }
            c.update(_get_connected_sysname(interface))
            if interface.to_interface and switch_has_services:
                c.update({'expandable': True})

            elif Cam.objects.filter(
                netbox=interface.netbox, ifindex=interface.ifindex, end_time__gt=dt.max
            ).count():
                c.update({'expandable': True})
            context.append(c)
        return sorted(
            context, key=lambda vlan: natsort.split(vlan['interface']['ifname'])
        )


class ExpandSWPortContextMixin(object):
    """Mixin implementing the logic for expanding a swport"""

    def get_context_data(self, **kwargs):
        swport = kwargs.pop('object')
        to_netbox = swport.to_netbox or swport.to_interface.netbox or None
        services = to_netbox.services.all() if to_netbox else []

        active_macs = Cam.objects.filter(
            netboc=swport.netbox, ifindex=swport.ifindex, end_time__gt=dt.max
        )
        hosts_behind_port = set()
        for mac in active_macs:
            arp_entries = Arp.objects.filter(mac=mac.mac, end_time__gt=dt.max)
            for arp_entry in arp_entries:
                try:
                    hostname = socket.gethostbyaddr(arp_entry.ip)[0]
                except socket.herror:
                    hostname = ''
                finally:
                    # TODO: Use reverse
                    host_string = """
                        {0} ({1}) [<a href="/machinetracker/mac?mac={2}&days=7"
                                    target="_blank">{3}</a>]
                        """.format(hostname, arp_entry.ip, mac.mac, mac.mac)
                hosts_behind_port.add(host_string)
            if not arp_entries and mac.mac not in hosts_behind_port:
                hosts_behind_port.add(mac.mac)
        return {
            'type': 'swport-leaf',
            'netbox': to_netbox,
            'services': services,
            'active_hosts': sorted(hosts_behind_port),
        }


def _get_connected_sysname(interface):
    if interface.to_netbox:
        return {
            'connected_to': {
                'sysname': interface.to_netbox.sysname,
                'short': str(interface.to_netbox),
            }
        }
    elif interface.to_interface:
        return {
            'connected_to': {
                'sysname': interface.to_interface.netbox.sysname,
                'short': str(interface.to_interface.netbox),
            }
        }
    else:
        return {}
