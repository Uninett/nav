from mod_python import apache
from nav.db import manage
from nav.web import urlbuilder
import forgetHTML as html

def process(request):
    # PYTHON IMPORTS ZUCZ=RZZZ!!
    import netbox
    netbox = netbox.findNetbox(request['hostname'])
    module = findModule(netbox, request['module'])
    result = html.Division()
    result.append("Module %s, netbox %s" % 
                   (module.module,
                   urlbuilder.createLink(module.netbox)))
    result.append(showModuleLegend())                
    moduleInfo = ModuleInfo(module)
    result.append(moduleInfo.showModule())               
    return result               
    

def findModule(netbox, moduleName):
    # possible bug: module can't be named 'module'! =)
    moduleName = moduleName.replace("module", "").lower()
    allModules = netbox.getChildren(manage.Module)
    for m in allModules:
        if m.module.lower() == moduleName:
            return m
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

class ModuleInfo(manage.Module):
    def showModule(self):
        def findDisplayWidth(ports):
            # Normally we'll show 12 ports in a row, but
            # sometimes (?) 16 could be the one.
            length = len(ports)
            for x in 12,16,8,14:
                if not length % x:
                    return x
            return 12

        ports = self.getChildren(manage.Swport, orderBy=('port', 'ifindex'))
        if not ports:
            type = "gw"
        else:
            type = "sw"
        #ports += self.getChildren(manage.Gwport)

        if not ports:
            return None

        moduleView = html.Division(_class="module")
        if type == "gw":
            moduleView['class'] += ' gw'
        moduleView.append(html.Header(self.module or "", level=3))
        # calc width
        width = findDisplayWidth(ports)
        count = 0
        portTable = html.Table()
        moduleView.append(portTable)
        row = html.TableRow()
        for port in ports:
            if count and not count % width:
                portTable.append(row)
                row = html.TableRow()
            count += 1
            if type=="gw":
                if port.masterindex:
                    portNr = "%s-%s" % (port.masterindex, port.ifindex)
                else:
                    portNr = port.ifindex
            else:
                # Hmmmmmm what's the difference between these?
                # portNr = (port.ifindex is not None and port.ifindex) or port.port
                portNr = (port.port is not None and port.port) or port.ifindex
            portView = html.TableCell(urlbuilder.createLink(port, content=portNr), _class="port")
            row.append(portView)
            titles = []
            portView['title'] = ""
            if type == 'sw' and port.link <> 'y':
                portView['class'] += ' passive'
                titles.append('not active')
            if port.speed:
                portView['class'] += ' Mb%d' % port.speed
                titles.append( '%d Mbit' % port.speed)
            if type == 'sw':
                if port.trunk:
                    portView['class'] += ' trunk'
                    titles.append("trunk")
                portView['class'] += ' %sduplex' % port.duplex
                if port.duplex == 'h':
                    titles.append("half duplex")
                elif port.duplex == 'f':
                    titles.append("full duplex")
                if port.media:
                    titles.append(port.media)
                vlans = port.getChildren(manage.Swportvlan)
                if vlans:
                    vlans = [str(x.vlan) for x in vlans]
                    titles.append('Vlan ' + ','.join(vlans))
                blocked = port.getChildren(manage.Swportblocked)
                if blocked:
                    portView['class'] += ' blocked'
                    vlans = [str(block.vlan) for block in blocked]
                    titles.append("blocked " + ','.join(vlans))
            if type == 'gw':
                for item in port._values.items():
                    titles.append("%s %s" % item)
            if titles:
                # beautiful! but .capitalize() lowercases everything first
                titles[0] = titles[0][0].upper() + titles[0][1:]
                title = ', '.join(titles)
                portView['title'] = title

        portTable.append(row)
        return moduleView

def showModuleLegend():
    legend = html.Division(_class="legend")
    legend.append(html.Header("Legend", level=3))
    def mkLegend(name, descr):
        port = html.Span("1")
        port['class'] = "port %s" % name
        legend.append(port)
        legend.append(descr)
        legend.append(" ")
    mkLegend("passive", "Not active")
    mkLegend("hduplex", "Half duplex")
    mkLegend("blocked", "Blocked")
    mkLegend("Mb10", "10 Mbit")
    mkLegend("Mb100", "100 Mbit")
    mkLegend("Mb1000", "1 Gbit")
    mkLegend("trunk", "Trunk")
    legend.append(html.Break())
    legend.append(html.Emphasis("Hold mouse over port for info, click for details"))
    return legend
