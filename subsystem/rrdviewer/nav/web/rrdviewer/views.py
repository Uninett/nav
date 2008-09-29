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
from django.template import RequestContext

from nav.config import readConfig
from nav.django.shortcuts import render_to_response, object_list
from nav.models.rrd import RrdFile, RrdDataSource
from nav.rrd import presenter
from nav.web.templates.RrdViewerTemplate import RrdViewerTemplate

def rrd_details(request, rrddatasource_id, time_frame='week'):
    """Show the RRD graph corresponding to the given datasource ID"""

    # Get data source
    rrddatasource = get_object_or_404(RrdDataSource, id=rrddatasource_id)

    # Play along with the very legacy nav.rrd.presenter
    presenter_page = presenter.page()
    presentation = presenter.presentation(tf=time_frame, ds=rrddatasource.id)
    presenter_page.presentations.append(presentation)

    return render_to_response(RrdViewerTemplate,
        'rrdviewer/rrd-details.html',
        {
            'rrddatasource': rrddatasource,
            'presenter_page': presenter_page,
        },
        context_instance=RequestContext(request))

def rrd_image(request, rrdfile_id):
    """Return the graph image of an RRD file"""

    # Get file name
    config = readConfig('rrdviewer/rrdviewer.conf')
    file_name = '%s%s%s' % (
        config['file_prefix'], rrdfile_id, config['file_suffix'])

    # Return file content
    file = File(open(file_name))
    return HttpResponse(file.read(), mimetype='image/gif')
