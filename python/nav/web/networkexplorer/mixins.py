import json

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
            context_dict,
            cls=DjangoJSONEncoder,
            **self.get_json_dumps_kwargs())
        return HttpResponse(json_context,
                            content_type=self.content_type,
                            status=status)

    def render_json_object_response(self, objects, **kwargs):
        """
        Serializes objects using Django's builtin JSON serializer. Additional
        kwargs can be used the same way for django.core.serializers.serialize.
        """
        json_data = serializers.serialize('json', objects, **kwargs)
        return HttpResponse(json_data, content_type=self.content_type)


class GetRoutersMixin(object):
    """
    Fetches all the routers on the network
    """
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
                'fields': model_to_dict(router, fields=('sysname',))
            }
            for router in kwargs.pop('object_list')
        ]
        return context


class GetGWPortsMixin(object):
    """
    A mixin to 'hide away' the ugly legacy logic of
    expand_router
    """
    def get_context_data(self, **kwargs):
        router = kwargs.pop('object')
        gwports = router.get_gwports()
        sorted_ports = sorted(
            gwports,
            key=lambda p: natsort.split(p.ifname)
        )
        context = []
        for gwport in sorted_ports:
            c = {
                'pk': gwport.pk,
                'sysname': router.sysname,
                'type': 'gwport',
                'fields': model_to_dict(gwport),
            }
            if gwport.to_netbox:
                c.update({
                    'netbox_sysname': gwport.to_netbox.sysname,
                    'trunk_port': gwport.to_interface.trunk,
                })
            c.update(self._get_expandable(gwport))
            context.append(c)

        return context

    @staticmethod
    def _get_expandable(gwport):
        gwport_prefixes = []
        has_children = False

        prefixes = GwPortPrefix.objects.filter(
            interface_id=gwport.id
        ).exclude(
            prefix__vlan__net_type='static')
        for prefix in prefixes:
            netmask_pos = prefix.prefix.net_address.rfind('/')
            netmask = prefix.prefix.net_address[netmask_pos:]
            p = {
                'display_addr': prefix.gw_ip + netmask,
                'net_type': str(prefix.prefix.vlan.net_type),
                'net_ident': str(prefix.prefix.vlan.net_ident),
            }
            gwport_prefixes.append(p)

            vlans = prefix.prefix.vlan.swportvlan_set.exclude(
                vlan__net_type='static'
            ).filter(
                interface__netbox=gwport.netbox)
            for vlan in vlans:
                if not vlan.interface.swportblocked_set.filter(
                        vlan=vlan.vlan.vlan).count():
                    has_children = True
                    break
        gwport_prefixes.sort(key=lambda d: d['display_addr'])

        if not gwport.to_netbox and gwport.to_interface:
            gwport.to_netbox = gwport.to_interface.netbox
        else:
            # FIXME: Find out what the legacy code is trying
            # FIXME: to achieve here or remove else-clause.
            pass

        return {'prefixes': gwport_prefixes, 'expandable': has_children}


class GetSWPortsMixin(object):
    """
    A mixin to 'hide away' the even uglier legacy
    logic of expand_gwport
    """
    def get_context_data(self, **kwargs):
        gwport = kwargs.pop('object')
        prefixes = gwport.gwportprefix_set.exclude(
            prefix__vlan__net_type='static')

        vlans = []
        vlans_found = {}
        for prefix in prefixes:
            # TODO: Use select related?
            for vlan in prefix.prefix.vlan.swportvlan_set.filter(
                    interface__netbox=gwport.netbox).order_by(
                    'interface__ifname'):

                # Check if port is spanningtreeblocked
                if vlan.interface.swportblocked_set.filter(
                    vlan=vlan.vlan.vlan  # really!
                ).count():
                    continue

                # Check for children, services and connection
                # to switches
                elif vlan and not vlan.pk in vlans_found:
                    vlans_found[vlan.pk] = True
                    vlan_context = {
                        'pk': vlan.interface.pk,  # FIXME added .interface
                        'type': 'swport',
                        'interface': model_to_dict(vlan.interface),
                        'netbox_sysname': vlan.interface.netbox.sysname,
                        'to_netbox_sysname': vlan.interface.to_netbox.sysname
                        if vlan.interface.to_netbox else '',
                        'to_netbox_sysname_short':
                        vlan.interface.to_netbox.get_short_sysname()
                        if vlan.interface.to_netbox else '',
                        'to_interface_netbox_sysname':
                        vlan.interface.to_interface.netbox.sysname
                        if vlan.interface.to_interface else '',
                        'to_interface_netbox_sysname_short':
                        vlan.interface.to_interface.netbox.get_short_sysname()
                        if vlan.interface.to_interface else '',
                        'module_netbox_sysname':
                        vlan.interface.module.netbox.sysname
                        if vlan.interface.module else '',
                    }
                    vlan_context.update(self._get_expandable(vlan))

                    vlans.append(vlan_context)
        sorted_vlans = sorted(
            vlans,
            key=lambda vlan: natsort.split(vlan['interface']['ifname']))
        return sorted_vlans

    @staticmethod
    def _get_expandable(vlan):
        has_children = False
        has_services = False
        connected_to_switch = False
        interface = vlan.interface
        connected_interface = interface.to_interface
        c = {}

        if (interface.to_netbox and
                interface.to_netbox.service_set.count()):
            has_children = True
            has_services = True

        if (connected_interface and
            connected_interface.netbox.category.id
                in ('SW', 'GSW', 'EDGE')):
            has_children = True
            connected_to_switch = True
            c.update({
                'switch_id': interface.to_netbox.id,
                'vlan_id': vlan.vlan.id
            })

        if not has_children:

            if (connected_interface and
                    connected_interface.netbox.service_set.count()):
                has_children = True

            elif Cam.objects.filter(
                netbox=interface.netbox,
                ifindex=interface.ifindex,
                end_time__gt=dt.max
            ).count():
                has_children = True

            elif connected_interface and Cam.objects.filter(
                netbox=connected_interface.netbox,
                ifindex=connected_interface.ifindex,
                end_time__gt=dt.max
            ).count():
                has_children = True

        c.update({
            'expandable': has_children,
            'has_services': has_services,
            'connected_to_switch': connected_to_switch,
        })
        return c


class GetSWPortVlansMixin(object):
    """
    """
    def get_context_data(self, **kwargs):
        switch = kwargs.pop('object')
        vlan_id = self.kwargs.pop('vlan_id', None)
        swports = switch.get_swports()
        swport_vlans = SwPortVlan.objects.select_related(
            'interface__netbox',
            'interface__to_interface__netbox',
            'interface__to_netbox',
        ).filter(
            interface__in=swports,
            vlan__id=vlan_id)

        context = []

        for vlan in swport_vlans:
            interface = vlan.interface
            c = {
                'pk': vlan.pk,
                'type': 'switch',
                'interface': model_to_dict(interface),
                'interface_netbox_sysname': interface.netbox.sysname,
                'interface_netbox_sysname_short':
                unicode(interface.netbox.sysname),
            }
            c.update(self._get_connected_sysname(interface))
            if (interface.to_interface
                    and interface.netbox.service_set.all().count()):
                c.update({'expandable': True})

            elif Cam.objects.filter(
                    netbox=interface.netbox,
                    ifindex=interface.ifindex,
                    end_time__gt=dt.max).count():
                c.update({'expandable': True})
            context.append(c)
        return sorted(
            context,
            key=lambda vlan: natsort.split(vlan['interface']['ifname'])
        )

    @staticmethod
    def _get_connected_sysname(interface):
        if interface.to_netbox:
            return {
                'connected_to': {
                    'sysname': interface.to_netbox.sysname,
                    'short': unicode(interface.to_netbox)
                }
            }
        elif interface.to_interface:
            return {
                'connected_to': {
                    'sysname': interface.to_interface.netbox.sysname,
                    'short': unicode(interface.to_interface.netbox)
                }
            }
        else:
            return {}