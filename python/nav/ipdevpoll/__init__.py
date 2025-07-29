#
# Copyright (C) 2008-2012 Uninett AS
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
"""NAV subsystem for IP device polling.

Packages:

  plugins -- polling plugin system

"""

from nav.models import manage
from nav.ipdevpoll.config import IpdevpollConfig
from .log import ContextLogger, ContextFormatter

__all__ = ["ContextFormatter", "IpdevpollConfig", "Plugin"]


class Plugin(object):
    """Abstract class providing common functionality for all polling plugins.

    Do *NOT* create instances of the base class.

    """

    _logger = ContextLogger()
    RESTRICT_TO_VENDORS = []

    def __init__(self, netbox, agent, containers, config: IpdevpollConfig = None):
        """

        :type netbox: nav.ipdevpoll.shadows.Netbox
        :type agent: nav.ipdevpoll.snmp.AgentProxy
        :type containers: nav.ipdevpoll.storage.ContainerRepository
        :type config: configparser.ConfigParser
        """
        self.netbox = netbox
        self.agent = agent
        self.containers = containers
        self.config = config
        # touch _logger to initialize logging context right away
        self._logger

    def __str__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox.sysname))

    def __repr__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox))

    def handle(self):
        """Handle plugin business, return a deferred."""
        raise NotImplementedError

    @classmethod
    def can_handle(cls, netbox):
        """Verifies whether this plugin can/wants to handle polling for this
        netbox instance at this time.

        The base implementation returns True as long as the Netbox' SNMP agent
        is not known to be down and it has a configured SNMP community;
        plugins must override this method if their requirements are different.

        :returns: A boolean value.
        """
        snmp_up = getattr(netbox, 'snmp_up', True)

        basic_req = netbox.is_up() and snmp_up and bool(netbox.snmp_parameters)
        vendor_check = cls._verify_vendor_restriction(netbox)
        return basic_req and vendor_check

    @classmethod
    def _verify_vendor_restriction(cls, netbox):
        if cls.RESTRICT_TO_VENDORS:
            return (
                netbox.type
                and netbox.type.get_enterprise_id() in cls.RESTRICT_TO_VENDORS
            )
        else:
            return True

    @classmethod
    def on_plugin_load(cls):
        """Called as the plugin class is loaded in the plugin registry.

        Can be used to perform any kind of initialization task that
        doesn't fit into module-level initialization.

        """
        pass

    def name(self):
        """Return the class name of this instance."""
        return self.__class__.__name__

    def full_name(self):
        """Return the full module and class name of this instance."""
        return "%s.%s" % (self.__class__.__module__, self.__class__.__name__)

    def _get_netbox_list(self):
        """Returns a list of netbox names to make metrics for. Will return just
        the one netbox in most instances, but for situations with multiple
        virtual device contexts, all the subdevices will be returned.

        """
        netboxes = [self.netbox.sysname]
        instances = manage.Netbox.objects.filter(master=self.netbox.id).values_list(
            'sysname', flat=True
        )
        netboxes.extend(instances)
        self._logger.debug("duplicating metrics for these netboxes: %s", netboxes)
        return netboxes
