#
# Copyright (C) 2013, 2019 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Serializers for the NAV REST api"""

from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nav.web.api.v1.fields import DisplayNameWritableField
from nav.models import manage, cabling, rack, profiles
from nav.web.seeddb.page.netbox.edit import get_sysname


class ManagementProfileSerializer(serializers.ModelSerializer):
    """Serializer for management profiles"""

    protocol = DisplayNameWritableField()

    class Meta(object):
        model = manage.ManagementProfile
        fields = "__all__"


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for accounts"""

    accountgroups = serializers.PrimaryKeyRelatedField(
        source='groups',
        many=True,
        queryset=profiles.AccountGroup.objects.all(),
    )

    class Meta(object):
        model = profiles.Account
        fields = (
            'id',
            'login',
            'name',
            'ext_sync',
            'preferences',
            'organizations',
            'accountgroups',
        )


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
        fields = (
            'id',
            'name',
            'descr',
            'serial',
            'vendor_type',
            'hardware_revision',
            'firmware_revision',
            'software_revision',
            'mfg_name',
            'model_name',
            'fru',
            'mfg_date',
        )


class NetboxTypeSerializer(serializers.ModelSerializer):
    """Serializer for the type model"""

    class Meta(object):
        model = manage.NetboxType
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
        allow_null=True,
        required=False,
        min_length=2,
        max_length=2,
    )

    class Meta(object):
        model = manage.Room
        fields = '__all__'

    def validate(self, attrs):
        """Ensures conversion of coordinate from string list to tuple of Decimals"""
        if attrs.get("position"):
            lat, lon = attrs.get("position")
            attrs["position"] = (Decimal(lat), Decimal(lon))
        return attrs


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
        source='room', write_only=True, queryset=manage.Room.objects.all()
    )
    room = RoomSerializer(required=False)

    organizationid = serializers.PrimaryKeyRelatedField(
        source='organization',
        write_only=True,
        queryset=manage.Organization.objects.all(),
    )
    organization = OrganizationSerializer(required=False)

    categoryid = serializers.PrimaryKeyRelatedField(
        source='category', write_only=True, queryset=manage.Category.objects.all()
    )
    category = CategorySerializer(required=False)

    masterid = serializers.PrimaryKeyRelatedField(
        source='master',
        required=False,
        write_only=True,
        queryset=manage.Netbox.objects.all(),
    )
    master = SubNetboxSerializer(required=False)

    typeid = serializers.PrimaryKeyRelatedField(
        source='type',
        required=False,
        write_only=True,
        queryset=manage.NetboxType.objects.all(),
    )
    type = NetboxTypeSerializer(read_only=True)

    profiles = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        write_only=False,
        queryset=manage.ManagementProfile.objects,
    )

    mac_addresses = serializers.ListField(read_only=True, required=False)

    class Meta(object):
        model = manage.Netbox
        depth = 1
        fields = '__all__'

    def validate(self, attrs):
        if attrs.get("ip") and not attrs.get("sysname"):
            attrs["sysname"] = get_sysname(attrs.get("ip")) or attrs.get("ip")
        try:
            duplicate = manage.Netbox.objects.get(sysname=attrs.get("sysname"))
        except manage.Netbox.DoesNotExist:
            pass
        else:
            if duplicate != self.instance:
                raise ValidationError(
                    "{} already exists in the database".format(attrs.get("sysname")),
                    code="unique",
                )
        return attrs

    def create(self, validated_data):
        profile_list = validated_data.pop("profiles", None)
        netbox = manage.Netbox.objects.create(**validated_data)
        self._update_profiles(netbox, profile_list)
        return netbox

    def update(self, instance, validated_data):
        profile_list = validated_data.pop("profiles", None)
        instance = super(NetboxSerializer, self).update(instance, validated_data)
        self._update_profiles(instance, profile_list)
        return instance

    @staticmethod
    def _update_profiles(instance, profile_list):
        if profile_list is None:
            return

        profile_set = set(profile_list)
        old_profiles = set(instance.profiles.all())
        to_add = profile_set.difference(old_profiles)
        to_remove = old_profiles.difference(profile_set)
        for profile in to_remove:
            manage.NetboxProfile.objects.get(netbox=instance, profile=profile).delete()
        for profile in to_add:
            manage.NetboxProfile(netbox=instance, profile=profile).save()


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


class NetboxInlineSerializer(serializers.ModelSerializer):
    """Serializer for including netbox information in other serializers"""

    class Meta(object):
        model = manage.Netbox
        fields = ('id', 'sysname')


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for the device model"""

    class Meta(object):
        model = manage.Device
        fields = '__all__'


class DeviceInlineSerializer(serializers.ModelSerializer):
    """Serializer for the device model"""

    class Meta(object):
        model = manage.Device
        fields = ('id', 'serial')


class ModuleInlineSerializer(serializers.ModelSerializer):
    """Serializer for including module information in other serializers"""

    object_url = serializers.CharField(source='get_absolute_url')

    class Meta(object):
        model = manage.Module
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for the module model"""

    object_url = serializers.CharField(source='get_absolute_url')
    device = DeviceSerializer()
    netbox = NetboxInlineSerializer()

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


class AggregatedInterfaceSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = manage.Interface
        fields = ['id', 'ifname']


class InterfaceSerializer(serializers.ModelSerializer):
    """Serializer for the interface model"""

    patches = SpecificPatchSerializer()
    module = ModuleInlineSerializer()
    object_url = serializers.CharField(source='get_absolute_url')
    to_netbox = SubNetboxSerializer()
    to_interface = SubInterfaceSerializer()
    aggregator = AggregatedInterfaceSerializer(source='get_aggregator')
    bundled_interfaces = AggregatedInterfaceSerializer(
        source='get_bundled_interfaces', many=True
    )
    netbox = SubNetboxSerializer()
    vlan_netident = serializers.CharField(read_only=True)

    class Meta(object):
        model = manage.Interface
        depth = 1
        fields = '__all__'


class InterfaceWithCamSerializer(InterfaceSerializer):
    last_used = CamSerializer(source='get_last_cam_record')

    class Meta(object):
        model = manage.Interface
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
    display_configuration = serializers.ReadOnlyField(
        source='get_display_configuration'
    )

    class Meta(object):
        fields = '__all__'


class RackConfigurationField(serializers.ReadOnlyField):
    """Field representing the configuration of a rack"""

    def to_representation(self, value):
        configuration = {}
        for column in ['left', 'center', 'right']:
            configuration[column] = [RackItemSerializer(i).data for i in value[column]]
        return configuration


class RackSerializer(serializers.ModelSerializer):
    """Serializer for the rack model"""

    configuration = RackConfigurationField()

    class Meta(object):
        model = rack.Rack
        exclude = ('_configuration',)


class VlanSerializer(serializers.ModelSerializer):
    """Serializer for the vlan model"""

    VALID_NET_TYPES = ["scope", "reserved"]

    class Meta(object):
        model = manage.Vlan
        fields = '__all__'

    def validate_net_type(self, value):
        """Validate net_type

        :type value: nav.models.manage.NetType
        """
        if value.id not in VlanSerializer.VALID_NET_TYPES:
            raise serializers.ValidationError(
                "net_type must be {}".format(
                    ' or '.join(VlanSerializer.VALID_NET_TYPES)
                )
            )
        return value


class PrefixSerializer(serializers.ModelSerializer):
    """Serializer for prefix model"""

    usages = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, required=False, queryset=manage.Usage.objects.all()
    )
    vlan_data = VlanSerializer(read_only=True, source='vlan')

    class Meta(object):
        model = manage.Prefix
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'usages' in validated_data:
            new_usages = set(u.id for u in validated_data.pop('usages'))
            current_usages = set(u.id for u in instance.usages.all())
            to_add = new_usages - current_usages
            to_delete = current_usages - new_usages

            for usage in to_add:
                manage.PrefixUsage(
                    prefix=instance, usage=manage.Usage.objects.get(pk=usage)
                ).save()

            manage.PrefixUsage.objects.filter(
                prefix=instance, usage__in=list(to_delete)
            ).delete()
        return super(PrefixSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        usages = validated_data.pop('usages', [])
        instance = super(PrefixSerializer, self).create(validated_data)
        for usage in usages:
            manage.PrefixUsage(prefix=instance, usage=usage).save()

        return instance


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


class NetboxEntitySerializer(serializers.ModelSerializer):
    """Serializer for the NetboxEntity model"""

    device = DeviceInlineSerializer()
    physical_class_name = serializers.CharField(source='get_physical_class_display')

    class Meta(object):
        model = manage.NetboxEntity
        fields = '__all__'
