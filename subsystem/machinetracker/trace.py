from mod_python import apache

import re,string,sys
from mx import DateTime
from time import strftime
from socket import inet_aton,error

import Trace
#from Trace import PortTrace
from URI import URI

from nav.web.templates.ArpCamTemplate import ArpCamTemplate,MainTemplate

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
    page.title = "Trace"
    page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Trace", False)]
    req.content_type = "text/html"
    req.send_http_header()

    c = ""
    
    if section and section != "trace":
      c += "The specified section '"+section+"' does not exist"

    c += "<p><h2>Trace Tools</h2></p>Search for:<br>"
    c += "<a href=ip>ip</a><br>"
    c += "<a href=mac>mac</a><br>"
    c += "mac/ip connected to a specific <a href=switchport>switch port</a><br>" 
    page.content = lambda:c
    req.write(page.respond())

    return apache.OK

    
  

def ip(req, from_ip="",to_ip="",days="7",dns="",aip="",naip="",prefixid=""):
  page = ArpCamTemplate()
  object = Trace.Trace()
  keyword = "IP"
  if not days:
    days = "7"

  orgids = ()

  if not to_ip and from_ip:
    to_ip = from_ip
    
  form = Trace.IpForm(from_ip,to_ip,days,dns,aip,naip)
  
  page.object = object

  page.title = "Trace - "+keyword
  page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Trace", "/trace/"), (keyword,False)]
  
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
  page = ArpCamTemplate()
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
                
  page.title = "Trace - "+keyword
  page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Trace", "/trace/"), (keyword,False)]
  return page.respond()

  
def switchport(req, netbox="", module="%", port="%"):

    keyword = "Switchport"

    page = MainTemplate()
    req.content_type = "text/html"
    req.send_http_header()
    #import PortTrace
    object = Trace.PortTrace()

    object.form = Trace.PortForm(netbox,module,port)
        
    streng = object.createForm(object.form)
    if object.form.netbox:
        
        object = object.get_data(object.form)
        
        streng = streng+"<h3>"+object.title+"</h3>"
        
        if object.errmsg:
            streng = streng+object.errmsg 
        else:
            streng = streng+object.createTable(object.data)


    page.content = lambda:streng
    page.title = "Trace - "+keyword
    page.path = [("Frontpage", "/"), ("Tools", "/toolbox"), ("Trace", "/trace/"), (keyword,False)]


    return page.respond()

