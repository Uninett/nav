# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 UNINETT AS
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
"""Handler module to bypass NAV's auth system.

Apache will by default be configured to pass all requests under the
document root to NAV's nav.web.headerparserhandler function.  This
enables NAV to authenticate and authorize each request to the Apache
server.

For static documents such as images, stylesheets and javascript files
it mostly makes no sense to perform authorization checks, as no
secrets are contained in these files.  It will only incur unwanted
performance penalties.

Once a PythonHeaderParserHandler has been set for Apache's document
root, it cannot be unset for subdirectories.  This module provides a
dummy headerparserhandler which can be set for subdirectories instead,
thereby bypassing NAV's auth system.

To exclude a subdirectory from the authentication/authorization
process, add a .htaccess file to the subdirectory, contaning the
following line:

PythonHeaderParserHandler nav.web.noauth

"""

try:
    from mod_python import apache
except:
    pass

import logging

logger = logging.getLogger('nav.web.noauth')

def headerparserhandler(req):
    """Dummy headerparserhandler.

    This mod_python headerparserhandler does nothing but return a
    go-ahead OK status to Apache to process the request as it normally
    would.
    """
    logger.debug('noauth passed %s', req.uri)
    return apache.OK
