from django.conf.urls.defaults import patterns, include

def get_urlpatterns():
    urlpatterns = patterns('',
        # Give the report namespace to the Report subsystem
        (r'^report/', include('nav.web.report.urls')),
    )
    return urlpatterns