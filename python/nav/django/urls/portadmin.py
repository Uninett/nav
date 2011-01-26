from django.conf.urls.defaults import *

def get_urlpatterns():
    urlpatterns = patterns('',
        (r'^portadmin/', include('nav.web.portadmin.urls')),
    )
    return urlpatterns
