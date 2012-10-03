from django.conf.urls.defaults import patterns, include

def get_urlpatterns():
    urlpatterns = patterns('',
        # Give the networkexplorer namespace to the Netmap subsystem
        (r'^report/', include('nav.web.report.urls')),
    )
    return urlpatterns