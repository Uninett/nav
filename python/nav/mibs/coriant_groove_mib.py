#
# Copyright (C) 2019 Uninett AS
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
"""A class for getting DOM values from Coriant Groove equipment"""

from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

UNIT_DECIBEL = "dB"  # This is actually not defined in Sensor
UNIT_PS = "ps"
UNIT_PS_PER_NM = "ps/nm"


def filter_port_by_adminstatus(index, _, filter_data):
    """Filters a port sensor based on admin state of said port"""
    port_index = index[:4]
    if port_index in filter_data:
        return filter_data[port_index].get("portAdminStatus") == "up"
    return True


SENSOR_GROUPS = [
    {
        "name_from": "ochOsAliasName",
        "alias_from": "ochOsServiceLabel",
        "columns": {
            "ochOsActualTxOpticalPower": {
                "unit_of_measurement": Sensor.UNIT_DBM,
                "type": "string",
                "name": "{name} TX Optical Power",
            },
            "ochOsActualFrequency": {
                "unit_of_measurement": Sensor.UNIT_HERTZ,
                "scale": Sensor.SCALE_MEGA,
                "type": "string",
                "name": "{name} actual laser frequency",
            },
            "ochOsDGD": {
                "unit_of_measurement": Sensor.UNIT_SECONDS,
                "scale": Sensor.SCALE_PICO,
                "name": "{name} differential group delay",
            },
            "ochOsCD": {
                "unit_of_measurement": UNIT_PS_PER_NM,
                "name": "{name} chromatic dispersion",
            },
            "ochOsOSNR": {
                "unit_of_measurement": UNIT_DECIBEL,
                "type": "string",
                "name": "{name} OSNR",
            },
            "ochOsQFactor": {
                "unit_of_measurement": UNIT_DECIBEL,
                "type": "string",
                "name": "{name} Q-factor",
            },
            "ochOsPreFecBer": {
                "unit_of_measurement": Sensor.UNIT_OTHER,
                "type": "string",
                "name": "{name} PreFEC bit error ratio",
            },
        },
    },
    {
        "name_from": "portName",
        "alias_from": "portServiceLabel",
        # lookup portName using the first 4 items of the oid index
        "index_translation": lambda x: x[:4],
        "filter_function": filter_port_by_adminstatus,
        "filter_columns": ["portAdminStatus"],
        "columns": {
            "inOpticalPowerInstant": {
                "unit_of_measurement": Sensor.UNIT_DBM,
                "type": "string",
                "name": "{name} RX instant optical power",
                "description": "{name} RX optical power",
            },
            "outOpticalPowerInstant": {
                "unit_of_measurement": Sensor.UNIT_DBM,
                "type": "string",
                "name": "{name} TX instant optical power",
                "description": "{name} TX optical power",
            },
        },
    },
    {
        "name_from": "portName",
        "alias_from": "portServiceLabel",
        "filter_function": filter_port_by_adminstatus,
        "filter_columns": ["portAdminStatus"],
        "columns": {
            "inOpticalPowerLaneTotalInstant": {
                "unit_of_measurement": Sensor.UNIT_DBM,
                "type": "string",
                "name": "{name} RX Lane total optical power",
                "description": "{name}{alias} total value of RX lane optical power",
            },
            "outOpticalPowerLaneTotalInstant": {
                "unit_of_measurement": Sensor.UNIT_DBM,
                "type": "string",
                "name": "{name} TX Lane total optical power",
                "description": "{name}{alias} total value of TX lane optical power",
            },
        },
    },
    {
        "name_from": "oduAliasName",
        "alias_from": "oduServiceLabel",
        "columns": {
            "oduDelayInstant": {
                "unit_of_measurement": Sensor.UNIT_SECONDS,
                "scale": Sensor.SCALE_MICRO,
                "type": "string",
                "name": "{name} odu signal delay",
                "description": "{name}{alias} ODU signal delay",
            }
        },
    },
]


class CoriantGrooveMib(MibRetriever):
    """MibRetriever for Coriant Groove DOM Sensors"""

    mib = get_mib("CORIANT-GROOVE-MIB")

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible optical channel sensors"""
        sensors = []
        for group in SENSOR_GROUPS:
            response = yield self._discover_sensors(
                group["columns"],
                group["name_from"],
                group.get("alias_from"),
                index_translator=group.get("index_translation", lambda x: x),
                filter_function=group.get("filter_function"),
                filter_columns=group.get("filter_columns"),
            )
            sensors.extend(response)
        return sensors

    @defer.inlineCallbacks
    def _discover_sensors(
        self,
        config,
        subject_names_from,
        subject_aliases_from,
        index_translator,
        filter_columns=None,
        filter_function=None,
    ):
        """Returns sensor definitions for a given set of statistics values.

        :param config: A dict of measurement columns to produce sensors from.
        :param subject_names_from: The OID object from which to get a name for the
                                   subjects referred to in the collected stats rows.
        :param subject_aliases_from: The OID object from which to get a an alias for the
                                     subjects referred to in the collected stats rows.
        :param index_translator: A function to translate column indexes into a index
                                 that can be used to look up the subject name from the
                                 subject_names_from object.
        :param filter_function: An optional function that will filter the returned
                                sensor records. If provided, only records that cause
                                this filter to return a True value will be included in
                                the result.
        :type filter_function: func(index:OID, columns:dict, filter_columns:dict)
        :param filter_columns: Extra table columns to fetch and feed as an argument to
                               the filter function.

        """
        name_map = yield self.retrieve_column(subject_names_from)
        self._logger.debug("name map %s: %r", subject_names_from, name_map)
        if subject_aliases_from:
            alias_map = yield self.retrieve_column(subject_aliases_from)
            self._logger.debug("alias map %s: %r", subject_aliases_from, alias_map)
        else:
            alias_map = {}
        filter_data = None
        if filter_columns:
            filter_data = yield self.retrieve_columns(filter_columns).addCallback(
                self.translate_result
            )

        response = yield self.retrieve_columns(list(config.keys()))
        self._logger.debug("Found columns: %r", response)

        sensors = []
        for index, columns in response.items():
            _index = index_translator(index)
            name = name_map.get(_index, str(index))
            alias = alias_map.get(_index)
            alias = " ({})".format(alias) if alias else ""
            if filter_function and not filter_function(index, columns, filter_data):
                self._logger.debug(
                    "ignoring %s based on %s", name, filter_function.__name__
                )
                continue

            sensors.extend(
                [
                    self._make_sensor(
                        index=index,
                        name=name,
                        alias=alias,
                        column=column,
                        config=config.get(column),
                    )
                    for column in config
                    if column in columns
                ]
            )
        self._logger.debug("Returning sensor list: %r", sensors)
        return sensors

    def _make_sensor(self, index, name, alias, column, config):
        value_oid = self.nodes[column].oid
        sensor = dict(
            oid=str(value_oid + index),
            scale=None,
            mib=self.get_module_name(),
            internal_name="{name}.{column}".format(name=name, column=column),
            description="{name}{alias} " + self._get_sensor_description(column),
        )
        sensor.update(config)
        sensor["name"] = sensor["name"].format(name=name)
        sensor["description"] = sensor["description"].format(name=name, alias=alias)
        return sensor

    def _get_sensor_description(self, column):
        """Returns the first line of the mib object's description"""
        mib_object = self.nodes[column].raw_mib_data
        description = mib_object.get("description", "").strip()
        return description.split("\n")[0]


def _fix_text_columns():
    """Updates CoriantGrooveMib.text_columns to include all known text columns.

    The text_columns attribute cannot be modified directly in the class definition
    because of the way the metaclass generates the text_columns attribute during the
    construction of the CoriantGrooveMib class.

    The MIB modules itself marks most of these up as OctetString, rather than
    DisplayString, causing the SNMP library to return them all as bytes objects
    rather than strings.
    """
    # TODO Find a way to let the metaclass make a union w/the class' own text_columns
    CoriantGrooveMib.text_columns.update(grp["name_from"] for grp in SENSOR_GROUPS)
    CoriantGrooveMib.text_columns.update(grp["alias_from"] for grp in SENSOR_GROUPS)
    CoriantGrooveMib.text_columns.update(
        column_name
        for group in SENSOR_GROUPS
        for column_name, column in group["columns"].items()
        if column.get("type") == "string"
    )


_fix_text_columns()
