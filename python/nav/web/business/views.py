"""Controllers for business tool"""

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

import calendar
from datetime import datetime, timedelta

from nav.web.utils import create_title
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
            start, end = self.get_interval(sometime)
            context['start'] = start
            context['end'] = end
            context['alerts'] = self.get_alerts(start, end)

        context['months'] = self.get_months()

        return context


    @staticmethod
    def get_interval(sometime, _interval='month'):
        """Get the interval for the report

        :param sometime: A datetime.datetime object
        :param interval: A string to indicate interval
        :returns: The start and endtime for the interval
        :rtype: datetime.datetime, datetime.datetime
        """
        year = sometime.year
        month = sometime.month
        _day, days = calendar.monthrange(year, month)
        start = datetime(year, month, 1)
        end = (datetime(year, month, days) + timedelta(days=1)
               - timedelta(seconds=1))
        return start, end


    @staticmethod
    def get_months(number_of_months=12):
        """Returns a list of datetime objects for each month

        The date is set to the first date in the month.
        The first date is the previous months first day

        :rtype: list[datetime.datetime]
        """
        now = datetime.now()
        month = datetime(now.year, now.month, 1)
        months = []
        for _ in range(number_of_months):
            month = (month - timedelta(days=1)).replace(day=1)
            months.append(month)

        return months

    @staticmethod
    def get_alerts(start, end):
        """Get all alerts to filter on"""
        from django.db.models import Q

        return AlertHistory.objects.filter(
            event_type='boxState', end_time__isnull=False,
            alert_type__name='boxDown').filter(
                Q(end_time__range=(start, end)) |
                Q(start_time__range=(start, end)))
