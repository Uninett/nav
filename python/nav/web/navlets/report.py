#
# Copyright (C) 2015 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Report widget"""

from django.http import HttpResponse, JsonResponse, QueryDict
from nav.models.profiles import AccountNavlet
from nav.web.auth.utils import get_account
from nav.web.report.views import CONFIG_DIR, make_report
from nav.report.generator import ReportList
from nav.config import list_config_files_from_dir
from . import Navlet, NAVLET_MODE_EDIT, NAVLET_MODE_VIEW


class ReportWidget(Navlet):
    """Widget for displaying a report"""

    title = "Report"
    description = "Shows a report"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    is_editable = True

    def get_template_basename(self):
        return "report"

    def get_context_data(self, **kwargs):
        context = super(ReportWidget, self).get_context_data(**kwargs)
        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        report_id = navlet.preferences.get('report_id')
        query_string = navlet.preferences.get('query_string')

        if self.mode == NAVLET_MODE_EDIT:
            report_list = ReportList(
                list_config_files_from_dir(CONFIG_DIR)
            ).get_report_list()

            context['report_list'] = report_list
            context['current_report_id'] = report_id
            context['query_string'] = query_string
        elif self.mode == NAVLET_MODE_VIEW:
            full_context = make_report(
                self.request,
                report_id,
                None,
                QueryDict(query_string).copy(),
                paginate=False,
            )
            if full_context:
                report = full_context.get('report')
                context['report'] = report
                context['page'] = report.table.rows

        return context

    def post(self, request):
        """Save navlet options on post"""
        try:
            account = get_account(request)
            navlet = AccountNavlet.objects.get(pk=self.navlet_id, account=account)
        except AccountNavlet.DoesNotExist:
            return HttpResponse(status=404)
        else:
            navlet.preferences['report_id'] = request.POST.get('report_id')
            navlet.preferences['query_string'] = request.POST.get('query_string')
            navlet.save()
            return JsonResponse(navlet.preferences)


def get_report_names():
    """Get all report names"""
