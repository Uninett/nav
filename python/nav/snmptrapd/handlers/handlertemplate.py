#
# Copyright (C) 2018 Uninett AS
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


import logging
import nav.errors
from nav.db import getConnection
from nav.event import Event


# Create logger with modulename here
_logger = logging.getLogger(__name__)


# If you need to contact database.
global db
db = getConnection('default')


def handleTrap(trap, config=None):
    """
    handleTrap is run by snmptrapd every time it receives a
    trap. Return False to signal trap was discarded, True if trap was
    accepted.
    """

    # Use the trap-object to access trap-variables and do stuff.
    if trap.genericType in ['LINKUP', 'LINKDOWN']:
        _logger.debug("This is a linkState trap")

    # config may be fetched like this
    variable = config.get('template', 'variable')

    if doSomething:

        # Events are posted like this. For more information about the
        # event-module see "pydoc nav.event"

        # Create eventobject.
        e = Event(
            source=source,
            target=target,
            netboxid=netboxid,
            deviceid=deviceid,
            subid=subid,
            eventtypeid=eventtypeid,
            state=state,
        )

        # These go to eventqvar.
        e['alerttype'] = 'linkUp'
        e['module'] = module

        try:
            e.post()
        except nav.errors.GeneralException as why:
            _logger.error(why)
            return False

        # Return True if trap was processed.
        return True
    else:
        # Return False if this trap was not interesting.
        return False


# This function is a nice to run to make sure the event and alerttypes
# exist in the database if you post events for alerting.


def verifyEventtype():
    """
    Safe way of verifying that the event- and alarmtypes exist in the
    database. Should be run when module is imported.
    """

    c = db.cursor()

    # NB: Remember to replace the values with the one you need.

    sql = """
    INSERT INTO eventtype (
    SELECT 'linkState','Tells us whether a link is up or down.','y' WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'linkState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkUp', 'Link active' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkUp'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkDown', 'Link inactive' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkDown'));
    """

    queries = sql.split(';')
    for q in queries:
        if len(q.rstrip()) > 0:
            c.execute(q)

    db.commit()


def initialize():
    """Initialize method for snmpdtrap daemon so it can initialize plugin
    after __import__
    """
    verifyEventtype()
