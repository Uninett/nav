"""URL config for business tool"""

from django.conf.urls import url, patterns
from nav.web.business import views

urlpatterns = patterns('',
    url(r'^$', views.BusinessView.as_view(),
        name='business-index'),
    url('^device_availability/$', views.DeviceAvailabilityReport.as_view(),
        name='business-report-device-availability'),
    url('^link_availability/$', views.LinkAvailabilityReport.as_view(),
        name='business-report-link-availability')
)
