#
# Copyright (C) 2012 Uninett AS
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
"common AgentProxy mixin"
import time
import logging
from functools import wraps
from collections import namedtuple

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.task import deferLater

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


# pylint: disable=R0903
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
            self.snmp_parameters = SNMP_DEFAULTS
        self._result_cache = {}
        self._last_request = 0
        self.throttle_delay = self.snmp_parameters.throttle_delay

        super(AgentProxyMixIn, self).__init__(*args, **kwargs)
        # If we're mixed in with a pure twistedsnmp AgentProxy, the timeout
        # parameter will have no effect, since it is an argument to individual
        # method calls.
        self.timeout = self.snmp_parameters.timeout

    def __repr__(self):
        return "<{module}.{klass}({ip}, ...) at {ident}>".format(
            module=self.__class__.__module__,
            klass=self.__class__.__name__,
            ip=repr(self.ip),
            ident=id(self))

    # hey, we're mimicking someone else's API here, never mind the bollocks:
    # pylint: disable=C0111,C0103
    @cache_for_session
    def getTable(self, *args, **kwargs):
        kwargs['maxRepetitions'] = self.snmp_parameters.max_repetitions
        return super(AgentProxyMixIn, self).getTable(*args, **kwargs)

    # hey, we're mimicking someone else's API here, never mind the bollocks:
    # pylint: disable=C0111,C0103
    @throttled
    def _get(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._get(*args, **kwargs)

    # hey, we're mimicking someone else's API here, never mind the bollocks:
    # pylint: disable=C0111,C0103
    @throttled
    def _walk(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._walk(*args, **kwargs)

    # hey, we're mimicking someone else's API here, never mind the bollocks:
    # pylint: disable=C0111,C0103
    @throttled
    def _getbulk(self, *args, **kwargs):
        return super(AgentProxyMixIn, self)._getbulk(*args, **kwargs)


# pylint: disable=C0103
SNMPParameters = namedtuple('SNMPParameters',
                            'timeout max_repetitions throttle_delay')

SNMP_DEFAULTS = SNMPParameters(timeout=1.5, max_repetitions=50,
                               throttle_delay=0)


# pylint: disable=W0212
def snmp_parameter_factory(host=None):
    """Returns specific SNMP parameters for `host`, or default values from
    ipdevpoll's config if host specific values aren't available.

    :returns: An SNMPParameters namedtuple.

    """
    section = 'snmp'

    from nav.ipdevpoll.config import ipdevpoll_conf as config
    params = SNMP_DEFAULTS._asdict()

    for var, getter in [
            ('max-repetitions', config.getint),
            ('timeout', config.getfloat),
            ('throttle-delay', config.getfloat),
    ]:
        if config.has_option(section, var):
            key = var.replace('-', '_')
            params[key] = getter(section, var)

    return SNMPParameters(**params)


class SnmpError(Exception):
    pass
