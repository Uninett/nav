#!/usr/lib/apache/python/bin/python

from mx import DateTime
from socket import gethostbyaddr,herror,inet_aton
from time import strftime
import re, psycopg
from nav import db

## $object
##   +-- title                         ::
##   +-- errmsg                        :: error message
##   +-- Arp
##   |    +-- ip                  ::
##   |    +-- dns                 :: (optional)
##   |    +-- mac                 ::
##   |    +-- start               ::
##   |    +-- end                 ::
##   |    +-- uri                 ::
##   +-- Cam
##   |    +-- mac                 ::
##   |    +-- sysname             ::
##   |    +-- module              ::
##   |    +-- port                ::
##   |    +-- start               ::
##   |    +-- end                 ::
##   |    +-- uri                 ::
##   |
##   +-- Form                          :: choices made by the user:
##        +-- search                   :: ip or mac
##        +-- from_ip                  :: (optional)
##        +-- to_ip                    :: (optional)
##        +-- mac                      :: (optional)
##        +-- dns                      :: boolean: should DNS be shown?
##        +-- aip                    :: boolean: should all IPs be shown?
##        +-- naip                     :: boolean: should inactive IPs be shown?
##        +-- days                     :: number of days in search
##



class Form:
  def __init__(self,days="7",dns=""):

    self.search  = ""
    self.dns     = dns
    self.aip     = ""
    self.naip    = ""
    self.days    = days
    self.mac     = ""
    self.from_ip = ""
    self.to_ip   = ""

class IpForm (Form):

  def __init__(self,from_ip="",to_ip="",days="7",dns="",aip="",naip=""):
    Form.__init__(self,days,dns)
    if not from_ip:
      from_ip = "129.241."

    if not aip and not naip:
      aip="on"
      
    self.aip     = aip
    self.naip    = naip
    self.from_ip = from_ip
    self.to_ip   = to_ip

class MacForm (Form):
  def __init__(self,mac="",days="7",dns=""):
    Form.__init__(self,days,dns)

    self.mac     = mac

class PortForm:

    def __init__(self,netbox="",module="",port="",days="7",justme=""):
        if not module or module == "*":
            module = "%"
            
        if not port or port == "*":
            port = "%"

	if not days:
	    days = "7"
                
        self.netbox  = netbox
        self.module  = module
        self.port    = port
        self.days    = days
        self.justme  = justme

  
class Cam:
  def __init__(self,mac = "", sysname = "", module = None, port = None, start = None, end = None, uri = ""):
    self.mac     = mac
    self.sysname = sysname
    self.module  = module
    self.port    = port
    self.start   = start
    self.end     = end
    self.uri     = uri
      
class Arp:
  def __init__(self, ip = "", dns = "", mac = "", start = "", end = "", uri = ""):
    self.ip = ip
    self.dns= dns
    self.mac= mac
    self.start = start
    self.end = end
    self.uri = uri

class Port:
    def __init__(self,row=None,dns=""):
        if row:
            self.module   = row[0]
            self.port     = row[1]
            self.mac      = row[2]
            self.ip       = row[3]
            self.portname = row[4]
            self.dns      = dns
        else:
            self.module   = ""
            self.port     = ""
            self.mac      = ""
            self.ip       = ""
            self.portname = ""
            self.dns      = ""

            
class Trace:

  def __init__(self):
    self.arp    = None
    self.cam    = None
    self.form   = None
    self.title  = ""
    self.errmsg = ""
    self.host   = {}
  ##############################
    
  execfile("/usr/local/nav/local/etc/conf/machinetracker.conf")


  def strip_mac(self,mac):
    """ Fjerner : - . + og whitespace fra innparameter """
    mac = re.sub("\W","",mac)
#    mac = re.sub(":|-|\.\s\+","",mac)
    return mac

  #####################################################################

  def get_macstreng(self,mac):
    
    mac = self.strip_mac(mac)
    
    if len(mac)==12:
      streng = "mac = '"+mac+"'"
    elif len(mac) > 12:
      print "For lang macadresse"
      streng = mac
    else:
      streng = "mac LIKE '"+mac+"%'"
      
    return streng
                                
  #####################################################################
  
  def macIcam(self,form):
    """Soker paa mac i camtabell, gir resultat"""

    mac = form.mac
    tidstreng = self.formatTime(form.days)
    dns = form.dns

    streng = self.get_macstreng(mac)

    sql = "select netbox.sysname, ip, module, port, vlan, mac, start_time, end_time from cam inner join netbox using (netboxid) inner join prefix using (prefixid) left outer join vlan using (vlanid) where " + streng + " and " + tidstreng + " order by mac, start_time"
    
    connection = db.getConnection('webfront', 'manage')
    handle = connection.cursor()
    
    handle.execute(sql)
    cam_ = handle.fetchall()
    
    cam = []
    
    for row in cam_:
      (sysname,ip,module,port,vlan,mac,start,end) = row
      
      start = start.strftime("%Y-%m-%d %H:%M")
      if end.year>DateTime.now().year+1:
        end = "infinity"
      else:
        end = end.strftime("%Y-%m-%d %H:%M")

      uri = self.link("macIcam",row[1:5])
      if not uri:
        uri = ""
        
      cam.append(Cam(mac,sysname,module,port,start,end,uri))

    return cam
  ######################################
  
  def macIarp(self,form,prefixid="",orgids=[]):

    mac = form.mac
    tidstreng = self.formatTime(form.days)
    dns = form.dns
    aip = form.aip
    naip = form.naip
    
    streng = self.get_macstreng(mac)

    sql = "select ip,mac, start_time, end_time,vlan from prefix inner join arp using (prefixid) left outer join vlan using (vlanid) where " + streng + " and " + tidstreng + " order by ip, mac, start_time"

    connection = db.getConnection('webfront', 'manage')
    handle = connection.cursor()
    
    handle.execute(sql)
    arp_ = handle.fetchall()
    
    arp = []
    host = {}

    for row in arp_:
      ip = row[0]
      if dns:
        if not host.has_key(ip):
	  try:
            host[ip] = gethostbyaddr(ip)[0]
	  except herror,e:
	    #håndterer dnsfeil på denne uelegante måten:
	    host[ip] = "feil"
      mac = row[1]
      start = row[2]
      end = row[3]
      vlan = row[4]
      start = start.strftime("%Y-%m-%d %H:%M")
      if end.year>DateTime.now().year+1:
        end = "infinity"
      else:
        end = end.strftime("%Y-%m-%d %H:%M")

    if dns:    
      arp.append(Arp(ip,host[ip],mac,start,end))
    else:
      arp.append(Arp(ip,"",mac,start,end))
   
    return arp
  
  #########################################################################
  
  def ipIarp(self,form,prefixid="",orgids=[]):

    from_ip = form.from_ip
    to_ip = form.to_ip

    tidstreng = self.formatTime(form.days)
    dns = form.dns

    aip = form.aip
    naip = form.naip

    orgids = ('nett','idi')
    if orgids:
      orgids = " orgid in "+ str(tuple(orgids)) + " and " 
    else:
      orgids = ""

    prefixid = ""

    group = "admin"

    #raise TypeError, tidstreng

    #lager sql selv
    #sql = "select ip,mac, start_time, end_time from vlan inner join prefix using (vlan) inner join arp using (prefixid) where orgid in (,,,) and ip between '129.241.104.0' and '129.241.104.255'";
    if prefixid:
      sql = "select ip,mac, start_time, end_time from vlan inner join prefix using (vlanid) inner join arp using (prefixid) where orgid in " + orgids + " and prefixid = " + prefixid + " and " + tidstreng + " order by ip, mac, start_time";
    elif group == "admin":
      sql = "select ip,mac, start_time, end_time from prefix inner join arp using (prefixid) where ip between '" + from_ip + "' and '" + to_ip + "' and " + tidstreng + " order by ip, mac, start_time";
    else :
      sql = "select ip,mac, start_time, end_time from vlan inner join prefix using (vlan) inner join arp using (prefixid) where " + orgids + "ip between '" + from_ip + "' and '" + to_ip + "' and " + tidstreng + " order by ip, mac, start_time";

    connection = db.getConnection('webfront','manage')
    handle = connection.cursor()	
    
    handle.execute(sql)
    arp_ = handle.fetchall()
    
    arp = []
    host = {}
    convert = {}

    for row in arp_:
      ip = row[0]
      if not convert.has_key(ip):
        convert[ip] = []
      convert[ip].append(arp_.index(row))

    if prefixid:
      from_ip = arp_[0][0]
      to_ip = arp_[-1][0]

    # konverterer til størrelser som sammenliknes korrekt
    # unngår da at ip-adresser blir sammenliknet som strenger
    if not inet_aton(from_ip) > inet_aton(to_ip):

      (a,b,c,d) = map(lambda(x):int(x),from_ip.split("."))
      #(e,f,g,h) = map(lambda(x):int(x),to_ip.split("."))
      #to_ip = str(e) + "." + str(f) + "." + str(g) + "." + str(h+1)
      
      #import pprint
      #raise TypeError, from_ip + to_ip + pprint.pformat(convert)

      do = 1
      while do:

        _ip = str(a) + "." + str(b) + "." + str(c) + "." + str(d)

        if convert.has_key(_ip) and aip:

          for index in convert[_ip]:
            
            row = arp_[index]
            mac = row[1]
            start = row[2]
            end = row[3]

            start = start.strftime("%Y-%m-%d %H:%M")
            if end.year>DateTime.now().year+1:
              end = "infinity"
            else:
              end = end.strftime("%Y-%m-%d %H:%M")

            if dns:
              arp.append(Arp(_ip,self.hostname(_ip),mac,start,end))
            else:
              arp.append(Arp(_ip,"",mac,start,end))

        elif not convert.has_key(_ip) and naip:
          if dns:
            arp.append(Arp(_ip,self.hostname(_ip)))
          else:
            arp.append(Arp(_ip,""))

        d += 1

        if d == 256:
          d = 0
          c += 1

        if c == 256:
          c = 0
          b += 1

        if b == 256:
          b = 0
          a += 1

        _ip = str(a) + "." + str(b) + "." + str(c) + "." + str(d)

        if inet_aton(_ip) > inet_aton(to_ip):
          do = 0

      form.from_ip = from_ip
      form.to_ip = to_ip
      
    return arp
  
  def hostname(self,ip):

    host = self.host

    if not host.has_key(ip):
      try:
        host[ip] = gethostbyaddr(ip)[0]
      except herror:
        host[ip] = ""

    return host[ip]
 
  def formatTime(self,days):
    
    if days:
      fra = DateTime.today()-(int(days)*DateTime.oneDay)
      fra = fra.strftime("%Y-%m-%d")
      tidstreng = "start_time > '" +fra+"'"
      return tidstreng



class PortTrace:
    def __init__(self):
        self.data   = None
        self.form   = None
        self.title  = ""
        self.errmsg = ""
    
    def get_data(self,form):

        self.title = "Search for mac/ip: "+form.netbox+" module: "+form.module+" port: "+form.port+" last "+form.days+" days";

        if form.days:
            fra = DateTime.today()-(int(form.days)*DateTime.oneDay)
        fra = fra.strftime("%Y-%m-%d")

            
        sql = "SELECT DISTINCT cam.module,cam.port,cam.mac,arp.ip,swport.portname FROM netbox JOIN cam USING (netboxid) JOIN module USING (netboxid) JOIN swport USING (moduleid) JOIN arp USING (mac) WHERE "

        sql = sql+"netbox.sysName = '"+form.netbox+"' "


        if form.module == "%":
            sql = sql+"AND cam.module = module.module "
        else:
            sql = sql+"AND cam.module='"+form.module+"' AND module.module='"+form.module+"' "
            
        if form.port == "%":
            sql = sql+"AND cam.port = swport.port "
        else:
            sql = sql+"AND cam.port='"+form.port+"' AND swport.port='"+form.port+"' "

        if form.days == "0":
            sql = sql+"AND cam.end_time='infinity' AND arp.end_time='infinity' "
        else:
            sql = sql+"AND cam.end_time > '"+fra+"' AND arp.end_time > '"+fra+"' "

        if form.justme:
            sql = sql+"AND netbox.prefixid = arp.prefixid "


        sql = sql+"order by module,port,mac,ip"
            
        conn = db.getConnection('webfront', 'manage')
        cursor = conn.cursor()
        
        cursor.execute(sql)
        _data = cursor.fetchall()

        host = {}
        data = []

        
        if not _data:
            self.errmsg = "Sorry, no results"
            self.data = data

        else:
            for row in _data:
                if not host.has_key(row[3]):
                    try:
                        host[row[3]] = gethostbyaddr(row[3])[0]
                    except herror:
                        host[row[3]] = '-'
                data.append(Port(row,host[row[3]]))
            self.data = data
            
        return self


    def createTable(self,_data):
        tableHeader = "<table cellspacing=5 cellpadding=5><tr><th>module</th><th>port</th><th>portname</th><th>mac</th><th>ip</th><th>dns</th></tr>"

        tableEnd = "</table>"
        
        table = tableHeader
        
        for row in _data:
            tableRow = "<tr><td>"+str(row.module)+"</td><td>"+str(row.port)+"</td><td>"+str(row.portname)+"</td><td>"+self.hrefCam(str(row.mac))+"</td><td>"+self.hrefArp(str(row.ip))+"</td><td>"+str(row.dns)+"</td></tr>"
            table += tableRow
            
        table = table+tableEnd
            
        return table

    def createForm(self,form):
        formStart  = '<FORM METHOD="GET" ACTION="./switchport">'
        formNetbox = '<td colspan=2>Netbox <INPUT TYPE="text" NAME="netbox" SIZE="30" VALUE='+form.netbox.__str__()+'></td>'
        formModule = '<td>Module <INPUT TYPE="text" NAME="module" SIZE="5" VALUE='+form.module.__str__()+'></td>'
        formPort   = '<td>Port <INPUT TYPE="text" NAME="port" SIZE="5" VALUE='+form.port.__str__()+'></td>'
        formDays   = '<td>Last <INPUT TYPE="text" NAME="days" SIZE="5" VALUE='+form.days+'> days</td>'
        formJustme = '<td><INPUT TYPE="checkbox" NAME="justme" VALUE='+form.justme+'>My own subnet</td>'
        formSubmit = '<td><INPUT TYPE="submit" VALUE="Search"></td>'
 #       formHelp   = '<td>'+self.refHelp()+'</td>'
        formEnd    = '</FORM>'

 #       form = formStart+'<table cellspacing="5" cellpadding="5" border=1><tr>'+formNetbox+formModule+formPort+"</tr><tr>"+formJustme+formDays+formSubmit+formHelp+"</tr></table>"+formEnd

        form = formStart+'<table cellspacing="5" cellpadding="5" border=1><tr>'+formNetbox+formModule+formPort+"</tr><tr>"+formJustme+formDays+formSubmit+"</tr></table>"+formEnd
        
        return form
    
    def hrefArp(self,ip):
        ref = "<a href=/machinetracker/ip?days=7&from_ip="+ip+"&aip=on>"+ip+"</a>"
        return ref

    def hrefCam(self,mac):
        ref = "<a href=/machinetracker/mac?days=7&mac="+mac+">"+mac+"</a>"
        return ref

#    def refHelp(self):
#        tekst = "'netbox: ip or sysname<br>module, port: % gives all modules/ports<br>my own subnet: removes ip addresses used on other subnet than netbox' subnet. Giving an overview of which ip's used by a mac address while it was connected to this swport'"
#        ref = '<a href="" onclick="alert('+tekst+')">Help</a>'
#        return ref
