"""Controllers for business tool"""

from collections import defaultdict
from operator import attrgetter
from datetime import datetime

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from nav.web.utils import create_title
from nav.web.business import utils
from nav.models.event import AlertHistory
from nav.models.manage import Interface


class BusinessView(TemplateView):
    """A default business view"""
    template_name = 'business/base.html'
    report_name = ''

    def get_context_data(self, **kwargs):
        """Creates a common context for business pages"""
        context = super(BusinessView, self).get_context_data(**kwargs)
        navpath = [('Home', '/'),
                   ('Business reports', reverse('business-index'))]

        if self.report_name:
            navpath.append((self.report_name,))

        context['navpath'] = navpath
        context['title'] = create_title(navpath)
        context['available_reports'] = [DeviceAvailabilityReport,
                                        LinkAvailabilityReport]

        return context


class AvailabilityReportView(BusinessView):
    """View for the availability report"""
    template_name = 'business/report-availability.html'
    report_name = 'Dummy report'
    description = 'Dummy description'

    def get_context_data(self, **kwargs):
        context = super(AvailabilityReportView, self).get_context_data(**kwargs)

        if 'report-month' in self.request.GET:
            year, month = [int(x) for x in
                           self.request.GET.get('report-month').split('-')]
            sometime = datetime(year, month, 1)
            start, end = utils.get_interval(sometime)
            context['start'] = start
            context['end'] = end
            context['records'] = sorted(self.get_records(start, end),
                                        key=attrgetter('availability'))

        context['months'] = utils.get_months()
        context['report'] = self

        return context

    def get_records(self, start, end,
                    eventtype='boxState', alerttype='boxDown'):
        """Get records for the specified event and alert types"""
        from django.db.models import Q

        # Coarse filtering of alerts
        alerts = AlertHistory.objects.filter(
            event_type=eventtype, end_time__isnull=False,
            alert_type__name=alerttype).filter(
                Q(end_time__range=(start, end)) |
                Q(start_time__range=(start, end)) |
                  (Q(start_time__lte=start) & Q(end_time__gte=end)
               ))

        # Group alerts by subject
        grouped_alerts = self.group_alerts(alerts)

        # Create availability records for each subject
        return [utils.create_record(subject, alerts, start, end)
            for subject, alerts in grouped_alerts.items()]

    @staticmethod
    def group_alerts(alerts):
        """Group alerts by subject"""
        grouped_alerts = defaultdict(list)
        for alert in alerts:
            grouped_alerts[alert.netbox].append(alert)
        return grouped_alerts

    def get_url(self):
        """Get the url for this view"""
        raise NotImplementedError


class DeviceAvailabilityReport(AvailabilityReportView):
    """Availability for IP Devices"""
    report_name = 'Device Availability'
    description = 'Displays a report of IP Devices that ' \
                  'have less than 100% uptime.'

    def get_url(self):
        return reverse('business-report-device-availability')


class LinkAvailabilityReport(AvailabilityReportView):
    """Availability for links"""
    report_name = 'Link Availability'
    description = 'Displays a report of links that ' \
                  'have less than 100% uptime.'

    def get_url(self):
        return reverse('business-report-link-availability')

    def get_records(self, start, end, **_kwargs):
        """Gets all records regarding links for this period"""
        return super(LinkAvailabilityReport, self).get_records(
            start, end, 'linkState', 'linkDown')

    @staticmethod
    def group_alerts(alerts):
        grouped_alerts = defaultdict(list)
        for alert in alerts:
            try:
                interface = Interface.objects.get(pk=alert.subid)
            except Interface.DoesNotExist:
                continue
            else:
                grouped_alerts[interface].append(alert)

        return grouped_alerts
