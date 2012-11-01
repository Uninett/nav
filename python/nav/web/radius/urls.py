"""Radius backend URL config."""
from django.conf.urls import url
from nav.web.radius.views import index, log_search, account_charts, account_search

urlpatterns = patterns('nav.web.radius.views',
    url(r'^$', index, name='radius-index'),
    url(r'^logsearch$', log_search, name='radius-log_search'),
    url(r'^acctcharts$', account_charts, name='radius-account_charts'),
    url(r'^acctsearch$', account_search, name='radius-account_search')
)
