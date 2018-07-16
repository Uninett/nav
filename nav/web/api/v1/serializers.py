#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=R0903
"""Serializers for the NAV REST api"""

from nav.models import manage, cabling, rack, profiles
from rest_framework import serializers


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for accounts"""
    accountgroups = serializers.PrimaryKeyRelatedField(
        source='accountgroup_set', many=True,
        queryset=profiles.AccountGroup.objects.all())

    class Meta(object):
        model = profiles.Account
        fields = ('id', 'login', 'name', 'ext_sync', 'preferences', 'organizations',
                  'accountgroups')


class AccountGroupSerializer(serializers.ModelSerializer):
    """Serializer for accountgroups"""
    class Meta(object):
        model = profiles.AccountGroup
        fields = ('id', 'name', 'description', 'accounts')


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for netboxentities"""
    serial = serializers.CharField(source='device')

    class Meta(object):
        model = manage.NetboxEntity
        fields = ('id', 'name', 'descr', 'serial', 'vendor_type',
                  'hardware_revision', 'firmware_revision', 'software_revision',
                  'mfg_name', 'model_name', 'fru', 'mfg_date')


class NetboxTypeSerializer(serializers.ModelSerializer):
    """Serializer for the type model"""

    class Meta(object):
        model = manage.NetboxType()
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for the location model"""
    class Meta(object):
        model = manage.Location
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for the room model"""
    position = serializers.ListField(
        child=serializers.DecimalField(max_digits=20, decimal_places=12),
        read_only=True)

    class Meta(object):
        model = manage.Room
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = manage.Organization
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta(object):
        model = manage.Category
        fields = '__all__'


class SubNetboxSerializer(serializers.ModelSerializer):
    object_url = serializers.CharField(source='get_absolute_url')
    class Meta(object):
        model = manage.Netbox
        fields = '__all__'


class NetboxSerializer(serializers.ModelSerializer):
    """Serializer for the netbox model"""
    chassis = EntitySerializer(source='get_chassis', many=True, read_only=True)
    sysname = serializers.CharField(required=False)

    # We need two fields for related fields that are required: one for reading
    # (room) and one for writing (roomid).
    #
    # The reason for this is that if we try to create a netbox by POSTing, it
    # will try to create a new room aswell (giving an existing roomid will make
    # it complain about already existing rooms). Not giving a room is impossible
    # as it is required.
    #
    # Thus we need a PrimaryKeyRelatedField where the source defines the key
    # that we use to find the related room when creating a new netbox

    roomid = serializers.PrimaryKeyRelatedField(
        source='room', write_only=True, queryset=manage.Room.objects.all())
    room = RoomSerializer(required=False)

    organizationid = serializers.PrimaryKeyRelatedField(
        source='organization', write_only=True, queryset=manage.Organization.objects.all())
    organization = OrganizationSerializer(required=False)

    categoryid = serializers.PrimaryKeyRelatedField(
        source='category', write_only=True, queryset=manage.Category.objects.all())
    category = CategorySerializer(required=False)

    masterid = serializers.PrimaryKeyRelatedField(source='master',
                                                  required=False,
                                                  write_only=True,
                                                  queryset=manage.Netbox.objects.all()
                                                  )
    master = SubNetboxSerializer(required=False)

    typeid = serializers.PrimaryKeyRelatedField(source='type', required=False,
                                                write_only=True,
                                                queryset=manage.NetboxType.objects.all())
    type = NetboxTypeSerializer(read_only=True)


    class Meta(object):
        model = manage.Netbox
        depth = 1
        fields = '__all__'


class PatchSerializer(serializers.ModelSerializer):
    """Serializer for the patch model"""
    class Meta(object):
        model = cabling.Patch
        depth = 2
        fields = '__all__'


class SpecificPatchSerializer(serializers.ModelSerializer):
    """Specific serializer used for InterfaceSerializer"""
    class Meta(object):
        model = cabling.Patch
        depth = 1
        fields = ('id', 'cabling', 'split')


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for the module model"""
    object_url = serializers.CharField(source='get_absolute_url')

    class Meta(object):
        model = manage.Module
        fields = '__all__'


class CamSerializer(serializers.ModelSerializer):
    """Serializer for the cam model"""
    class Meta(object):
        model = manage.Cam
        fields = '__all__'


class ArpSerializer(serializers.ModelSerializer):
    """Serializer for the arp model"""
    class Meta(object):
        model = manage.Arp
        fields = '__all__'


class SubInterfaceSerializer(serializers.ModelSerializer):
    object_url = serializers.CharField(source='get_absolute_url')
    class Meta(object):
        model = manage.Interface
        fields = '__all__'


class InterfaceSerializer(serializers.ModelSerializer):
    """Serializer for the interface model"""
    patches = SpecificPatchSerializer()
    module = ModuleSerializer()
    object_url = serializers.CharField(source='get_absolute_url')
    to_netbox = SubNetboxSerializer()
    to_interface = SubInterfaceSerializer()

    class Meta(object):
        model = manage.Interface
        depth = 1
        fields = '__all__'


class InterfaceWithCamSerializer(InterfaceSerializer):
    last_used = CamSerializer(source='get_last_cam_record')
    class Meta(object):
        fields = '__all__'


class CablingSerializer(serializers.ModelSerializer):
    """Serializer for the cabling model"""
    class Meta(object):
        model = cabling.Cabling
        fields = '__all__'


class UnrecognizedNeighborSerializer(serializers.ModelSerializer):
    """Serializer for the arp model"""
    class Meta(object):
        model = manage.UnrecognizedNeighbor
        fields = '__all__'


class RackItemSerializer(serializers.Serializer):
    """Serialize a rack item manually - no models available"""
    id = serializers.ReadOnlyField()
    title = serializers.ReadOnlyField()
    metric = serializers.ReadOnlyField(source='get_metric')
    unit_of_measurement = serializers.ReadOnlyField()
    human_readable = serializers.ReadOnlyField()
    absolute_url = serializers.ReadOnlyField(source='get_absolute_url')
    display_range = serializers.ReadOnlyField(source='get_display_range')

    class Meta(object):
        fields = '__all__'


class RackConfigurationField(serializers.ReadOnlyField):
    """Field representing the configuration of a rack"""
    def to_representation(self, value):
        configuration = {}
        for column in ['left', 'center', 'right']:
            configuration[column] = [RackItemSerializer(i).data
                                     for i in value[column]]
        return configuration


class RackSerializer(serializers.ModelSerializer):
    """Serializer for the rack model"""
    configuration = RackConfigurationField()

    class Meta(object):
        model = rack.Rack
        exclude = ('_configuration',)


class VlanSerializer(serializers.ModelSerializer):
    """Serializer for the vlan model"""
    class Meta(object):
        model = manage.Vlan
        fields = '__all__'


class PrefixSerializer(serializers.ModelSerializer):
    """Serializer for prefix model"""
    class Meta(object):
        model = manage.Prefix
        fields = '__all__'


class PrefixUsageSerializer(serializers.Serializer):
    """Serializer for prefix usage queries"""
    starttime = serializers.DateTimeField()
    endtime = serializers.DateTimeField()
    prefix = serializers.CharField()
    usage = serializers.FloatField()
    active_addresses = serializers.IntegerField()
    max_addresses = serializers.IntegerField()
    max_hosts = serializers.IntegerField()
    vlan_id = serializers.IntegerField()
    net_ident = serializers.CharField()
    url_machinetracker = serializers.CharField()
    url_report = serializers.CharField()
    url_vlan = serializers.CharField()

    class Meta(object):
        fields = '__all__'


class ServiceHandlerSerializer(serializers.Serializer):
    """Serializer for service handlers.

    These handlers does not exist in the database but as python modules.

    NB: Later versions of django rest framework supports list and dict
    fields. Then we can add the args and optargs.
    """

    name = serializers.CharField()
    ipv6_support = serializers.BooleanField()
    description = serializers.CharField()

    class Meta(object):
        fields = '__all__'
