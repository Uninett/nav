from django.conf.urls import patterns, url

urlpatterns = patterns(
    'nav.web.neighbors.views',
    url(r'^$', 'index', name='neighbors-index'),
    url(r'neighbor-state/', 'set_ignored_state', name='neighbors-set-state'),
    url(r'neighbor-render-tbody/', 'render_tbody', name='neighbors-render-tbody'),
)
