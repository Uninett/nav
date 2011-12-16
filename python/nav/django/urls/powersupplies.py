"""PortAdmin URL config inclusion"""

from django.conf.urls.defaults import patterns, include

def get_urlpatterns():
    urlpatterns = patterns('',
        (r'^powersupplies/', include('nav.web.powersupplies.urls')),
    )
    return urlpatterns
