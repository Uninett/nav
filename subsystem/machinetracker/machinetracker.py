from mod_python import apache

import re,string,sys
from mx import DateTime
from time import strftime
from socket import inet_aton,error

import Trace
#from Trace import PortTrace
from URI import URI

from nav.web.templates.MachineTrackerTemplate import MachineTrackerTemplate,MainTemplate

def handler(req):
  s = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
  if s:
    section = s.group(1)
  else:
    section = ""

  args = URI(req.unparsed_uri)

  if section.lower() == "ip":
    contents = ip(req,args.get("from_ip"),args.get("to_ip"),args.get("days"),args.get("dns"),args.get("aip"),args.get("naip"),args.get("prefixid"));
    req.write(contents)
#str(args.get("dns"))+str(args.get("days"))+
    return apache.OK

  elif section.lower() == "mac":
    contents = mac(req,args.get("mac"),args.get("days"),args.get("dns"),args.get("aip"),args.get("naip"),args.get("prefixid"));
    req.write(contents)
    return apache.OK


  elif section.lower() == "switchports" or section.lower() == "switchport" or section.lower() == "swport" or section.lower() == "port":
    contents = switchport(req,args.get("netbox"),args.get("module"),args.get("port"));
    req.write(contents)
    return apache.OK

  else:
    page = MainTemplate()
    page.title = "Machine Tracker"
    page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Machine Tracker", False)]
    req.content_type = "text/html"
    req.send_http_header()

    c = ""
    
    if section and section != "machinetracker":
      c += "The specified section '"+section+"' does not exist"

    c += "<p><h2>Machine Tracker</h2>"

    c += "The NAV system collects arp and cam information from all registered net devices.<br> Arp data from all routers are inserted into the NAV database every 30. minutes,<br> and mac address tables from all layer2-equipment are collected and inserted every X. minutes.<p> Machine tracker gives you the oppertunity to search these data, to trace the whereabouts of a mac address or an IP address.<br> The reverse search is also possible - to find which mac/ip was registered on a specified switchport in the last days.<p>"

    c += "<h3>Search for: "
    c += "<a href=ip>IP</a> | "
    c += "<a href=mac>mac</a> | "
    c += "<a href=switchport>switch port</a></h3>" 
    page.content = lambda:c
    req.write(page.respond())

    return apache.OK

    
  

def ip(req, from_ip="",to_ip="",days="7",dns="",aip="",naip="",prefixid=""):
  page = MachineTrackerTemplate()
  object = Trace.Trace()
  keyword = "IP"
  if not days:
    days = "7"

  orgids = ()

  if not to_ip and from_ip:
    to_ip = from_ip
    
  form = Trace.IpForm(from_ip,to_ip,days,dns,aip,naip)
  
  page.object = object

  page.title = "Machine Tracker - "+keyword
  page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Machine Tracker", "/machinetracker/"), (keyword,False)]
  
  if not from_ip and not prefixid:
    #object.errmsg = "You have to specify a valid IP address in the 'from'-field"
    pass
  else:
    if to_ip:
      try:
        if inet_aton(from_ip) > inet_aton(to_ip):
          object.errmsg = "The IP address in the 'from'-field cannot be larger than the IP address in the 'to'-field"
        elif not re.search("\d+\.\d+\.\d+\.\d+",from_ip) or to_ip and not re.search("\d+\.\d+\.\d+\.\d+",to_ip):
          object.errmsg = "One of the addresses is not a valid IP address"
        else:
          object.arp = object.ipIarp(form,prefixid=prefixid,orgids=orgids)
          if not object.arp:
            object.errmsg = "Your search did not return any results"
      except error:
        object.errmsg = "One of the addresses is not a valid IP address"
  object.form = form
                
  return page.respond()
  

def mac(req, mac="",days="7",dns="",aip="",naip="",prefixid=""):
  page = MachineTrackerTemplate()
  keyword = "Mac"
  if not days:
    days = "7"
  object = Trace.Trace()

  orgids = ("nett","idi")

  form = Trace.MacForm(mac,days,dns)
  
  page.object = object

  if not mac:
    object.errmsg = "" #You have to specify a MAC address #ikke pen
  else:
    object.cam = object.macIcam(form)
    object.arp = object.macIarp(form)

  object.form = form
                
  page.title = "Machine Tracker - "+keyword
  page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Machine Tracker", "/machinetracker/"), (keyword,False)]
  return page.respond()

  
def switchport(req, netbox="", module="", port="", days=""):

    if not days:
	days="7"

    keyword = "Switchport"

    page = MainTemplate()
    req.content_type = "text/html"
    req.send_http_header()
    #import PortTrace
    object = Trace.PortTrace()

    object.form = Trace.PortForm(netbox,module,port,days)
        
    streng = object.createForm(object.form)
    if object.form.netbox:
        
        object = object.get_data(object.form)
        
        streng = streng+"<h3>"+object.title+"</h3>"
        
        if object.errmsg:
            streng = streng+object.errmsg 
        else:
            streng = streng+object.createTable(object.data)


    page.content = lambda:streng
    page.title = "Machine Tracker - "+keyword
    page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Machine Tracker", "/machinetracker/"), (keyword,False)]


    return page.respond()

