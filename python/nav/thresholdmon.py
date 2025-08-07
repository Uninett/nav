#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Threshold monitoring program"""

import logging
from optparse import OptionParser
from collections import defaultdict

import django
from django.db import transaction

from nav import buildconf
from nav.logs import init_generic_logging
from nav.models.fields import INFINITY
from nav.models.manage import Netbox, Interface, Sensor
from nav.models.thresholds import ThresholdRule
from nav.models.event import EventQueue as Event, AlertHistory
from nav.metrics.lookup import lookup

LOG_FILE = 'thresholdmon.log'

_logger = logging.getLogger('nav.thresholdmon')


def main():
    """Main thresholdmon program"""
    parser = make_option_parser()
    (_options, _args) = parser.parse_args()

    init_generic_logging(
        logfile=LOG_FILE,
        stderr=False,
        stdout=True,
        read_config=True,
    )
    django.setup()
    scan()


def make_option_parser():
    """Sets up and returns a command line option parser."""
    parser = OptionParser(
        version="NAV " + buildconf.VERSION,
        description=(
            "Scans metric values for exceeded thresholds, according"
            "to configured threshold rules."
        ),
    )
    return parser


def scan():
    """Scans for threshold rules and evaluates them"""
    rules = ThresholdRule.objects.all()
    alerts = get_unresolved_threshold_alerts()

    _logger.info("evaluating %d rules", len(rules))
    for rule in rules:
        evaluate_rule(rule, alerts)
    _logger.info("done")


def evaluate_rule(rule, alerts):
    """
    Evaluates the current status of a single rule and posts events if
    necessary.
    """
    _logger.debug("evaluating rule %r", rule)

    evaluator = rule.get_evaluator()
    try:
        if not evaluator.get_values():
            _logger.warning(
                "did not find any matching values for rule %r %s",
                rule.target,
                rule.alert,
            )
    except Exception:  # noqa: BLE001
        _logger.exception("Unhandled exception while getting values for rule: %r", rule)
        return

    # post new exceed events
    try:
        exceeded = evaluator.evaluate(rule.alert)
    except Exception:  # noqa: BLE001
        _logger.exception("Unhandled exception while evaluating rule alert: %r", rule)
        return

    for metric, value in exceeded:
        alert = alerts.get(rule.id, {}).get(metric, None)
        _logger.info(
            "%s: %s %s (=%s)", "old" if alert else "new", metric, rule.alert, value
        )
        if not alert:
            start_event(rule, metric, value)

    # try to clear any existing threshold alerts
    if rule.id in alerts:
        clearable = alerts[rule.id]
        try:
            if rule.clear:
                cleared = evaluator.evaluate(rule.clear)
            else:
                cleared = evaluator.evaluate(rule.alert, invert=True)
        except Exception:  # noqa: BLE001
            _logger.exception(
                "Unhandled exception while evaluating rule clear: %r", rule
            )
            return

        for metric, value in cleared:
            if metric in clearable:
                _logger.info("cleared: %s %s (=%s)", metric, rule.clear, value)
                end_event(rule, metric, value)


def get_unresolved_threshold_alerts():
    """
    Retrieves unresolved threshold alerts from the database, mapped to rules
    and metric names.
    """
    alert_map = defaultdict(dict)
    alerts = AlertHistory.objects.filter(
        event_type__id='thresholdState', end_time__gte=INFINITY
    )
    for alert in alerts:
        try:
            ruleid, metric = alert.subid.split(':', 1)
            ruleid = int(ruleid)
        except (AttributeError, ValueError):
            continue
        else:
            alert_map[ruleid][metric] = alert

    return dict(alert_map)


def start_event(rule, metric, value):
    """Makes and posts a threshold start event"""
    event = make_event(True, rule, metric, value)
    _logger.debug("posted start event: %r", event)
    return event


def end_event(rule, metric, value):
    """Makes and posts a threshold end event"""
    event = make_event(False, rule, metric, value)
    _logger.debug("posted end event: %r", event)
    return event


@transaction.atomic()
def make_event(start, rule, metric, value):
    """Makes and posts a threshold event"""
    event = _event_template()
    event.state = event.STATE_START if start else event.STATE_END
    event.subid = "{rule}:{metric}".format(rule=rule.id, metric=metric)

    varmap = dict(
        metric=metric,
        alert=rule.alert,
        ruleid=str(rule.id),
        measured_value=str(value),
    )
    if rule.clear:
        varmap['clear'] = str(rule.clear)
    if rule.description:
        varmap['description'] = rule.description
    _add_subject_details(event, metric, varmap)

    event.save()
    if varmap:
        event.varmap = varmap
    return event


def _add_subject_details(event, metric, varmap):
    obj = lookup(metric)
    if obj:
        try:
            varmap['subject'] = "{table}:{pk}".format(
                table=getattr(obj, '_meta').db_table, pk=obj.pk
            )
        except AttributeError:
            pass  # probably wasn't a Django model object, fuhgeddaboutit

        if isinstance(obj, Netbox):
            event.netbox = obj
        else:
            try:
                event.netbox = obj.netbox
            except AttributeError:
                pass

        try:
            event.device = obj.device
        except AttributeError:
            try:
                event.device = obj.netbox.device
            except AttributeError:
                pass

        if isinstance(obj, Interface):
            varmap['interface'] = obj.ifname
        elif isinstance(obj, Sensor):
            varmap['sensor'] = obj.name


def _event_template():
    event = Event()
    event.source_id = 'thresholdMon'
    event.target_id = 'eventEngine'
    event.event_type_id = 'thresholdState'
    return event


if __name__ == '__main__':
    main()
