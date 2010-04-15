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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from nav.config import readConfig
from nav.models.manage import SwPort, GwPort
from nav.models.rrd import RrdFile, RrdDataSource
from nav.rrd import presenter

def rrd_index(request):
    """Redirect to the IP Device Info search page"""

    return HttpResponseRedirect(reverse('ipdevinfo-search'))

def rrd_details(request, rrddatasource_id, time_frame='week'):
    """Show the RRD graph corresponding to the given datasource ID"""

    errors = []

    # Get data source
    rrddatasource = get_object_or_404(RrdDataSource, id=rrddatasource_id)

    # Get related port
    if rrddatasource.rrd_file.key == 'swport':
        port = get_object_or_404(SwPort, id=rrddatasource.rrd_file.value)
    elif rrddatasource.rrd_file.key == 'gwport':
        port = get_object_or_404(GwPort, id=rrddatasource.rrd_file.value)
    else:
        port = None

    # Check if RRD file exists
    fs = FileSystemStorage(location=rrddatasource.rrd_file.path)
    if not fs.exists(rrddatasource.rrd_file.get_file_path()):
        errors.append('Cannot find the RRD file "%s".' %
            rrddatasource.rrd_file.get_file_path())
        presenter_page = None
    else:
        # Play along with the very legacy nav.rrd.presenter
        presenter_page = presenter.page()
        presentation = presenter.presentation(
            tf=time_frame, ds=rrddatasource.id)
        presenter_page.presentations.append(presentation)

    return render_to_response(
        'rrdviewer/rrd-details.html',
        {
            'errors': errors,
            'rrddatasource': rrddatasource,
            'time_frame': time_frame,
            'port': port,
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
