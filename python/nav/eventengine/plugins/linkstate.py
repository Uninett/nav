#
# Copyright (C) 2012 UNINETT
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
""""linkState event plugin"""

from nav.config import ConfigurationError
from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate
from nav.models.manage import Interface, Netbox


class LinkStateHandler(delayedstate.DelayedStateHandler):
    """Accepts linkState events"""
    HAS_WARNING_ALERT = False
    ALERT_WAIT_TIME = 'linkDown.alert'
    handled_types = ('linkState',)

    __waiting_for_resolve = {}
    _target = None

    def __init__(self, *args, **kwargs):
        super(LinkStateHandler, self).__init__(*args, **kwargs)
        self.config = LinkStateConfiguration(self.engine.config)

    def get_target(self):
        if not self._target:
            self._target = Interface.objects.get(id=self.event.subid)
            assert self._target.netbox_id == self.event.netbox.id
        return self._target

    def get_link_partner(self):
        """Returns the link partner of the target interface"""
        return self.get_target().to_netbox

    def _set_internal_state_down(self):
        self._set_ifoperstatus(Interface.OPER_DOWN)

    def _set_internal_state_up(self):
        self._set_ifoperstatus(Interface.OPER_UP)

    def _set_ifoperstatus(self, ifoperstatus):
        ifc = self.get_target()
        if ifc.ifoperstatus != ifoperstatus:
            ifc.ifoperstatus = ifoperstatus
            Interface.objects.filter(id=ifc.id).update(
                ifoperstatus=ifoperstatus)

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "linkUp"
        self._logger.info("Posting %s alert for %s", alert.alert_type,
                          self.get_target())
        return alert

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "linkDown"

        if any((self._hold_back_alert_due_to_vlan_mismatch(),
                self._hold_back_alert_due_to_redundancy_limit())):
            self._logger.info("%s: withholding %s alert because of unmatched "
                              "criteria", self.get_target(), alert.alert_type)
            return None

        return alert

    def _post_down_warning(self):
        pass

    def _hold_back_alert_due_to_redundancy_limit(self):
        if self.config.alert_only_on_redundancy_loss():
            partner = self.get_link_partner()
            redundancy_loss = partner and partner.up == Netbox.UP_UP
            if redundancy_loss:
                self._logger.info("likely link redundancy degradation: %s is "
                                  "down, but link partner %s is still up",
                                  self.get_target(), partner)
            else:
                return True
        return False

    def _hold_back_alert_due_to_vlan_mismatch(self):
        limited_to_vlans = self.config.get_vlan_limit_set()
        if limited_to_vlans:
            vlans = self._get_target_vlans()
            if vlans.intersection(limited_to_vlans):
                self._logger.info("%s vlans %r intersects with list of "
                                  "limited vlans %r",
                                   self.get_target(), vlans, limited_to_vlans)
            elif vlans:
                self._logger.info("%s vlans %r does not intersect with list "
                                  "of limited vlans %r",
                                   self.get_target(), vlans, limited_to_vlans)
                return True
        return False

    def _get_target_vlans(self):
        """Returns the set of untagged/tagged vlans configured on the target
        interface.

        """
        ifc = self.get_target()
        vlans = ifc.swportvlan_set.values('vlan__vlan')
        vlans = set([row['vlan__vlan'] for row in vlans])
        return vlans


class LinkStateConfiguration(object):
    """Retrieves configuration options for the LinkStateHandler"""
    def __init__(self, config):
        self.config = config

    def get_vlan_limit_set(self):
        """Returns a set of VLAN IDs to limit linkState alerts to"""
        opt = ("linkdown", "limit_to_vlans")
        if self.config.has_option(*opt):
            vlanstring = self.config.get(*opt)
            try:
                vlans = [int(vlan) for vlan in vlanstring.split()]
            except (TypeError, ValueError):
                raise ConfigurationError("Invalid config value for %s" % opt)
            return set(vlans)
        else:
            return set()

    def alert_only_on_redundancy_loss(self):
        """Returns True if linkState alerts are only to be sent on linkDown's
         that degrade a redundant link setup

        """
        opt = ("linkdown", "only_redundant")
        if self.config.has_option(*opt):
            return self.config.getboolean(*opt)
        else:
            return True
