#
# Copyright (C) 2013 UNINETT AS
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

from nav.models import manage
from rest_framework import serializers


class NetboxSerializer(serializers.ModelSerializer):
    """Serializer for the netbox model"""
    class Meta:
        model = manage.Netbox


class InterfaceSerializer(serializers.ModelSerializer):
    """Serializer for the interface model"""
    class Meta:
        model = manage.Interface


class CamSerializer(serializers.ModelSerializer):
    """Serializer for the cam model"""
    class Meta:
        model = manage.Cam


class ArpSerializer(serializers.ModelSerializer):
    """Serializer for the arp model"""
    class Meta:
        model = manage.Arp


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for the room model"""
    @staticmethod
    def transform_position(obj, _value):
        if obj.position:
            lat, lon = obj.position
            return str(lat), str(lon)

    class Meta:
        model = manage.Room
        fields = ('id', 'location', 'description', 'position')


class PrefixSerializer(serializers.ModelSerializer):
    """Serializer for prefix model"""
    class Meta:
        model = manage.Prefix


class PrefixUsageSerializer(serializers.Serializer):
    """Serializer for prefix usage queries"""
    starttime = serializers.DateTimeField()
    endtime = serializers.DateTimeField()
    prefix = serializers.CharField()
    usage = serializers.FloatField()
    active_addresses = serializers.IntegerField()
    max_addresses = serializers.IntegerField()
