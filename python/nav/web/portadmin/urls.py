from django.conf.urls.defaults import *
from nav.web.portadmin.views import *

urlpatterns = patterns('',
    url(r'^$', index),
    url(r'^ip=(?P<ip>[\d\.]+)', search_by_ip),
    url(r'^sysname=(?P<sysname>\S+)', search_by_sysname),
    url(r'^interfaceid=(?P<interfaceid>\d+)', search_by_interfaceid),
    url(r'^save_interfaceinfo', save_interfaceinfo),
   )
