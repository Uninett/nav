# -*- coding: utf-8 -*-
#
# Copyright 2008 NTNU
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
# Authors: John-Magne Bredal <john.m.bredal@ntnu.no>
#

__copyright__ = "Copyright 2008 NTNU"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"
__id__ = "$Id$"

from django.http import HttpResponseRedirect
from nav.django.shortcuts import render_to_response

from nav.web.templates.MacWatchTemplate import MacWatchTemplate
from nav.web.macwatch.models import MacWatch, Account
from nav.web.macwatch.forms import *

def list_watch(request):
    """ Render current macwatches and option to add new one. """

    messages = request.session.get('messages',[])
    try:
        del request.session['messages']
    except KeyError:
        pass

    macwatches = MacWatch.objects.all()
    return render_to_response(MacWatchTemplate, 'macwatch/list_watches.html',
                              {'macwatches': macwatches, 'messages': messages})

def add_macwatch(request):
    """ Display form for adding of mac address to watch. """

    request.session['messages'] = []

    if request.method == 'POST':
        macwatchform = MacWatchForm(request.POST)
        if macwatchform.is_valid():
            # Get user object
            userid = request._req.session['user'].id
            u = Account.objects.get(id=userid)

            # Insert into database
            m = MacWatch(mac=macwatchform.cleaned_data['macaddress'],
                         user=u,
                         login=request._req.session['user'].login,
                         description=macwatchform.cleaned_data['description'])

            m.save()
            
            request.session['messages'].append("Added watch for %s" %m.mac)

            # Redirect to list watch
            return HttpResponseRedirect("/macwatch/")

        else:
            return render_to_response(MacWatchTemplate, 'macwatch/addmacwatch.html',
                                      {'form': macwatchform },)
            

    macwatchform = MacWatchForm()
    return render_to_response(MacWatchTemplate, 'macwatch/addmacwatch.html',
                              {'form': macwatchform },)

def delete_macwatch(request, macwatchid):
    """ Delete tuple for mac address watch """

    request.session['messages'] = []

    # Delete tuple based on url
    if macwatchid:
        # Captured args are always strings. Make it int.
        macwatchid = int(macwatchid)

        try:
            m = MacWatch.objects.get(id=macwatchid)
        except Exception, e:
            request.session['messages'].append(e)
            return HttpResponseRedirect("/macwatch/")

        if request.method == 'POST':
            if request.POST['submit'] == 'Yes':
                try:
                    m.delete()
                    request.session['messages'].append("%s deleted from watch."
                                                       %m.mac)
                except Exception, e:
                    request.session['messages'].append(e)
            else:
                return HttpResponseRedirect("/macwatch/")
                
        else:
            return render_to_response(MacWatchTemplate,
                                      'macwatch/deletemacwatch.html',
                                      {'macwatch': m})
            
    return HttpResponseRedirect("/macwatch/")

            
def edit_macwatch(request, macwatchid):
    """ Edit description on a macwatch - currently not in use """

    if request.method == 'POST':
        macwatchform = MacWatchForm(request.POST)
        if macwatchform.is_valid():
            m = MacWatch.objects.get(id=macwatchid)
            m.mac = macwatchform.cleaned_data['macaddress']
            m.description = macwatchform.cleaned_data['description']
            m.save()
            
            # Redirect to list watch
            return HttpResponseRedirect("/macwatch/")

        else:
            return render_to_response(MacWatchTemplate,
                                      'macwatch/editmacwatch.html',
                                      {'form': macwatchform },)
            
        
    if macwatchid:
        m = MacWatch.objects.get(id=macwatchid)
        data = {'macaddress':m.mac, 'description':m.description}
        macwatchform = MacWatchForm(initial=data)
        
    return render_to_response(MacWatchTemplate, 'macwatch/editmacwatch.html',
                              {'form': macwatchform },)

    
        
