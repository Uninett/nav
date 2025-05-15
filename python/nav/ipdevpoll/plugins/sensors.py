#
# Copyright (C) 2008-2011, 2016 Uninett AS
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
"""ipdevpoll plugin to collect sensor data.

This plugin can use any MibRetriever class that provides the get_all_sensors()
method to discover and store information about physical environmental sensors
available for readout on a device.

Which MibRetriever classes to use for each type of device is configured
in the [sensors] and [sensors:vendormibs] sections of ipdevpoll.conf.

"""

import importlib
import logging
import os
import re
from collections import defaultdict

from twisted.internet import defer
from twisted.internet import error

from nav.config import ConfigurationError
from nav.mibs import mibretriever
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.enterprise import ids
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.oids import get_enterprise_id

_logger = logging.getLogger(__name__)


class Sensors(Plugin):
    """Plugin to detect environmental sensors in netboxes"""

    @classmethod
    def on_plugin_load(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf

        loadmodules(ipdevpoll_conf)
        cls.mib_map = get_mib_map(ipdevpoll_conf)

    @defer.inlineCallbacks
    def handle(self):
        """Collects sensors and feed them in to persistent store."""
        mibs = yield self.mibfactory()
        self._logger.debug(
            "Discovering sensors sensors using: %r", [type(m).__name__ for m in mibs]
        )
        for mib in mibs:
            self._logger.debug("Trying %r", type(mib).__name__)
            try:
                all_sensors = yield mib.get_all_sensors()
            except (error.TimeoutError, defer.TimeoutError):
                self._logger.debug(
                    "Timed out collecting sensors from %s", mib.mib["moduleName"]
                )
                continue

            if all_sensors:
                # Store and jump out on the first MIB that give
                # any results
                self._logger.debug(
                    "Found %d sensors from %s", len(all_sensors), type(mib).__name__
                )
                self._store_sensors(all_sensors)

    @defer.inlineCallbacks
    def mibfactory(self):
        """
        Returns a list of MibRetriever instances, as configured in
        ipdevpoll.conf, to use for retrieving sensors from this netbox.

        """
        vendor_id = None

        snmpv2_mib = Snmpv2Mib(self.agent)
        sysobjectid = yield snmpv2_mib.get_sysObjectID()
        if sysobjectid:
            vendor_id = get_enterprise_id(sysobjectid)
        elif self.netbox.type:
            vendor_id = self.netbox.type.get_enterprise_id()

        classes = self.mib_map.get(vendor_id, ()) or self.mib_map.get('*', ())
        mibs = [cls(self.agent) for cls in classes]
        return mibs

    def _store_sensors(self, result):
        """Stores sensor records in the current job's container dictionary, so
        that they may be persisted to the database.

        """
        sensors = []
        for row in result:
            oid = row.get('oid', None)
            internal_name = row.get('internal_name', None)
            mib = row.get('mib', None)
            ifindex = row.get('ifindex')
            # Minimum requirement.  Uniq by netbox, internal name and mib
            if oid and internal_name and mib:
                sensor = self.containers.factory(oid, shadows.Sensor)
                sensor.netbox = self.netbox
                sensor.oid = oid
                sensor.unit_of_measurement = row.get('unit_of_measurement', None)
                sensor.precision = row.get('precision', 0)
                sensor.data_scale = row.get('scale', None)
                sensor.human_readable = row.get('description', None)
                sensor.name = row.get('name', None)
                sensor.internal_name = internal_name
                sensor.mib = mib
                sensor.display_minimum_sys = row.get('minimum', None)
                sensor.display_maximum_sys = row.get('maximum', None)
                sensor.on_message_sys = row.get('on_message')
                sensor.off_message_sys = row.get('off_message')
                sensor.on_state_sys = row.get('on_state')
                if ifindex:
                    iface = self.containers.factory(ifindex, shadows.Interface)
                    iface.netbox = self.netbox
                    iface.ifindex = ifindex
                    sensor.interface = iface
                sensors.append(sensors)
        return sensors


####################
# Helper functions #
####################


def loadmodules(config):
    """:type config: ConfigParser.ConfigParser"""
    names = _get_space_separated_list(config, 'sensors', 'loadmodules')
    names = sorted(list(_expand_module_names(names)))
    _logger.debug("importing modules: %s", names)
    for name in names:
        importlib.import_module(name)


def get_mib_map(config):
    """:type config: ConfigParser.ConfigParser"""
    candidate_classes = {
        k: v
        for k, v in mibretriever.MibRetrieverMaker.modules.items()
        if hasattr(v, 'get_all_sensors')
    }
    _logger.debug("sensor candidate classes: %r", candidate_classes)
    candidate_classes.update({cls.__name__: cls for cls in candidate_classes.values()})

    mib_map = defaultdict(list)
    for opt in config.options('sensors:vendormibs'):
        names = _get_space_separated_list(config, 'sensors:vendormibs', opt)
        enterprise = _translate_enterprise_id(opt)
        if not enterprise:
            raise ConfigurationError("Unknown enterprise value: %s", opt)

        for mib in names:
            if mib not in candidate_classes:
                raise ConfigurationError(
                    "No known MIB implementation with sensor support: %s", mib
                )
            cls = candidate_classes[mib]
            mib_map[enterprise].append(cls)

    return dict(mib_map)


def _translate_enterprise_id(name):
    if not name or name == '*':
        return name
    if name.isdigit():
        return int(name)

    for lookup in (name.upper(), 'VENDOR_ID_' + name.upper()):
        if hasattr(ids, lookup):
            return getattr(ids, lookup)


def _expand_module_names(names):
    for name in names:
        items = name.split('.')
        if items[-1] == '*':
            for subname in _find_submodules('.'.join(items[:-1])):
                yield subname
        else:
            yield name


def _find_submodules(name):
    package = importlib.import_module(name)
    directory = os.path.dirname(package.__file__)
    pyfiles = (
        n
        for n in os.listdir(directory)
        if (n.endswith('.py') or n.endswith('.pyc')) and n[0] not in '_.'
    )
    names = (os.path.splitext(n)[0] for n in pyfiles)
    return ["{}.{}".format(name, n) for n in names]


def _get_space_separated_list(config, section, option):
    raw_string = config.get(section, option, fallback='').strip()
    items = re.split(r"\s+", raw_string)
    return [item for item in items if item]
