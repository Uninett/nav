"""
Integrate rrdBrowser into deviceBrowser...



TODO:
* Define y-axis, max-min
* probably some more

Author: Magnus Nordseth <magnun@stud.ntnu.no>
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
    if args[0] == 'graphAction':
        graphAction(request['req'])
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
    
    return html.Division("args: %s, query: %s " %(str(args), str(query)))


def graphAction(req):
    req.form = util.FieldStorage(req)
    action = req.form['action']
    selected = req.form['selected']
    if type(selected) != list:
        selected = [selected]
    if 'join'in action:
        return join(req.session, selected)
    if 'remove' in action:
        return remove(req.session, selected)
    if 'split' in action:
        return split(req.session, selected)
    return html.Division("req.form: %s action: %s selected: %s" % (str(req.form), action, selected))

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
def timeframe(session, query):
    for i in session['rrd'].presentations:
        i.timeLast(query['tf'][0])

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
        req.session.save()
        raise RedirectError, urlbuilder.createUrl(division="rrd")        

    if req:
        selectbox.update(req.form)
        nameSpace = {'selectbox': selectbox}
        oldds = req.session['rrd'].presentations
        debug = {'debug': "%s Old Ds: %s" % (str(req.form.keys()), str(oldds))}
        template = nav.web.templates.tsTemplate.tsTemplate()
        result.append(template.treeselect(selectbox))
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
    form = html.Form(action='graphAction', method='post')
    result = html.Division()
    form.append(result)
    for tf in ['year', 'month', 'week', 'day', 'hour']:
        result.append(html.Anchor(tf, href='timeframe?tf=%s' % tf))
    table = html.SimpleTable(id='rrdgraphs')
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
        table.add(html.Image(src=images[index].graphUrl(), name=index), editCell,
            html.Checkbox(name="selected", value=index))

    table.add('', html.TableCell(selectbox, colspan='2', _class="actionselectbottom"))
    result.append(html.Anchor('Add datasource', href='add'))
    return form

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
        
def graph(req,id):
    conf = nav.config.readConfig(configfile)
    filename = "%s%s%s" % (conf['fileprefix'],id, conf['filesuffix'])
    req.content_type  = 'image/gif'
    req.send_http_header()
    f = open(filename)
    req.write(f.read())
    f.close()
                                
