#
# Copyright (C) 2015 Uninett AS
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
"""Serializers for status API data"""

from django.core.urlresolvers import reverse
from django.template.defaultfilters import urlize
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from rest_framework import serializers
from nav.models import event, profiles
from nav.models.fields import INFINITY


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Accounts that have acknowledged alerts"""

    class Meta(object):
        model = profiles.Account
        fields = ('id', 'login', 'name')


class AcknowledgementSerializer(serializers.ModelSerializer):
    """Serializer for alert acknowledgements"""
    account = AccountSerializer()

    comment_html = serializers.CharField(source='comment', read_only=True)

    @staticmethod
    def transform_comment_html(_obj, value):
        """Urlize content, but make sure other tags are stripped as we need
        to output this raw"""
        try:
            return urlize(strip_tags(value))
        except TypeError:
            return ''

    class Meta(object):
        model = event.Acknowledgement
        fields = ('account', 'comment', 'date', 'comment_html')


class AlertTypeSerializer(serializers.ModelSerializer):
    """Serializer for alert types"""
    class Meta(object):
        model = event.AlertType
        fields = ('name', 'description')


class EventTypeSerializer(serializers.ModelSerializer):
    """Serializer for event types"""
    class Meta(object):
        model = event.EventType
        fields = ('id', 'description')


class AlertHistorySerializer(serializers.ModelSerializer):
    """Serializer for the AlertHistory model"""
    subject = serializers.SerializerMethodField(source='get_subject')
    subject_url = serializers.SerializerMethodField()
    subject_type = serializers.SerializerMethodField()

    on_maintenance = serializers.SerializerMethodField('is_on_maintenance')
    acknowledgement = AcknowledgementSerializer()

    event_history_url = serializers.SerializerMethodField()
    netbox_history_url = serializers.SerializerMethodField()
    event_details_url = serializers.SerializerMethodField()
    device_groups = serializers.SerializerMethodField()

    alert_type = AlertTypeSerializer()
    event_type = EventTypeSerializer()
    start_time = serializers.DateTimeField()
    end_time = serializers.SerializerMethodField()


    @staticmethod
    def get_subject(obj):
        """Return textual description of object"""
        return force_text(obj.get_subject())

    @staticmethod
    def get_subject_url(obj):
        """Returns an absolute URL for the subject, or None if not applicable"""
        try:
            return obj.get_subject().get_absolute_url()
        except AttributeError:
            try:
                return obj.get_subject().netbox.get_absolute_url()
            except AttributeError:
                return None

    @staticmethod
    def is_on_maintenance(obj):
        """Returns True if alert subject is on maintenance"""
        try:
            return obj.get_subject().is_on_maintenance()
        except AttributeError:
            try:
                # attempt fallback to owning netbox, if any
                return obj.get_subject().netbox.is_on_maintenance()
            except AttributeError:
                pass

    @staticmethod
    def get_event_history_url(obj):
        """Returns a device history URL for this type of event"""
        return "".join([reverse('devicehistory-view'), '?eventtype=', 'e_',
                        obj.event_type.id])

    @staticmethod
    def get_netbox_history_url(obj):
        """Returns a device history URL for this subject, if it is a Netbox"""
        if AlertHistorySerializer.get_subject_type(obj) == 'Netbox':
            return reverse('devicehistory-view-netbox',
                           kwargs={'netbox_id': obj.get_subject().id})

    @staticmethod
    def get_event_details_url(obj):
        """Returns the url to the details page for this event"""
        return reverse('event-details', kwargs={'event_id': obj.pk})

    @staticmethod
    def get_subject_type(obj):
        """Returns the class name of the subject"""
        return obj.get_subject().__class__.__name__

    @staticmethod
    def get_end_time(obj):
        """
        Returns the alert endtime, complete with translation of 'infinite'
        values to the string 'infinity'
        """
        return obj.end_time if obj.end_time != INFINITY else "infinity"

    @staticmethod
    def get_device_groups(obj):
        """Returns all the device groups for the netbox if any"""
        try:
            netbox = obj.netbox
            return netbox.groups.values_list('id', flat=True)
        except:
            pass

    class Meta(object):
        model = event.AlertHistory
        fields = '__all__'
