#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Alert generator functionality for the eventEngine"""

from collections import namedtuple
import logging
import os
from pprint import pformat
import re

from django.template import loader

from nav.models.event import AlertQueue as Alert, EventQueue as Event, AlertType
from nav.models.event import AlertHistory
from nav.models.fields import INFINITY

import nav.config
from . import unresolved
from . import export
from . import severity

ALERT_TEMPLATE_DIR = nav.config.find_config_file('alertmsg')
_logger = logging.getLogger(__name__)
_template_logger = logging.getLogger(__name__ + '.template')


class AlertGenerator(dict):
    severity_rules: severity.SeverityRules = None

    def __init__(self, event):
        super(AlertGenerator, self).__init__()
        self.event = event

        self.source = event.source
        self.device = event.device
        self.netbox = event.netbox
        self.subid = event.subid
        self.time = event.time
        self.event_type = event.event_type
        self.state = event.state
        self.value = event.value
        self.severity = event.severity

        self.update(event.varmap)
        self.history_vars = {}

        if 'alerttype' in self:
            self.alert_type = self['alerttype']
            del self['alerttype']
        else:
            self.alert_type = None

        self._messages = None

    def __repr__(self):
        dictrepr = super(AlertGenerator, self).__repr__()
        attribs = [
            "{0}={1!r}".format(key, value)
            for key, value in vars(self).items()
            if not key.startswith('_') and key != 'event'
        ]
        return "<AlertGenerator: {0} varmap={1}>".format(" ".join(attribs), dictrepr)

    def __bool__(self):
        """AlertGenerator inherits from dict, but must always be
        considered True

        """
        return True

    def make_alert(self):
        """Generates an alert object based on the current attributes"""
        attrs = {}
        if self.severity_rules:
            self.severity = self.severity_rules.evaluate(self)
        for attr in (
            'source',
            'device',
            'netbox',
            'subid',
            'time',
            'event_type',
            'state',
            'value',
            'severity',
        ):
            attrs[attr] = getattr(self, attr)
        alert = Alert(**attrs)
        alert.alert_type = self.get_alert_type()
        alert.varmap = self
        return alert

    def make_alert_history(self):
        """Generates an alert history object based on the current attributes"""
        if self.state == Event.STATE_END:
            return self._resolve_alert_history()

        attrs = dict(
            start_time=self.time,
            end_time=INFINITY if self.state == Event.STATE_START else None,
        )
        if self.severity_rules:
            self.severity = self.severity_rules.evaluate(self)
        for attr in (
            'source',
            'device',
            'netbox',
            'subid',
            'event_type',
            'value',
            'severity',
        ):
            attrs[attr] = getattr(self, attr)
        alert = AlertHistory(**attrs)
        alert.alert_type = self.get_alert_type()
        self._update_history_vars(alert)
        return alert

    def _resolve_alert_history(self):
        alert = self._find_existing_alert_history()
        if alert:
            alert.end_time = self.event.time
            self._update_history_vars(alert)
        return alert

    def _update_history_vars(self, alert):
        if self.history_vars:
            vars = alert.varmap
            vars[self.state] = self.history_vars
            alert.varmap = vars

    def _find_existing_alert_history(self):
        return unresolved.refers_to_unresolved_alert(self.event) or None

    def post(self, post_alert=True, set_state=True):
        """Generates and posts the necessary alert objects to the database,
        and exports the alert to an external script if configured.

        :param post_alert: If True, an AlertQueue entry is posted.

        :param set_state: If True, a new AlertHistory (state) entry is posted,
                          or an existing one is updated/resolved. If False, no
                          AlertHistory objects are created or updated. If this is an
                          actual AlertHistory instance and _post_alert is True, the
                          posted alert will reference this AlertHistory record.
        """
        if isinstance(set_state, AlertHistory):
            history = set_state
        else:
            history = self._post_alert_history() if set_state else None
        alert = self._post_alert(history) if post_alert else None
        if export.exporter:
            if not alert:
                alert = self.make_alert()
                alert.history = history
            try:
                export.exporter.export(alert)
            except Exception:  # noqa: BLE001
                # we don't want to derail everything internally if external export fails
                _logger.exception("Ignoring unhandled exception on alert export")

    def _post_alert(self, history=None):
        """Generates and posts an alert on the alert queue only"""
        _logger.debug("posting to alert queue for %r", self)
        alert = self.make_alert()
        alert.history = history
        alert.save()
        self._post_alert_messages(alert)
        return alert

    def _post_alert_history(self):
        """Generates and posts an alert history record only"""
        _logger.debug("posting to alert history for %r", self)
        history = self.make_alert_history()
        if history:
            history.save()
            self._post_alert_messages(history)
        return history

    def _post_alert_messages(self, obj):
        msg_class = obj.messages.model
        for details, text in self._make_messages():
            kwargs = {"type": details.msgtype, "language": details.language}
            if hasattr(msg_class, "alert_queue"):
                kwargs["alert_queue"] = obj
            elif hasattr(msg_class, "alert_history"):
                kwargs["alert_history"] = obj
                kwargs["state"] = self.state

            msg, _created = msg_class.objects.get_or_create(
                **kwargs,
                defaults={"message": text},
            )
            msg.save()

    def _make_messages(self):
        if self._messages is None:
            self._messages = render_templates(self)
        return self._messages

    def is_event_duplicate(self):
        """Returns True if the represented event seems to duplicate an
        existing unresolved alert.

        """
        return (
            self.event.state == Event.STATE_START
            and unresolved.refers_to_unresolved_alert(self.event)
        )

    def get_alert_type(self):
        if not self.alert_type:
            return

        try:
            return AlertType.objects.get(name=self.alert_type)
        except AlertType.DoesNotExist:
            return


###
### Alert message template processing
###

TEMPLATE_PATTERN = re.compile(
    r"^(?P<alert_type>\w+)-" r"(?P<msgtype>\w+)" r"(\.(?P<language>\w+))?" r"\.txt$"
)

DEFAULT_LANGUAGE = "en"


def ensure_alert_templates_are_available():
    """Inserts the ALERT_TEMPLATE_DIR into Django's TEMPLATE_DIRS list"""
    from django.conf import settings

    for config in settings.TEMPLATES:
        if (
            config.get('BACKEND') == 'django.template.backends.django.DjangoTemplates'
            and ALERT_TEMPLATE_DIR not in config['DIRS']
        ):
            config['DIRS'] += (ALERT_TEMPLATE_DIR,)


def render_templates(alert):
    """Renders and returns message template based on the parameters of `alert`.

    :param alert: An :py:class:AlertGenerator object representing the alert
    :return: A list of (TemplateDetails, <rendered_unicode>) tuples

    """
    ensure_alert_templates_are_available()
    templates = get_list_of_templates_for(
        alert.event_type.id, alert.alert_type
    ) or get_list_of_templates_for(alert.event_type.id)
    if not templates:
        _logger.error(
            "no templates defined for %r, sending generic alert message", alert
        )
        templates = [
            TemplateDetails("default-email.txt", "email", DEFAULT_LANGUAGE),
            TemplateDetails("default-sms.txt", "sms", DEFAULT_LANGUAGE),
        ]

    return [_render_template(template, alert) for template in templates]


def _render_template(details, alert):
    template = loader.get_template(details.name)
    context = dict(alert)
    context.update(vars(alert))
    context.update(dict(msgtype=details.msgtype, language=details.language))
    context.update(dict(context_dump=pformat(context)))

    _template_logger.debug(
        "rendering alert template with context:\n%s", context['context_dump']
    )
    output = template.render(context).strip()
    _template_logger.debug("rendered as:\n%s", output)
    return details, output


def get_list_of_templates_for(event_type, alert_type="default"):
    """Returns a list of TemplateDetails objects for the available alert
    message templates for the given event_type and alert_type.

    """

    def _matcher(name):
        match = TEMPLATE_PATTERN.search(name)
        if match and match.group('alert_type') == alert_type:
            return match

    directory = os.path.join(ALERT_TEMPLATE_DIR, event_type)
    if os.path.isdir(directory):
        matches = [
            (_matcher(name), os.path.join(event_type, name))
            for name in os.listdir(directory)
        ]
    else:
        matches = []
    return [
        TemplateDetails(
            name, match.group('msgtype'), match.group('language') or DEFAULT_LANGUAGE
        )
        for match, name in matches
        if match
    ]


TemplateDetails = namedtuple("TemplateDetails", "name msgtype language")
