# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

from django.core.files import File
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from nav.config import readConfig
from nav.models.rrd import RrdFile, RrdDataSource
from nav.django.shortcuts import render_to_response, object_list
from nav.web.templates.RrdViewerTemplate import RrdViewerTemplate

def rrd_details(request, datasource_id):
    """Show the RRD graph corresponding to the given datasource ID"""

    # TODO

    return render_to_response(RrdViewerTemplate,
        'ipdevinfo/rrd-graph.html',
        {
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def rrd_image(request, rrdfile_id):
    """Return the graph image of an RRD file"""

    # Check that rrdfile_id exists
    rrdfile = get_object_or_404(RrdFile, id=rrdfile_id)

    # Get file name
    config = readConfig('rrdviewer.conf')
    file_name = '%s%s%s' % (
        config['file_prefix'], rrdfile.id, config['file_suffix'])

    # Return file content
    file = File(open(file_name))
    return HttpResponse(file.read(), mimetype='image/gif')
