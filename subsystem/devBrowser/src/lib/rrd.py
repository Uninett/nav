"""
Integrate rrdBrowser into deviceBrowser...

"""

from mod_python import apache, util
import nav.config
import os
from nav.web.TreeSelect import TreeSelect, Option, Select, UpdateableSelect
from nav.rrd import presenter
import forgetHTML as html
from nav.web import urlbuilder
from nav.errors import *
import nav.web.templates.tsTemplate

def process(request):
    args = request['args']
    query = parseQuery(request['query'])
    session = request['session']
    if not args:
        raise RedirectError, urlbuilder.createUrl(division="rrd")
    if args[0] == "":
        return treeselect(request['req'], session)
        #return showIndex()
    if args[0] == "ds":
        return datasources(query, session)
    if args[0] == "timeframe":
        return timeframe(session, query)
    if args[0] == "add":
        return treeselect(request['req'], session)
    if args[0] == "join":
        try:
            idlist = query['id']
        except:
            return "nalle"
        return join(session, idlist)
    if args[0] == "remove":
        try:
            id = query['id'][0]
        except:
            return showGraphs(session)
        return remove(session, query['id'][0])
    return html.Division("args: %s, query: %s " %(str(args), str(query)))


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
    return showGraphs(session)
        
        

def remove(session, index):
    try:
        session['rrd'].presentations.pop(int(index))
    except Exception, e:
        return html.Division("%s %s" % (str(e), str(index)))
    return showGraphs(session)
def timeframe(session, query):
    for i in session['rrd'].presentations:
        i.timeLast(query['tf'][0])
    return showGraphs(session)

def showIndex():
    result = html.Division()
    result.append(html.Header("Select datasources", level=1))
    return result

def treeselect(req, session, action=None):
    result = html.Division()
    form = html.Form(action="", method='post')
    result.append(form)
    keep_blank_values = True
    req.form = util.FieldStorage(req, keep_blank_values)

    selectbox = TreeSelect()
    default_list = []
    select = Select('cn_category',
                    'Category',
                    multiple = True,
                    multipleSize = 20,
                    initTable='Cat',
                    initTextColumn='descr',
                    initIdColumn='catid')
    
    select2 = UpdateableSelect(select,           # previous element
                               'cn_netbox',      # element name
                               'Netbox',         # title
                               'Netbox',         # underlaying database table
                               'sysname',        # text column
                               'netboxid',       # id column
                               'catid',          # foreign key (from previous element)
                               default_list,     # default options
                               multiple=True,    
                               multipleSize=20)


    select3 = UpdateableSelect(select2,
                               'cn_datasource',
                               'Datasource',
                               'RrdDataSourceFile',
                               'descr',
                               'rrd_datasourceid',
                               'netboxid',
                               multiple=True,
                               multipleSize=20,
                               onchange=None)


    selectbox.addSelect(select)
    selectbox.addSelect(select2)
    selectbox.addSelect(select3)


    if req.form.has_key('cn_commitDs'):
        selectbox.update(req.form)
        try:
            pageobj = req.session['rrd']
        except:
            pageobj = presenter.page()

        datasources = req.form['cn_datasource']
        if type(datasources) != type([]):
            datasources = [datasources]

        for ds in datasources:
            a = presenter.presentation()
            a.addDs(ds)
            pageobj.presentations.append(a)
        req.session['rrd'] = pageobj
        return showGraphs(session)


    if req:
        selectbox.update(req.form)
        nameSpace = {'selectbox': selectbox}
        oldds = req.session['rrd'].presentations
        debug = {'debug': "%s Old Ds: %s" % (str(req.form.keys()), str(oldds))}
        #template = nav.web.templates.tsrrdTemplate.tsrrdTemplate(searchList=[nameSpace, debug])
        template = nav.web.templates.tsTemplate.tsTemplate()
        result.append(template.treeselect(selectbox))
        #result.append(template.respond())
    result.append(html.Input(type='submit', name='cn_commitDs', value='Add selected'))
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
    for tf in ['year', 'month', 'week', 'day', 'hour']:
        result.append(html.Anchor(tf, href='timeframe?tf=%s' % tf))
    table = html.SimpleTable()
    result.append(table)
    images = session['rrd'].presentations
    for index in range(len(images)):
        table.add(html.Image(src=images[index].graphUrl(), name=index),
                  html.Anchor('Remove', href='remove?id=%s' % index))
    result.append(html.Anchor('Add datasource', href='add'))
    return result

def datasources(query, session):
    page = presenter.page()
    if not query.has_key('id'):
        return
    id = query['id']
    timeframe = query.get('tf', ['week'])
    for i in id:
        pres = presenter.presentation(i)
        pres.timeLast(timeframe[0])
        page.presentations.append(pres)
    session['rrd'] = page
    return showGraphs(session)
        
    
