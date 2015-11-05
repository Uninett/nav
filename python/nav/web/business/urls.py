"""URL config for business tool"""

from django.conf.urls import url, patterns
from nav.web.business import views

urlpatterns = patterns('',
    url(r'^$', views.BusinessView.as_view(),
        name='business-index'),
    url('^availability/$', views.AvailabilityReportView.as_view(),
        name='business-report-availability')
)
