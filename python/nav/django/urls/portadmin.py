"""PortAdmin URL config inclusion"""

from django.conf.urls.defaults import patterns, include

def get_urlpatterns():
    urlpatterns = patterns('',
        (r'^portadmin/', include('nav.web.portadmin.urls')),
    )
    return urlpatterns
