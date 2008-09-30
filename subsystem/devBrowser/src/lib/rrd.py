# -*- coding: UTF-8 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
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
#
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland <stain@itea.ntnu.no>
"""
Integrate rrdBrowser into deviceBrowser...

TODO:
* Define y-axis, max-min
* probably some more

Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""

try:
    from mod_python import apache, util
except:
    pass
import nav.config
import os
from nav.web.TreeSelect import TreeSelect, Option, Select, UpdateableSelect
from nav.rrd import presenter
import forgetHTML as html
from nav.web.devBrowser import urlbuilder
from nav.errors import *
from nav.web.templates.TreeSelectTemplate import TreeSelectTemplate
from nav.web.templates.SearchBoxTemplate import SearchBoxTemplate
from nav.web.SearchBox import SearchBox

from nav.db import navprofiles
import nav.db

configfile = 'rrdBrowser.conf'

def process(request):
    args = request['args']
    query = parseQuery(request['query'])
    session = request['session']
    if not args:
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "":
        return showIndex(request['req'], session)
    if args[0] == "datasources":
        return datasources(query, session)
    if args[0] == "timeframe":
        timeframe(session, query)
        session.save()
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "add":
        return treeselect(request['req'], session)
    if args[0] == 'pageAction':
        pageAction(request['req'])
        session.save()
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "graph":
        graph(request['req'], query['id'][0])
    if args[0] == "join":
        try:
            id = query['id']
        except:
            return "nalle"
        join(session, id)
        session.save()
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "split":
        try:
            id = query['id']
        except:
            return html.Division('Noe gikk galt')
        split(session, id)
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "remove":
        try:
            id = query['id']
        except:
            return html.Division('Dette gikk dårlig')
            #return showGraphs(session)
        remove(session, id)
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "zoom":
        try:
            id = int(query['id'][0])
        except Exception, e:
            return html.Division("No id passed in %s, %s" % (e, query['id']))
        try:
            value = float(query['value'][0])
        except Exception, e:
            return html.Division("Invalid value, %s, %s" % (e, query['value']))
        zoom(session, id, value)
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "save":
        try:
            name = query['name'][0]
        except:
            name = 'ingenting'
        return save(session, name)
    if args[0] == 'load':
        try:
            name = query['name'][0]
        except:
            name = 'ingenting'
        load(session, name)
        raise RedirectError, urlbuilder.createUrl(division="rrd")
        
    return html.Division("args: %s, query: %s " %(str(args), str(query)))


def pageAction(req):
    req.form = util.FieldStorage(req)
    action = req.form['action']
    zoomList = req.form['zoom']
    if req.form.has_key('cn_zoom'):
        for i in range(len(zoomList)):
            try:
                value = float(zoomList[i])
            except:
                continue
            if value != 0:
                zoom(req.session, i, value)
    try:
        selected = req.form['selected']
    except KeyError:
        selected = []
    if type(selected) != list:
        selected = [selected]
    if 'join'in action:
        return join(req.session, selected)
    if 'remove' in action:
        return remove(req.session, selected)
    if 'split' in action:
        return split(req.session, selected)
    return html.Division("req.form: %s action: %s zoom: %s selected: %s" %
                         (str(req.form), action, zoom, selected))

def join(session, list):
    try:
        page = session['rrd'].presentations
    except Exception, e:
        return html.Division("%s %s" % (str(e), str(index)))
    if len(list) < 2:
        return html.Division("Need at least 2 elements to join")
    # we want to add to our first
    first = page[int(list[0])]
    toDelete = []
    for i in list[1:]:
        i = int(i)
        toDelete.append(i)
        for ds in page[i].datasources:
            first.datasources.append(ds)
    # remove the elements joind to another, but largest id first
    toDelete.sort()
    toDelete.reverse()
    for i in toDelete:
        del page[i]
    session.save()

def split(session, list):
    graphs = session['rrd'].presentations
    splitted = []
    for index in list:
        for ds in graphs[int(index)].datasources:
            pres = presenter.presentation()
            pres.datasources.append(ds)
            splitted.append(pres)
    graphs.extend(splitted)
    session.save()
    remove(session, list)
def remove(session, list):
    try:
        list.sort()
        list.reverse()
        for i in list:
            session['rrd'].presentations.pop(int(i))
    except Exception, e:
        return html.Division("%s %s" % (str(e), str(list)))
    session.save()

def zoom(session, id, value):
    session['rrd'].presentations[id].setYAxis(value)
    session.save()

def timeframe(session, query):
    tf = query['tf'][0]
    try:
        session['rrd'].timeframeIndex = query['tfIndex'][0]
    except:
        pass
    session['rrd'].timeframe = tf
    session.save()
    for i in session['rrd'].presentations:
        i.timeLast(tf, session['rrd'].timeframeIndex)

def showIndex(req, session):
    try:
        presentations = session['rrd'].presentations
    except KeyError:
        # session contains no rrd info.
        # poor user, but sure we can help
        session['rrd'] = presenter.page()
        session['rrd'].presentations = []
        session.save()
        presentations =  session['rrd'].presentations
    if len(presentations):
        return showGraphs(session)
    return treeselect(req, session)

def treeselect(req, session, action=None):
    result = html.Division()
    keep_blank_values = True
    req.form = util.FieldStorage(req, keep_blank_values)


    searchbox = SearchBox(req,'Type a room id, an ip or a (partial) sysname')
    searchbox.addSearch('ds',
                        'Datasource',
                        'RrdDataSourceFile',
                        {'catids': ['netbox.cat'],
                         'netboxes': ['netbox'],
                         'datasources' : ['rrd_datasourceid'],
                         },
                        where = "rrd_datasource.descr like '%%%s%%'"
                        )
                        

    searchResults = searchbox.getResults(req)
    searchBoxTemplate = SearchBoxTemplate()
    result.append(searchBoxTemplate.searchbox(searchbox))
    # Some debugging
    # result.append(html.Division(str(searchResults)))
    # all treeselect stuff...
    form = html.Form(action="", method='post')
    result.append(form)
    selectbox = TreeSelect()
    default_list = []
    select = Select('cn_category',
                    'Category',
                    multiple = True,
                    multipleSize = 20,
                    initTable='Cat',
                    initTextColumn='descr',
                    initIdColumn='catid',
                    optionFormat = '$d ($v)',
                    preSelected = searchResults['catids']
                    )
    
    select2 = UpdateableSelect(select,           # previous element
                               'cn_netbox',      # element name
                               'Netbox',         # title
                               'Netbox',         # underlaying database table
                               'sysname',        # text column
                               'netboxid',       # id column
                               'catid',          # foreign key (from previous element)
                               default_list,     # default options
                               multiple=True,    
                               multipleSize=20,
                               preSelected = searchResults['netboxes']
                               )


    select3 = UpdateableSelect(select2,
                               'cn_datasource',
                               'Datasource',
                               'RrdDataSourceFile',
                               'descr',
                               'rrd_datasourceid',
                               'netboxid',
                               multiple=True,
                               multipleSize=20,
                               preSelected = searchResults['datasources'],
                               onchange=None)


    selectbox.addSelect(select)
    selectbox.addSelect(select2)
    selectbox.addSelect(select3)

    if req.form.has_key('cn_cancel'):
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    
    if req.form.has_key('cn_commitDs') or req.form.has_key('cn_joinDs'):
        selectbox.update(req.form)
        try:
            pageobj = req.session['rrd']
        except:
            pageobj = presenter.page()
        try:
            datasources = req.form['cn_datasource']
        except KeyError:
            raise RedirectError, urlbuilder.createUrl(division="rrd")
        if type(datasources) != type([]):
            datasources = [datasources]

        # if the user selected join, we use only one presentation
        currentTimeFrame = pageobj.timeframe
        if req.form.has_key('cn_joinDs'):
            a = presenter.presentation(tf=currentTimeFrame)
            for ds in datasources:
                a.addDs(ds)
            pageobj.presentations.append(a)
        else:
            for ds in datasources:
                a = presenter.presentation(tf=currentTimeFrame)
                a.addDs(ds)
                pageobj.presentations.append(a)
        req.session['rrd'] = pageobj
        req.session.save()
        raise RedirectError, urlbuilder.createUrl(division="rrd")        

    if req:
        selectbox.update(req.form)
        nameSpace = {'selectbox': selectbox}
        oldds = req.session['rrd'].presentations
        debug = {'debug': "%s Old Ds: %s" % (str(req.form.keys()), str(oldds))}
        template = TreeSelectTemplate()
        result.append(template.treeselect(selectbox))
    result.append(html.Input(type='submit', name='cn_commitDs', value='Add selected'))
    result.append(html.Input(type='submit', name='cn_joinDs', value='Add and join'))
    result.append(html.Input(type='submit', name='cn_cancel', value='Cancel'))

    # result.append(html.Division(str(select2.selectedList)))
    return result


def parseQuery(query):
    try:
        splitted = query.split('&')
    except:
        return
    d = {}
    for arg in splitted:
        try:
            key, val = arg.split('=')
        except:
            continue
        if d.has_key(key):
            d[key].append(val)
        else:
            d[key] = [val]
    return d

def showGraphs(session):
    result = html.Division()

    result.append(html.Header('IP Device Center', level=2))
    result.append(html.Header('Statistics', level=3))

    timeframes = html.Paragraph('Time frame: ')
    for tf in ['year', 'month', 'week', 'day', 'hour']:
        timeframes.append(html.Anchor(tf, href='timeframe?tf=%s' % tf))
        if tf != 'hour':
            timeframes.append(' | ')
    result.append(timeframes)

    # Display previous link allowing to navigate in time
    prevnext = html.Paragraph()
    prevnext.append(html.Anchor('&lt;&lt; Previous', href='timeframe?tf=%s&tfIndex=%s' % (
            session['rrd'].timeframe, int(session['rrd'].timeframeIndex) + 1)))
    if int(session['rrd'].timeframeIndex) > 1:
        prevnext.append(' | ')
        prevnext.append(html.Anchor('Next &gt;&gt;', href='timeframe?tf=%s&tfIndex=%s' % (
            session['rrd'].timeframe, int(session['rrd'].timeframeIndex) - 1)))
    result.append(prevnext)

    form = html.Form(action='pageAction', method='post')
    result.append(form)
    table = html.SimpleTable(id='rrdgraphs', border=1)
    selectbox = html.Select(name = 'action', onChange='this.form.submit()')
    selectbox.append(html.Option('- Choose action -', value = 'dummy'))
    selectbox.append(html.Option('Remove selected', value = 'remove'))
    selectbox.append(html.Option('Join selected', value = 'join'))
    selectbox.append(html.Option('Split selected', value = 'split'))
    table.add('', html.TableCell(selectbox, colspan="2",
                                 _class="actionselecttop"))
    result.append(table)
    images = session['rrd'].presentations
    for index in range(len(images)):
        editCell = html.Division()
        editCell.append((html.Anchor('Remove', href='remove?id=%s' % index)))
        editCell.append(html.Break())
        editCell.append(html.Anchor('Split', href='split?id=%s' % index))
        editCell.append(html.Break())
        editCell.append(html.Input(type='text', name='zoom', value='0', size='4'))
        editCell.append(html.Input(type='submit', name='cn_zoom', value='zoom'))
        table.add(html.Image(src=images[index].graphUrl(), name=index), editCell,
            html.Checkbox(name="selected", value=index))

    table.add('', html.TableCell(selectbox, colspan='2', _class="actionselectbottom"))

    result.append(html.Anchor('Add datasource', href='add'))
    #result.append(html.Division("Timeframe: %s, timeframeIndex: %s" % (session['rrd'].timeframe,
    #                                                                   session['rrd'].timeframeIndex)))
    return result

def datasources(query, session):
    page = presenter.page()
    if not query.has_key('id'):
        return
    id = query['id']
    timeframe = query.get('tf', ['week'])[0]
    for i in id:
        pres = presenter.presentation(tf=timeframe, ds=i)
        page.presentations.append(pres)
    session['rrd'] = page
    return showGraphs(session)
        
def graph(req,id):
    conf = nav.config.readConfig(configfile)
    filename = "%s%s%s" % (conf['fileprefix'],id, conf['filesuffix'])
    req.content_type  = 'image/gif'
    req.send_http_header()
    f = open(filename)
    req.write(f.read())
    f.close()
                                
def save(session, name):
    conn = nav.db.getConnection('navprofile', 'navprofile')
    key="rrdPage"
    user = session['user']
    result = html.Division("user: %s " %user)
    property = navprofiles.Accountproperty.getAll(where="accountid=%s AND property='%s'" % (user, key))
    result.append(html.Division("len(prop) = %s" % len(property)))
    if property:
        oldPages = property[0]
        try:
            value = eval(oldPages.value)
        except:
            value = []
    else:
        result.append(html.Division("Creating new row"))
        oldPages = navprofiles.Accountproperty()
        oldPages.account = user
        oldPages.property = key
        value = []
    newPages = session['rrd']
    newPages.name = name
    result.append(html.Division("New pages: %s" % newPages.serialize()))
    oldValue = value
    result.append(html.Division("Old pages: %s" % value))
    result.append(html.Division("Name: %s" % name))
    value.append(newPages.serialize())
    oldPages.value = str(value)
    a = oldPages.save()
    oldPages._saveDB()
    result.append(html.Division("hei %s" % a))
    result.append(html.Division("To save: %s" % value))
    sql = """UPDATE accountproperty set accountid=%s, property='%s', value=%s
             WHERE accountid=%s AND property='%s'""" \
    % (user, key, nav.db.escape(str(value)), user, key)
    result.append(sql)
    cursor= conn.cursor()
    cursor.execute(sql)
    return result

def load(session, name):
    user = session['user']
    key="rrdPage"
    conn = nav.db.getConnection('navprofile', 'navprofile')
    property = navprofiles.Accountproperty.getAll(where="accountid=%s AND property='%s'" % (user, key))
    if property:
        property = property[0]
    else:
        raise "hei"
    pages = eval(property.value)
    #raise str(property.value)
    for page in pages:
        if page['name'] == name:
            session['rrd'] = presenter.page(page)
            session.save()
            return
    raise "hmm: %s" % len(pages)
