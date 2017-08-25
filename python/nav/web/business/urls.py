"""URL config for business tool"""

from django.conf.urls import url, patterns
from nav.web.business import views

urlpatterns = patterns('',
    url(r'^$', views.BusinessView.as_view(),
        name='business-index'),
    url('^device_availability/$', views.DeviceAvailabilityReport.as_view(),
        name='business-report-device-availability'),
    url('^link_availability/$', views.LinkAvailabilityReport.as_view(),
        name='business-report-link-availability'),
    url('^save_report_subscription', views.save_report_subscription,
        name='save-report-subscription'),
    url('^render_report_subscriptions', views.render_report_subscriptions,
        name='render-report-subscriptions'),
    url('^remove_report_subscription', views.remove_report_subscription,
        name='remove-report-subscription')
)
