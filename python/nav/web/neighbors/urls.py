from django.conf.urls import patterns, url

urlpatterns = patterns(
    'nav.web.neighbors.views',
    url(r'', 'index', name='neighbors-index')
)
