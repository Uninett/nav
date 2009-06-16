# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 UNINETT AS
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
from mod_python import apache,util
from nav.web.templates.MainTemplate import MainTemplate
import nav.path, os.path

contentFile = os.path.join(nav.path.webroot, "about/about.html")

def handler(req):
    page = MainTemplate()
    req.content_type = "text/html"
    req.send_http_header()
    page.path = [("Home", "/"), ("About NAV", False)]
    page.title = "About NAV"
    page.content = lambda:file(contentFile).read()
    req.write(page.respond())
    return apache.OK
