#
# Copyright (C) 2022 Sikt
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
"""Custom epollreactor implementation for ipdevpoll.

This reactor inherits Twisted's original epollrecator, but overrides the one
part that seems incompatible with pynetsnmp, which is central to ipdevpoll.
"""

import errno
import logging

from twisted.internet import epollreactor

_logger = logging.getLogger(__name__)


class EPollReactor2(epollreactor.EPollReactor):
    """A reactor that uses epoll(7), with modified handling of closed file
    descriptors
    """

    def _remove(self, xer, primary, other, selectables, event, antievent):
        """
        Private method for removing a descriptor from the event loop.

        It does the inverse job of _add, and also add a check in case of the fd
        has gone away.

        It overrides the inherited epollreactor functionality to ensure that file
        descriptors closed behind our back are ignored and properly removed from the
        reactor's internal data structures. This is needed mostly because pynetsnmp
        adds reactor readers for file descriptors that are managed by the NET-SNMP C
        library. There is no way for Python code close these file descriptors in a
        controlled way, wherein they are removed from the reactor first - the
        NET-SNMP library will close them "behind our backs", so to speak.

        Attempting to unregister a closed file descriptor from the epoll object will
        cause an OSError that the original implementation left the client to handle -
        but this also caused the internal data structures of the reactor to become
        inconsistent.
        """
        try:
            super()._remove(xer, primary, other, selectables, event, antievent)
        except OSError as error:
            if error.errno == errno.EBADF:
                fd = xer.fileno()
                _logger.debug("removing/ignoring bad file descriptor %r", fd)
                if fd in primary:
                    primary.remove(fd)
            else:
                raise


def install():
    """
    Install the epoll() reactor.
    """
    p = EPollReactor2()
    from twisted.internet.main import installReactor

    installReactor(p)


__all__ = ["EPollReactor2", "install"]
