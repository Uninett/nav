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
"""Serializers for the NAV REST api"""

from nav.models.manage import Room, Netbox
from rest_framework import serializers


class NetboxSerializer(serializers.ModelSerializer):
    """Serializer for the netbox model"""
    class Meta:
        model = Netbox


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for the room model"""
    class Meta:
        model = Room
        fields = ('id', 'location', 'description', 'position')



