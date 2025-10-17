"""Controllers for business tool"""

from collections import defaultdict
from datetime import datetime
import logging
from operator import attrgetter

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.urls import reverse

from nav.models.profiles import AlertAddress, ReportSubscription, AlertSender
from nav.web.business import utils
from nav.web.auth.utils import get_account
from nav.web.utils import create_title

_logger = logging.getLogger(__name__)


class BusinessView(TemplateView):
    """A default business view"""

    template_name = 'business/base.html'
    report_name = ''

    def get_context_data(self, **kwargs):
        """Creates a common context for business pages"""
        context = super(BusinessView, self).get_context_data(**kwargs)
        navpath = [('Home', '/'), ('Business reports', reverse('business-index'))]

        if self.report_name:
            navpath.append((self.report_name,))

        context['navpath'] = navpath
        context['title'] = create_title(navpath)
        context['available_reports'] = [
            DeviceAvailabilityReport,
            LinkAvailabilityReport,
        ]
        context['subscription_periods'] = ReportSubscription.PERIODS
        context['report_types'] = ReportSubscription.TYPES

        return context


class AvailabilityReportView(BusinessView):
    """View for the availability report"""

    template_name = 'business/report-availability.html'
    report_name = 'Dummy report'
    description = 'Dummy description'

    def get_context_data(self, **kwargs):
        context = super(AvailabilityReportView, self).get_context_data(**kwargs)

        if 'report-month' in self.request.GET:
            year, month = [
                int(x) for x in self.request.GET.get('report-month').split('-')
            ]
            sometime = datetime(year, month, 1)
            start, end = utils.get_interval(sometime, ReportSubscription.MONTH)
            context['start'] = start
            context['end'] = end
            context['records'] = sorted(
                self.get_records(start, end), key=attrgetter('availability')
            )

        context['months'] = utils.get_months()
        context['report'] = self
        context['exclude_maintenance'] = self.exclude_maintenance()

        return context

    def exclude_maintenance(self):
        return bool(self.request.GET.get('exclude_maintenance'))

    def get_records(self, start, end):
        """Get records for the specified event and alert types"""
        raise NotImplementedError

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
    description = 'Displays a report of IP Devices that have less than 100% uptime.'

    def get_url(self):
        return reverse('business-report-device-availability')

    def get_records(self, start, end):
        """Get records for the specified event and alert types"""
        return utils.get_netbox_records(start, end, self.exclude_maintenance())


class LinkAvailabilityReport(AvailabilityReportView):
    """Availability for links"""

    report_name = 'Link Availability'
    description = 'Displays a report of links that have less than 100% uptime.'

    def get_url(self):
        return reverse('business-report-link-availability')

    def get_records(self, start, end):
        """Gets all records regarding links for this period"""
        return utils.get_interface_records(start, end)


def save_report_subscription(request):
    """Saves a report subscription"""

    new_address = request.POST.get('new_address')
    period = request.POST.get('period')
    report_type = request.POST.get('report_type')
    exclude_maintenance = bool(request.POST.get('exclude_maintenance'))
    account = get_account(request)

    if new_address:
        email_sender = AlertSender.objects.get(name=AlertSender.EMAIL)
        address = AlertAddress(account=account, type=email_sender, address=new_address)
        address.save()
    else:
        address = get_object_or_404(AlertAddress, pk=int(request.POST.get('address')))

    ReportSubscription(
        account=account,
        address=address,
        period=period,
        exclude_maintenance=exclude_maintenance,
        report_type=report_type,
    ).save()

    return HttpResponse()


def render_report_subscriptions(request):
    """Renders the report subscriptions"""
    return render(request, 'business/frag-report-items.html')


def remove_report_subscription(request):
    """Remove a report subscription"""
    account = get_account(request)
    subscription_id = request.POST.get('subscriptionId')
    subscription = get_object_or_404(
        ReportSubscription, account=account, pk=subscription_id
    )
    subscription.delete()

    return HttpResponse()
