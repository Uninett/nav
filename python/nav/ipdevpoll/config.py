# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Uninett AS
# Copyright (C) 2020 Universitetet i Oslo
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
"""ipdevpoll configuration management"""

import logging

from nav.config import ConfigurationError, NAVConfigParser
from nav.util import parse_interval

_logger = logging.getLogger(__name__)
JOB_PREFIX = 'job_'


class IpdevpollConfig(NAVConfigParser):
    """ipdevpoll config parser"""

    DEFAULT_CONFIG_FILES = ('ipdevpoll.conf',)
    DEFAULT_CONFIG = """
[ipdevpoll]
logfile = ipdevpolld.log
max_concurrent_jobs = 500

[netbox_filters]
groups_included=
groups_excluded=

[snmp]
timeout = 1.5
max-repetitions = 10

[multiprocess]
ping_workers = true
ping_interval = 30
ping_timeout = 10

[plugins]

[jobs]

[prefix]
ignored = <<=127.0.0.0/8, <<=fe80::/16, =128.0.0.0/2

[linkstate]
filter = topology

[bgp]
alert_ibgp = yes

[interfaces]
always_use_ifhighspeed = false

[sensors]
loadmodules = nav.mibs.*

[sensors:vendormibs]
* = ENTITY-SENSOR-MIB UPS-MIB
CISCOSYSTEMS = ENTITY-SENSOR-MIB CISCO-ENTITY-SENSOR-MIB CISCO-ENVMON-MIB
HEWLETT_PACKARD = ENTITY-SENSOR-MIB
AMERICAN_POWER_CONVERSION_CORP = PowerNet-MIB
EMERSON_COMPUTER_POWER = UPS-MIB
EATON_CORPORATION = XUPS-MIB
MERLIN_GERIN = MG-SNMP-UPS-MIB
IT_WATCHDOGS_INC = IT-WATCHDOGS-MIB-V3 IT-WATCHDOGS-MIB ItWatchDogsMibV4
GEIST_MANUFACTURING_INC = GEIST-MIB-V3 GeistMibV4
COMET_SYSTEM_SRO = P8652-MIB COMETMS-MIB T3611-MIB
KCP_INC = SPAGENT-MIB
ELTEK_ENERGY_AS = ELTEK-DISTRIBUTED-MIB
EATON_WILLIAMS = CD6C
RARITAN_COMPUTER_INC = PDU2-MIB
IBM = IBM-PDU-MIB
RITTAL_WERK_RUDOLF_LOH_GMBH_COKG = RITTAL-CMC-III-MIB
JUNIPER_NETWORKS_INC = ENTITY-SENSOR-MIB JUNIPER-DOM-MIB JUNIPER-MIB
SUPERIOR_POWER_SOLUTIONS_HK_COLTD = Pwt3PhaseV1Mib
ALCATEL_LUCENT_ENTERPRISE_FORMERLY_ALCATEL = ALCATEL-IND1-PORT-MIB
COMPAQ = CPQPOWER-MIB
CORIANT_RD_GMBH = CORIANT-GROOVE-MIB
"""


def get_job_descriptions(config=None):
    """Builds a dict of all job descriptions"""
    return {d.name.replace(JOB_PREFIX, ''): d.description for d in get_jobs(config)}


def get_jobs(config=None):
    """Returns a list of JobDescriptors for each of the jobs configured in
    ipdevpoll.conf

    """
    if config is None:
        config = ipdevpoll_conf

    job_sections = get_job_sections(config)
    job_descriptors = [
        JobDescriptor.from_config_section(config, section) for section in job_sections
    ]
    _logger.debug("parsed jobs from config file: %r", [j.name for j in job_descriptors])
    return job_descriptors


def get_job_sections(config):
    """Find all job sections in a config file"""
    return [s for s in config.sections() if s.startswith(JOB_PREFIX)]


def get_netbox_filter(section, config=None):
    """Get the requested netbox filter as list"""
    if config is None:
        config = ipdevpoll_conf

    netbox_filters = ipdevpoll_conf.get('netbox_filters', section)

    if netbox_filters:
        return netbox_filters.split()
    return []


class JobDescriptor(object):
    """A data structure describing a job."""

    def __init__(self, name, interval, intensity, plugins, description=''):
        self.name = str(name)
        self.interval = int(interval)
        self.intensity = int(intensity)
        self.plugins = list(plugins)
        self.description = description

    @classmethod
    def from_config_section(cls, config, section):
        """Creates a JobDescriptor from a ConfigParser section"""
        if section.startswith(JOB_PREFIX):
            jobname = section.removeprefix(JOB_PREFIX)
        else:
            raise InvalidJobSectionName(section)

        interval = parse_interval(config.get(section, 'interval'))
        if interval < 1:
            raise ValueError(
                "Interval for job %s is too short: %s"
                % (jobname, config.get(section, 'interval'))
            )

        intensity = (
            config.getint(section, 'intensity')
            if config.has_option(section, 'intensity')
            else 0
        )

        plugins = _parse_plugins(config.get(section, 'plugins'))
        if not plugins:
            raise ValueError("Plugin list for job %s is empty" % jobname)

        description = (
            _parse_description(config.get(section, 'description'))
            if config.has_option(section, 'description')
            else ''
        )

        return cls(jobname, interval, intensity, plugins, description)


def _parse_plugins(value):
    if value:
        return value.split()

    return []


def _parse_description(descr):
    if descr:
        return descr.replace('\n', ' ').strip()


class InvalidJobSectionName(ConfigurationError):
    """Section name is invalid as a job section"""


ipdevpoll_conf = IpdevpollConfig()
