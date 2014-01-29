"""Radius backend URL config."""
from django.conf.urls.defaults import url, patterns
from nav.web.radius.views import (index, log_search, account_charts,
                                  account_search, log_detail_page,
                                  log_detail_modal, account_detail_page,
                                  account_detail_modal)

urlpatterns = patterns('nav.web.radius.views',
    url(r'^$', index, name='radius-index'),
    url(r'^logsearch$', log_search, name='radius-log_search'),
    url(r'^logdetail/(?P<accountid>\d+)/modal$', log_detail_modal,
        name='radius-log_detail-modal'),
    url(r'^logdetail/(?P<accountid>\d+)$', log_detail_page,
        name='radius-log_detail'),
    url(r'^acctdetail/(?P<accountid>\d+)/modal$', account_detail_modal,
        name='radius-account_detail-modal'),
    url(r'^acctdetail/(?P<accountid>\d+)$', account_detail_page,
        name='radius-account_detail'),
    url(r'^acctcharts$', account_charts, name='radius-account_charts'),
    url(r'^acctsearch$', account_search, name='radius-account_search')
)
