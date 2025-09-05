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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"common AgentProxy mixin"

import time
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Optional

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.task import deferLater

from nav.Snmp.defines import SecurityLevel, AuthenticationProtocol, PrivacyProtocol
from nav.models.manage import Netbox

_logger = logging.getLogger(__name__)


def cache_for_session(func):
    """Decorator for AgentProxyMixIn.getTable to cache responses"""

    def _wrapper(*args, **kwargs):
        self, oids = args[0], args[1]
        cache = getattr(self, '_result_cache')
        key = tuple(oids)
        if key not in cache:
            df = func(*args, **kwargs)
            if df:
                df.addCallback(_cache_result, cache, key)
            return df
        else:
            return succeed(cache[key])

    return wraps(func)(_wrapper)


def _cache_result(result, cache, key):
    cache[key] = result
    return result


def throttled(func):
    """Decorator for AgentProxyMixIn.getTable to throttle requests"""

    def _wrapper(*args, **kwargs):
        self = args[0]
        last_request = getattr(self, '_last_request')
        delay = (last_request + self.throttle_delay) - time.time()
        setattr(self, '_last_request', time.time())

        if delay > 0:
            _logger.debug("%sss delay due to throttling: %r", delay, self)
            return deferLater(reactor, delay, func, *args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wraps(func)(_wrapper)


class AgentProxyMixIn(object):
    """Common AgentProxy mix-in class.

    This mix-in provides some common base functionality for ipdevpoll
    AgentProxies, whether they be derived from the twistedsnmp or the pynetsmp
    library.  The former uses old-style classes, while the latter new-style
    classes, which makes weird things happen when we want super() to work
    properly.

    """

    def __init__(self, *args, **kwargs):
        """Initializes an agent proxy.

        :params snmp_parameters: An SNMPParameters namedtuple.

        """
        if 'snmp_parameters' in kwargs:
            self.snmp_parameters = kwargs['snmp_parameters']
            del kwargs['snmp_parameters']
        else:
            self.snmp_parameters = SNMPParameters()
        self._result_cache = {}
        self._last_request = 0
        self.throttle_delay = self.snmp_parameters.throttle_delay

        kwargs_out = self.snmp_parameters.as_agentproxy_args()
        kwargs_out.update(kwargs)
        super(AgentProxyMixIn, self).__init__(*args, **kwargs_out)
        # If we're mixed in with a pure twistedsnmp AgentProxy, the timeout
        # parameter will have no effect, since it is an argument to individual
        # method calls.
        self.timeout = self.snmp_parameters.timeout

    def __repr__(self):
        return "<{module}.{klass}({ip}, ...) at {ident}>".format(
            module=self.__class__.__module__,
            klass=self.__class__.__name__,
            ip=repr(self.ip),
            ident=id(self),
        )

    @cache_for_session
    def getTable(self, *args, **kwargs):
        kwargs['maxRepetitions'] = self.snmp_parameters.max_repetitions
        return super(AgentProxyMixIn, self).getTable(*args, **kwargs)

    @throttled
    def _get(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._get(*args, **kwargs)

    @throttled
    def _walk(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._walk(*args, **kwargs)

    @throttled
    def _getbulk(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._getbulk(*args, **kwargs)


@dataclass
class SNMPParameters:
    """SNMP session parameters common to all SNMP protocol versions"""

    # Constants, no annotations
    DEFAULT_TIMEOUT = 1.5

    # Common for all SNMP sessions
    version: int = 1
    timeout: float = DEFAULT_TIMEOUT
    tries: int = 3

    # Common for v1 and v2 only
    community: str = "public"

    # Common for v2c +
    max_repetitions: int = 50

    # SNMPv3 only
    sec_level: Optional[SecurityLevel] = None
    auth_protocol: Optional[AuthenticationProtocol] = None
    sec_name: str = None
    auth_password: Optional[str] = None
    priv_protocol: Optional[PrivacyProtocol] = None
    priv_password: Optional[str] = None

    # Specific to ipdevpoll-derived implementations
    throttle_delay: int = 0

    def __post_init__(self):
        """Enforces Enum types on init"""
        if self.sec_level and not isinstance(self.sec_level, SecurityLevel):
            self.sec_level = SecurityLevel(self.sec_level)
        if self.auth_protocol and not isinstance(
            self.auth_protocol, AuthenticationProtocol
        ):
            self.auth_protocol = AuthenticationProtocol(self.auth_protocol)
        if self.priv_protocol and not isinstance(self.priv_protocol, PrivacyProtocol):
            self.priv_protocol = PrivacyProtocol(self.priv_protocol)

    @property
    def version_string(self):
        """Returns the SNMP protocol version as a command line compatible string"""
        return "2c" if self.version == 2 else str(self.version)

    @classmethod
    def factory(
        cls, netbox: Optional[Netbox] = None, **kwargs
    ) -> Optional["SNMPParameters"]:
        """Creates and returns a set of SNMP parameters based on three sources, in
        reverse order of precedence:

        1. Given a Netbox, adds the parameters from its preferred SNMP profile.
        2. SNMP parameters from ipdevpoll.conf.
        3. SNMP parameters given as keyword arguments to the factory method.

        Beware that this method will synchronously fetch management profiles from the
        database using the Django ORM, and should not be called from async code
        unless deferred to a worker thread.

        If the netbox argument is a Netbox without a configured SNMP profile, None will
        be returned.
        """
        kwargs_out = {}
        if netbox:
            profile = netbox.get_preferred_snmp_management_profile()
            if profile:
                kwargs_out.update(
                    {k: v for k, v in profile.configuration.items() if hasattr(cls, k)}
                )
                # Let profile object parse its own version to an int
                kwargs_out["version"] = profile.snmp_version
            else:
                _logger.debug("%r has no snmp profile", netbox)
                return None

        kwargs_out.update(cls.get_params_from_ipdevpoll_config())
        kwargs_out.update(kwargs)
        return cls(**kwargs_out)

    @classmethod
    def get_params_from_ipdevpoll_config(cls, section: str = "snmp") -> dict[str, Any]:
        """Reads and returns global SNMP parameters from ipdevpoll configuration as a
        simple dict.
        """
        from nav.ipdevpoll.config import ipdevpoll_conf as config

        params = {}
        for var, getter in [
            ('max-repetitions', config.getint),
            ('timeout', config.getfloat),
            ('throttle-delay', config.getfloat),
        ]:
            if config.has_option(section, var):
                key = var.replace('-', '_')
                params[key] = getter(section, var)

        return params

    def as_agentproxy_args(self) -> dict[str, Any]:
        """Returns the SNMP session parameters in a dict format compatible with
        pynetsnmp.twistedsnmp.AgentProxy() keyword arguments.
        """
        kwargs = {"snmpVersion": f"v{self.version_string}"}
        if self.version in (1, 2):
            kwargs["community"] = self.community
        if self.timeout:
            kwargs["timeout"] = self.timeout
        if self.tries:
            kwargs["tries"] = self.tries

        if self.version == 3:
            params = []
            params.extend(["-l", self.sec_level.value, "-u", self.sec_name])
            if self.auth_protocol:
                params.extend(["-a", self.auth_protocol.value])
            if self.auth_password:
                params.extend(["-A", self.auth_password])
            if self.priv_protocol:
                params.extend(["-x", self.priv_protocol.value])
            if self.priv_password:
                params.extend(["-X", self.priv_password])
            kwargs["cmdLineArgs"] = tuple(params)

        return kwargs


class SnmpError(Exception):
    pass
