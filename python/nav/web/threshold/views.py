# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
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
# Authors: Fredrik Skolmli <fredrik.skolmli@uninett.no>
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import logging
import time
import simplejson
import re

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models.query_utils import Q

from nav.django.utils import get_account
from nav.models.rrd import RrdFile
from nav.models.rrd import RrdDataSource
from nav.models.manage import Netbox
from nav.models.manage import Interface
from nav.models.manage import NetboxType
from nav.models.oid import SnmpOid
from nav.web.threshold.forms import RrdDataSourceForm

from nav.web.threshold.utils import is_legal_operator
from nav.web.threshold.utils import is_legal_threshold
from nav.web.threshold.utils import is_legal_interfaceid
from nav.web.threshold.utils import is_legal_descr
from nav.web.threshold.utils import is_legal_ids
from nav.web.threshold.utils import is_illegal_parameters
from nav.web.threshold.utils import is_percent_value


NAVBAR = [('Home', '/'), ('Threshold monitor', None)]
DEFAULT_VALUES = {'title': "Threshold monitor", 'navpath': NAVBAR}

logger = logging.getLogger("nav.web.threshold")

INTERFACE_REGEXP = re.compile('^if\w+$')

SAVE_ERROR_TEMPLATE = 'Failed to save threshold %s for %s\n'

MISMATCH_ERROR_TEMPLATE = ('Number of records mismatch. ' +
                          ' Asked for %d, got %d from DB')

# Option that is selected
NETBOX_OPTION_SELECTED = '<option selected="selected" value="%d">%s</option>'
# Option with no selection
NETBOX_OPTION = '<option value="%d">%s</option>'

# Format for interface-option with ifalias
IF_W_IFALIAS = """<option value="%d">%s (%s)</option>"""
# Format for Interface-option without ifalias
IF_WO_IFALIAS = """<option value="%d">%s</option>"""

def get_netbox_types(vendor=None):
    """Get all active netbox-types, optionally filtered by vendor-name"""
    query = NetboxType.objects.filter(netbox__isnull=False)
    if vendor:
        query = query.filter(vendor__id__iexact=vendor)
    query = query.values('name').order_by('name').distinct()
    # Hit the database
    all_netbox_types = query
    box_types = []
    for netbox_type in all_netbox_types:
        box_types.append(netbox_type.get('name', ''))
    return box_types

def index(request):
    """Initial page for searching """
    before = time.clock()
    account = get_account(request)
    descriptions = RrdDataSource.objects.values(
                        'description').distinct().order_by('description')
    thresholds = []
    for descr in descriptions:
        thresholds.append(descr.get('description',''))
    
    # Pick only vendors with registered netboxes
    all_box_vendors = NetboxType.objects.filter(
                    netbox__isnull=False).values('vendor').order_by(
                        'vendor').distinct()
    box_vendors = []
    for box_vendor in all_box_vendors:
        box_vendors.append(box_vendor.get('vendor', ''))

    box_types = get_netbox_types()

    all_netboxes = []
    all_interfaces = []
    info_dict = {'thresholds': thresholds,
                 'vendors': box_vendors,
                 'types': box_types,
                 'chosenboxes': all_netboxes,
                 'choseninterfaces' : all_interfaces,
                }
    info_dict.update(DEFAULT_VALUES)

    logger.error('index: timer = %.3f' % (time.clock() - before))
    logger.error('index: len(netboxes) = %d' % len(all_netboxes))
    logger.error('index: len(interfaces) = %d' % len(all_interfaces))

    return render_to_response('threshold/select.html',
        info_dict,
        RequestContext(request))
    
def prepare_bulkset(request):
    """Prepare a table of thresholds that can be manipulated in bulk.
    Get all the chosen netboxes or interfaces and render the
    html table (ref. bulkset-template).
    """
    before = time.clock()
    result = {}
    message = None
    info_dict = {}
    data_sources = []

    account = get_account(request)
    if request.method == 'POST':
        descr = unicode(request.POST.get('descr', ''))
        ids = unicode(request.POST.get('ids', ''))
        logger.error('Ids = %s' % ids)
        if not is_legal_descr(descr):
            logger.error('Illegal description: login=%s; descr=%s' %
                    (account.login, descr))
            result = {'error': 1, 'message': 'Illegal description'}
            return HttpResponse(simplejson.dumps(result),
                mimetype="application/json")
            
        if not is_legal_ids(ids, allow_empty=False):
            logger.error('Illegal identities: login=%s; ids=%s' %
                    (account.login, ids))
            result = { 'error' : 1, 'message': 'Illegal identities'}
            return HttpResponse(simplejson.dumps(result),
                mimetype="application/json")

        identities = []
        if choose_device_type(descr) == 'netbox':
            for identity in ids.split('|'):
                identities.append(int(identity))
            netboxes = Netbox.objects.filter(pk__in=identities)
            data_sources = RrdDataSource.objects.filter(
                                    description__exact=descr,
                                    rrd_file__netbox__in=netboxes)
        else:
            # Identities for interfaces are stored as varchar
            for identity in ids.split('|'):
                identities.append(identity)
            data_sources = RrdDataSource.objects.filter(
                                    description=descr,
                                    rrd_file__key='interface',
                                    rrd_file__value__in=identities)
            info_dict['interfaces'] = True

        logger.error('prepare_bulkset: identities = %d' % len(identities))
        if data_sources:
            info_dict['descr'] = descr
            info_dict['datasources'] = data_sources
        # This is actually a html-table to get rendered in the browser
        message = render_to_response('threshold/bulkset.html',
                    info_dict, RequestContext(request))
        logger.error('prepare_bulkset: timer = %.3f' % (time.clock() - before))
        return HttpResponse(message, mimetype="text/plain")
    else:
        logger.error('Illegal request: login=%s' % account.login)
        result = {'error': 1, 'message': 'Wrong request'}
        return HttpResponse(simplejson.dumps(result),
            mimetype="application/json")
    
def choose_device_type(descr):
    """Determine if the we should search for netboxes or interfaces-"""
    if INTERFACE_REGEXP.match(descr):
        return 'interface'
    return 'netbox'
    
def box_or_interface(request):
    """Take a threshold description and decide if it associated
    to a netbox or interface.
    """
    account = get_account(request)
    result = {}
    if request.method == 'POST':
        descr = unicode(request.POST.get('descr', ''))
        if is_legal_descr(descr):
            descr.strip()
            result['error'] = 0
            result['message'] = choose_device_type(descr)
        else:
            logger.error('Illegal description: login=%s; description=%s' %
                    ( account.login, descr))
            result = { 'error': 1, 'message': 'Illegal description'}
    else:
        logger.error('Illegal request: login=%s' % account.login)
        result = { 'error': 1, 'messages' : 'Illegal request'}
    return HttpResponse(simplejson.dumps(result),
        mimetype="application/json")

def get_netbox_interfaces(nbox, ifname, updown):
    """Get interfaces from netbox where ifname contains 
    a given pattern.
    """
    if_query = Interface.objects.filter(netbox=nbox)
    if nbox.category.is_sw():
        if_query = if_query.filter(baseport__isnull=False)
    if nbox.category.is_gsw() or nbox.category.is_gw():
        if_query = if_query.filter(gwportprefix__isnull=False)
    if ifname:
        if_query = if_query.filter(ifname__contains=ifname)
    if updown:
        if_query = if_query.filter(Q(to_netbox__isnull=False)|
                                        Q(to_interface__isnull=False))
    if_query = if_query.distinct()
    return if_query

def get_netbox_qualifiers(sysname, vendor, model):
    """Add qualifiers to Django-query depending on values."""
    qualifier = None
    if sysname:
        qualifier = Q(sysname__contains=sysname)
    if vendor:
        if qualifier:
            qualifier = qualifier & Q(type__vendor__id__contains=vendor)
        else:   
            qualifier = Q(type__vendor__id__contains=vendor)
    if model:   
        if qualifier:
            qualifier = qualifier & Q(type__name__contains=model)
        else:   
            qualifier = Q(type__name__contains=model)
    return qualifier

def get_netbox_categories(cat_gw, cat_gsw, cat_sw):
    """Add qualifiers to Django-query depending on values."""
    netbox_categories = []
    if cat_gw:
        netbox_categories.append('GW')
    if cat_gsw:
        netbox_categories.append('GSW')
    if cat_sw:
        netbox_categories.append('SW')
    return netbox_categories

def get_interfaces(netbox, selected_boxes, ifname, updown):
    """Get interfaces from a given netbox"""
    if selected_boxes:
        if netbox.id in selected_boxes:
            return get_netbox_interfaces(netbox, ifname, updown)
        else:
            return None
    else:
        return get_netbox_interfaces(netbox, ifname, updown)

def format_netbox_option(netbox, selected_boxes):
    """Format an option in a select-box for netboxes"""
    if netbox.id in selected_boxes:
        return NETBOX_OPTION_SELECTED % (netbox.id, netbox.sysname)
    else:
        return NETBOX_OPTION % (netbox.id, netbox.sysname)

def format_option_group(sysname, interfaces):
    """Format an option-group in a select for interfaces"""
    opt_group = ['<optgroup label="%s">' % sysname]
    for interface in interfaces:
        opt_group.append(format_interface_option(interface))
    opt_group.append('</optgroup>')
    return "".join(opt_group)
    
def format_interface_option(interface):
    """Format an option in a select box with or without ifalias"""
    if interface.ifalias:
        return IF_W_IFALIAS % (interface.id, interface.ifname,
                                    interface.ifalias)
    else:
        return IF_WO_IFALIAS % (interface.id, interface.ifname)


def get_netbox_types_options(vendor, selected):
    all_netbox_types = get_netbox_types(vendor)
    type_options = ['<option value="empty">Not Chosen</option>']
    for netbox_type in all_netbox_types:
        option = '<option value="%s"' % netbox_type
        if netbox_type == selected:
            option += ' selected="selected"'
        option += '>%s</option>' % netbox_type
        type_options.append(option)
    options = ''.join(type_options)
    return options

def netbox_search(request):
    """Search for matching netboex and/or interfaces."""
    # logger.error('netbox_search: called ...')
    before = time.clock()
    account = get_account(request)
    result = {}
    query = None
    if request.method == 'POST':
        descr = unicode(request.POST.get('descr', ''))
        sysname = unicode(request.POST.get('sysname', ''))
        vendor = unicode(request.POST.get('vendor', ''))
        model = unicode(request.POST.get('model', ''))
        cat_gw = unicode(request.POST.get('GW', ''))
        cat_gsw = unicode(request.POST.get('GSW', ''))
        cat_sw = unicode(request.POST.get('SW', ''))
        ifname = unicode(request.POST.get('ifname', ''))
        updown = unicode(request.POST.get('updown', ''))
        boxes = unicode(request.POST.get('boxes', ''))

        logger.error('descr=%s; sysname=%s; vendor=%s; model=%s; gw=%s; gsw=%s; sw=%s; ifname=%s; updown=%s; boxes=%s' %
            (descr, sysname, vendor, model, cat_gw, cat_gsw, cat_sw,
                ifname, updown, boxes))
        
        # This utillity-method return an error-message if any of
        # the parameters are illegal.
        # Maybe a little strange, but i found this very easy to implement.
        result = is_illegal_parameters(account, descr, sysname, vendor,
                                        model, cat_gw, cat_gsw, cat_sw,
                                        ifname, updown, boxes)
        if result:
            return HttpResponse(simplejson.dumps(result),
                mimetype="application/json")

            
        chosen_boxes = []
        if boxes:
            for box_id in boxes.split('|'):
                chosen_boxes.append(int(box_id))

        search_interfaces = (choose_device_type(descr) == 'interface')

        netbox_qualifiers = get_netbox_qualifiers(sysname, vendor, model)
        netbox_categories = get_netbox_categories(cat_gw, cat_gsw, cat_sw)

        if descr:
            query = Netbox.objects.filter(
                        rrdfile__rrddatasource__description=descr)
        else:
            # Make a fake query and append the qualifiers
            query = Netbox.objects.filter(sysname__isnull=False)
        query = query.distinct()
        if netbox_qualifiers:
            query = query.filter(netbox_qualifiers)
        if netbox_categories:
            query = query.filter(category__id__in=netbox_categories)

        box_interfaces = {}
        foundboxes = []
        # Let the query hit the database
        netbox_list = query
        if netbox_list:
            for nbox in netbox_list:
                if search_interfaces:
                    interfaces = get_interfaces(nbox, chosen_boxes,
                                                ifname, updown)
                    # Weed out boxes that do not have interfaces or
                    # does not have interfaces that match the search.
                    if interfaces:
                        box_interfaces[nbox.sysname] = interfaces
                foundboxes.append(format_netbox_option(nbox, chosen_boxes))

        logger.error('!!!!! number of netboxes = %d' % len(netbox_list))

        numb_interfaces = 0
        foundinterfaces = []
        if box_interfaces:
            # All interfaces that belong to the same netbox are
            # grouped together.
            for sname, infs in box_interfaces.iteritems():
                numb_interfaces += len(infs)
                foundinterfaces.append(format_option_group(sname, infs))
        logger.error('&&&&& number of interfaces = %d' % numb_interfaces)

        result = { 'error': 0,
                   'foundboxes': ''.join(foundboxes),
                   'foundinterfaces': ''.join(foundinterfaces),
                   'types': get_netbox_types_options(vendor, model),
                }

    else:
        logger.error('Illegal request: login=%s' % account.login)
        result = { 'error': 1, 'message': 'Illegal request'}
    logger.error('netbox_search: timer = %.3f' % (time.clock() - before))
    return HttpResponse(simplejson.dumps(result),
        mimetype="application/json")

def format_save_error(data_source):
    """Format a useful error-message deping on netbox or interface."""
    postfix = ''
    if data_source.rrd_file.interface:
        postfix = "%s: %s (%s)" % (
                data_source.rrd_file.interface.netbox.get_short_sysname(),
                data_source.rrd_file.interface.ifname,
                data_source.rrd_file.interface.ifalias)
    else:
        postfix = data_source.rrd_file.netbox.get_short_sysname(),
    return SAVE_ERROR_TEMPLATE % (data_source.description, postfix)
    
def save_thresholds(request):
    """Save a single or a list of thresholds."""
    account = get_account(request)
    result = {}
    message = ''
    if request.method == 'POST':
        # A string with datasource-ids, separated with "|"
        ds_ids = unicode(request.POST.get('dsIds', ''))
        operator = unicode(request.POST.get('operator', ''))
        threshold = unicode(request.POST.get('threshold', ''))

        if not is_legal_ids(ds_ids, allow_empty=False):
            logger.error('Illegal datasource-id: login=%s; id=%s' %
                (account.login, ds_ids))
            result = {'error': 1, 'message' : 'Illegal datasource'}
            return HttpResponse(simplejson.dumps(result),
                    mimetype="application/json")

        if not is_legal_operator(operator):
            logger.error('Illegal operator: login=%s; operator=%s' %
                (account.login, operator))
            result = {'error': 1, 'message' : 'Illegal operator2'}
            return HttpResponse(simplejson.dumps(result),
                    mimetype="application/json")

        if not is_legal_threshold(threshold):
            logger.error('Illegal threshold: login=%s; threshold=%s' %
                         (account.login, threshold))
            result = {'error': 1, 'message' : 'Illegal threshold'}
            return HttpResponse(simplejson.dumps(result),
                    mimetype="application/json")

        datasource_ids = []
        for ds_id in ds_ids.split('|'):
            datasource_ids.append(int(ds_id))

        rrd_data_sources = None
        try :
            rrd_data_sources = RrdDataSource.objects.filter(
                                                pk__in=datasource_ids)
        except Exception, filter_ex:
            logger.error('Exception: login=%s; exception=%s' %
                         (account.login, filter_ex))
            result = {'error': 1, 'message' : 'Illegal datasource'}
            return HttpResponse(simplejson.dumps(result),
                    mimetype="application/json")

        if len(rrd_data_sources) != len(datasource_ids):
            message = MISMATCH_ERROR_TEMPLATE % (
                        len(datasource_ids), len(rrd_data_sources))
            logger.error(message + ': login=%s' % account.login)
            result = {'error': 1, 'message' : message }
            return HttpResponse(simplejson.dumps(result),
                    mimetype="application/json")

        save_errors = []
        threshold.strip()
        for rrd_data_source in rrd_data_sources:
            if is_percent_value(threshold) and not rrd_data_source.max:
                # % is prohibited when max threshold is undefined.
                err_mesg = '; % is prohibited when max is undefined'
                log_mesg = 'login=%s; ds=%d ' % (account.login,
                                                 rrd_data_source.id)
                logger.error(log_mesg + err_mesg)
                save_errors.append((format_save_error(rrd_data_source) +
                                            err_mesg))
                continue
            rrd_data_source.threshold = threshold
            rrd_data_source.delimiter = operator
            try :
                rrd_data_source.save()
            except Exception, save_ex:
                logger.error('Exception: login=%s; ds=%d; exception=%s' %
                    (account.login, rrd_data_source.id, save_ex))
                save_errors.append(format_save_error(rrd_data_source))
        if save_errors:
            message = ''.join(save_errors)
            result = {'error': 1, 'message': message}
        else:
            msg = 'Threshold'
            if len(rrd_data_sources) > 1:
                msg += 's'
            msg += ' saved'
            result = {'error': 0, 'message': msg}
        return HttpResponse(simplejson.dumps(result),
                mimetype="application/json")
    else:
        logger.error('Illegal request: login=%s;' % account.login)
        result = {'error': 1, 'message' : 'Illegal request'}
        return HttpResponse(simplejson.dumps(result),
                mimetype="application/json")
        
def get_oid_descriptions():
    """Get the full texts for short descriptions."""
    snmp_oid_list = SnmpOid.objects.filter(
                        oid_key__isnull=False).filter(
                            description__isnull=False)
    oid_key_decriptions = {}
    for snmp_oid in snmp_oid_list:
        oid_key_decriptions[snmp_oid.oid_key] = snmp_oid.description
    return oid_key_decriptions
    
def threshold_all(request):
    """ Just list all thresholds that have a value."""
    before = time.clock()
    oid_key_descriptions = get_oid_descriptions()
    # pick all sources that have a threshold
    rrd_datasource_list = RrdDataSource.objects.filter(
                            threshold__isnull=False).order_by('rrd_file')
    # attach every datasource to a netbox
    rrd_data_sources = {}
    for rrd_datasource in rrd_datasource_list:
        rrd_datasource.extra_descr = oid_key_descriptions.get(
                                        rrd_datasource.description, '')
        sysname = rrd_datasource.rrd_file.netbox.sysname
        if not sysname in rrd_data_sources:
            rrd_data_sources[sysname] = []
        rrd_data_sources[sysname].append(rrd_datasource)

    # the view will present all netbox-nodes in a list,- and the
    # underlying datasources when the nextbox-nodes are expanded.
    netboxes = []
    for sysname, datasource_list in rrd_data_sources.iteritems():
        netbox = {
            'sysname': sysname,
            'sources': datasource_list,
            }
        netboxes.append(netbox)
    logger.error("len = %d" % len(netboxes))
    logger.error("time = %.3f" % (time.clock()-before))
    info_dict = {'netboxes' : netboxes }
    info_dict.update(DEFAULT_VALUES)
    return render_to_response('threshold/listall.html',
        info_dict,
        RequestContext(request))

def threshold_interface(request, interfaceid=None):
    """ Get threholds for a specific interface."""
    account = get_account(request)
    if not is_legal_interfaceid(interfaceid):
        logger.error('Illegal interface-id: login=%s; id=%s' %
            (account.login, interfaceid))
        return HttpResponseRedirect('/threshold/')

    interfaceid.strip()
    oid_key_descriptions = get_oid_descriptions()
    thresholds = RrdDataSource.objects.filter(
                    rrd_file__key__iexact='interface').filter(
                        rrd_file__value__iexact=interfaceid)
    for threshold in thresholds:
        threshold.extra_descr = oid_key_descriptions.get(
                                    threshold.description, '')
    sysname = thresholds[0].rrd_file.netbox.sysname
    ifname = thresholds[0].rrd_file.interface.ifname
    ifalias = thresholds[0].rrd_file.interface.ifalias
    info_dict = {
        'thresholds': thresholds,
        'sysname': sysname,
        'ifname' : ifname,
        'ifalias' : ifalias, 
        'interfaceid': interfaceid,
        }
    info_dict.update(DEFAULT_VALUES)
    return render_to_response('threshold/manageinterface.html',
        info_dict,
        RequestContext(request))

def threshold_delete(request, thresholdid=None):
    """ Delete a specific threshold."""
    if not thresholdid:
        return HttpResponseRedirect('/threshold/')
    thresholdid = int(thresholdid)
    threshold = None
    try :
        threshold = RrdDataSource.objects.get(pk=thresholdid)
    except Exception, get_ex:
        logger.error(get_ex)
        return HttpResponseRedirect('/threshold/')
    if len(request.POST.keys()):
        if request.POST.get('submit', '') == 'Yes':
            form = RrdDataSourceForm(request.POST, instance=threshold)
            if not form.errors:
                form.delete()
    else:
        info_dict = {'threshold' : threshold}
        info_dict.update(DEFAULT_VALUES)
        return render_to_response('threshold/delete.html',
            info_dict,
            RequestContext(request))
    interfaceid = threshold.rrd_file.interface_id
    url = '/threshold/interface/%d/' % interfaceid
    return HttpResponseRedirect(url)
            
def threshold_edit(request, thresholdid=None):
    """Edit a specific threshold."""
    if not thresholdid:
        return HttpResponseRedirect('/threshold/')
    threshold = None
    thresholdid = int(thresholdid)
    try :
        threshold = RrdDataSource.objects.get(pk=thresholdid)
    except Exception, get_ex:
        logger.error(get_ex)
        return HttpResponseRedirect('/threshold/')
    if len(request.POST.keys()):
        if request.POST.get('submit', '') == 'Save':
            form = RrdDataSourceForm(request.POST, instance=threshold)
            if not form.errors:
                form.save()
    else:
        form = RrdDataSourceForm(instance=threshold)
        info_dict = {
            'threshold_form': form,
            'threshold': threshold,
            }
        info_dict.update(DEFAULT_VALUES)
        return render_to_response('threshold/edit.html',
            info_dict,
            RequestContext(request))
    url = '/threshold/interface/%d/' % threshold.rrd_file.interface_id
    return HttpResponseRedirect(url)
