from mod_python import apache
import forgetHTML as html
from nav.db import manage
from nav.web import urlbuilder
import re

_directions = {
    'u': 'undefined',
    'o': 'up',
    'n': 'down',
    'b': 'both',
    'x': 'crossed',
}
_duplex = { 'f': 'Full duplex',
            'h': 'Half duplex',
}            
_link = {
    'd': 'Denied', 
    'n': 'Not active',
    'y': 'Active',
}

def process(request):
    import netbox,module
    netbox = netbox.findNetboxes(request['hostname'])
    if len(netbox) > 1:
        return
    netbox = netbox[0]
    module = module.findModule(netbox, request['module'])
    port = findPort(module, request['port'])
    request['templatePath'].append((str(netbox), 
                                    urlbuilder.createUrl(netbox)))
    request['templatePath'].append(("Module %s" % module.module, 
                                    urlbuilder.createUrl(module)))
    request['templatePath'].append(('Port %s' % port.port, None))
    result = html.Division()
    result.append(showInfo(port))
    return result

def findPort(module, portName):
    portName = portName.replace("port", "").lower()
    allPorts = module.getChildren(manage.Swport)
    for p in allPorts:
        if str(p.port) == portName:
            return p
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

def showInfo(port):
    info = html.Division()
    module = port.module
    info.append(html.Header("Device %s, module %s, port %s" % 
                (urlbuilder.createLink(module.netbox),
                urlbuilder.createLink(module, content=module.module),
                port.port)))
 
    table = html.SimpleTable()            
    info.append(table)
    for field in \
        'port duplex ifindex portname media link speed trunk'.split():
        value = getattr(port, field)
        if value is None:
            continue
        if field == 'duplex':
            value = _duplex.get(value, 'Unknown %s' % value)
        table.add(field.capitalize(), value)
    for field in 'to_netbox', 'to_swport':
        value = getattr(port, field)
        if value is None:
            continue
        title = field.replace("_", " ").capitalize()    
        table.add(title, urlbuilder.createLink(value))

    rrd = showRrds(port)        
    if rrd:
        info.append(rrd)
    vlanInfo = getVlanInfo(port)
    if vlanInfo:
        info.append(vlanInfo)
    return info    

def getVlanInfo(port):    
    vlans = port.getChildren(manage.Swportvlan)
    blocked = port.getChildren(manage.Swportblocked)
    allowed = port.getChildren(manage.Swportallowedvlan)

    if not vlans and not blocked and not allowed:
        return None # Nothing to show

    vlanInfo = html.Division()
    vlanInfo.append(html.Header("VLANs", level=2))
    if vlans:
        for vlanlink in vlans:
            vlan = manage.Vlan(vlanlink.vlan)
            line = html.Division()
            try:
                line.append(urlbuilder.createLink(vlan))
            except:
                #raise str(vlan)
                pass
            if vlanlink.direction is not None:
                line.append("(direction %s)" % 
                    _directions.get(vlanlink.direction, 
                                    "Unknown %s" % vlanlink.direction))
            vlanInfo.append(line)
    if blocked:
        vlanInfo.append(html.Header("Blocked", level=3))
        for vlanlink in blocked:
            vlan = manage.Vlan(vlanlink.vlan)
            div = html.Division()
            try:
                div.append(urlbuilder.createLink(vlan))
            except:
                #raise str(vlan.vlanid)
                pass
            vlanInfo.append(div)

    # This is no useful information. I remove it for now...
    #if allowed:
    #    vlanInfo.append(html.Header("Allowed hexstrings", level=3))
    #    for allow in allowed:
    #        hex = allow.hexstring
    #        # insert some linebreaks
    #        hex = re.sub(r"(.{50})", "\\1\n", hex)
    #        pre = html.Pre(hex)
    #        vlanInfo.append(pre)

    return vlanInfo
    
def showRrds(port):
    netbox = port.module.netbox
    rrdfiles = manage.Rrd_file.getAll(where="key='swport' and value='%s'" % port.swportid)
    if not rrdfiles:
        return None
    result = html.Division()
    result.append(html.Header("Statistics", level=2))
    all = []
    for rrd in rrdfiles:
        for ds in rrd.getChildren(manage.Rrd_datasource):
            link = urlbuilder.createLink(subsystem='rrd',
                id=ds.rrd_datasourceid, division="datasources", content=(ds.descr or "(unknown)"))
            all.append(ds.rrd_datasourceid)    
            result.append(html.Division(link))
    link = urlbuilder.createLink(subsystem='rrd',
                id=all, division="datasources", content="[All]")
    result.append(html.Division(link))
    return result
