#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import

import os
import sys
import logging
from optparse import OptionParser
from nav import buildconf

from nav.models.manage import Netbox, Interface, Sensor
from nav.models.thresholds import ThresholdRule
from nav.models.event import EventQueue as Event
#from nav.models.event import AlertHistory

from nav.metrics.lookup import lookup

from django.db.transaction import commit_on_success

LOGFILE_NAME = 'thresholdmon.log'
LOGFILE_PATH = os.path.join(buildconf.localstatedir, 'log', LOGFILE_NAME)

_logger = logging.getLogger('nav.thresholdmon')


def main():
    parser = make_option_parser()
    (options, _args) = parser.parse_args()

    init_logging()
    scan()


def make_option_parser():
    """Sets up and returns a command line option parser."""
    parser = OptionParser(
        version="NAV " + buildconf.VERSION,
        description=("Scans metric values for exceeded thresholds, according"
                     "to configured threhold rules.")
    )
    return parser


def init_logging():
    """Initializes logging for this program"""
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s %(name)s] %(message)s")
    handler = logging.FileHandler(LOGFILE_PATH, 'a')
    handler.setFormatter(formatter)

    root = logging.getLogger('')
    root.addHandler(handler)

    if sys.stdout.isatty():
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        root.addHandler(stdout_handler)

    import nav.logs
    nav.logs.set_log_levels()


def scan():
    """Scans for threshold rules and evaluates them"""
    rules = ThresholdRule.objects.all()
    _logger.info("evaluating %d rules", len(rules))
    for rule in rules:
        _logger.debug("evaluating rule %r", rule)

        evaluator = rule.get_evaluator()
        if not evaluator.get_values():
            _logger.warning("did not find any values for this rule")
        new_exceeded = evaluator.evaluate(rule.alert)
        for metric, value in new_exceeded:
            _logger.debug("%s %s (=%s)", metric, rule.alert, value)
            # TODO: verify there isn't already an unresolved threshold alert for this
            start_event(rule, evaluator, metric, value)


def start_event(rule, evaluator, metric, value):
    return make_event(True, rule, evaluator, metric, value)


def end_event(rule, evaluator, metric, value):
    return make_event(False, rule, evaluator, metric, value)


@commit_on_success
def make_event(start, rule, evaluator, metric, value):
    event = _event_template()
    event.state = event.STATE_START if start else event.STATE_END
    event.subid = "{rule}:{metric}".format(rule=rule.id, metric=metric)

    varmap = dict(metric=metric, alert=rule.alert, clear=rule.clear,
                  ruleid=str(rule.id), value=str(value))
    obj = lookup(metric)
    if obj:
        varmap['subject'] = "{table}:{pk}".format(
            table=getattr(obj, '_meta').db_table,
            pk=obj.pk)

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
            pass

        if isinstance(obj, Interface):
            varmap['interface'] = obj.ifname
        elif isinstance(obj, Sensor):
            varmap['sensor'] = obj.name

    event.save()
    if varmap:
        event.varmap = varmap


def _event_template():
    event = Event()
    event.source_id = 'thresholdMon'
    event.target_id = 'eventEngine'
    event.event_type_id = 'thresholdState'
    return event

if __name__ == '__main__':
    main()
