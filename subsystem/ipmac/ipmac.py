from mod_python import apache

import re,string,sys
from mx import DateTime
from time import strftime
from socket import inet_aton,error

from ArpCamClass import ArpCamClass
from ArpCamClass import Form

from nav.web.templates.ArpCamTemplate import ArpCamTemplate

def trace(req,search="ip",from_ip="",to_ip="",mac="",days="7",dns="",aip="",naip="",prefixid=""):
  page = ArpCamTemplate()
  object = ArpCamClass()

  orgids = ("nett","idi")

  if not to_ip and from_ip:
    to_ip = from_ip
    
  form = Form(search,from_ip,to_ip,mac,days,dns,aip,naip)
  
  page.object = object

  
  #tidstreng = "end_time!='infinity' OR start_time > " + fra
  #streng = "end_time!='infinity'"
  

  if form.search == "mac":
    if not mac:
      object.errmsg = "You have to specify a MAC address"
    else:
      object.cam = object.macIcam(form)
      object.arp = object.macIarp(form)
  elif form.search == "ip":
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
  else:
    object.errmsg = "You cannot search by that category"

  object.form = form
                
  return page.respond()
