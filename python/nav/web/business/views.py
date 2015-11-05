"""Controllers for business tool"""

from collections import defaultdict
from datetime import datetime

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from nav.web.utils import create_title
from nav.web.business import utils
from nav.models.event import AlertHistory


class BusinessView(TemplateView):
    """A default business view"""
    template_name = 'business/base.html'
    page_name = ''

    def get_context_data(self, **kwargs):
        """Creates a common context for business pages"""
        context = super(BusinessView, self).get_context_data(**kwargs)
        navpath = [('Home', '/'),
                   ('Business reports', reverse('business-index'))]

        if self.page_name:
            navpath.append((self.page_name,))

        context['navpath'] = navpath
        context['title'] = create_title(navpath)

        return context


class AvailabilityReportView(BusinessView):
    """View for the availability report"""
    template_name = 'business/report-availability.html'
    page_name = 'Availability'

    def get_context_data(self, **kwargs):
        context = super(AvailabilityReportView, self).get_context_data(**kwargs)

        if 'report-month' in self.request.GET:
            year, month = [int(x) for x in
                           self.request.GET.get('report-month').split('-')]
            sometime = datetime(year, month, 1)
            start, end = utils.get_interval(sometime)
            context['start'] = start
            context['end'] = end
            context['records'] = self.get_ipdevice_records(start, end)

        context['months'] = utils.get_months()

        return context


    @staticmethod
    def get_ipdevice_records(start, end):
        """Get all records regarding IP Devices for this period"""
        from django.db.models import Q

        # Coarse filtering of alerts
        alerts = AlertHistory.objects.filter(
            event_type='boxState', end_time__isnull=False,
            alert_type__name='boxDown').filter(
                Q(end_time__range=(start, end)) |
                Q(start_time__range=(start, end)) |
                  (Q(start_time__lte=start) & Q(end_time__gte=end)
               ))

        # Group alerts by IP Device
        grouped_alerts = defaultdict(list)
        for alert in alerts:
            grouped_alerts[alert.netbox].append(alert)

        # Create availability records for each IP Device
        return [utils.create_record(netbox, alerts, start, end)
            for netbox, alerts in grouped_alerts.items()]
