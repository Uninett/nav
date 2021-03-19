#
# Copyright (C) 2012 (SD -311000) Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Urlconfig for arnold"""

from django.conf.urls import url
from nav.web.arnold import views


urlpatterns = [
    url(r"^$", views.render_detained_ports, name="arnold_index"),
    url(r"^history/$", views.render_history, name="arnold-history"),
    url(r"^details/(?P<did>\d+)$", views.render_details, name="arnold-details"),
    url(r"^detainedports/$", views.render_detained_ports, name="arnold-detainedports"),
    url(r"^search/$", views.render_search, name="arnold-search"),
    url(
        r"^manualdetention/$",
        views.render_manual_detention_step_one,
        name="arnold-manual-detention",
    ),
    url(
        r"^manualdetention/(?P<target>[^/]+)$",
        views.render_manual_detention_step_two,
        name="arnold-manual-detention-step-two",
    ),
    url(
        r"^enable/(?P<did>\d+)$",
        views.choose_detentions,
        name="arnold-choose-detentions",
    ),
    url(r"^doenable/$", views.lift_detentions, name="arnold-lift-detentions"),
    url(
        r"^predefined/$",
        views.render_detention_profiles,
        name="arnold-detention-profiles",
    ),
    url(
        r"^predefined/add$",
        views.render_edit_detention_profile,
        name="arnold-detention-profile-add",
    ),
    url(
        r"^predefined/edit/(?P<did>\d+)$",
        views.render_edit_detention_profile,
        name="arnold-detention-profile-edit",
    ),
    url(r"^addreason/$", views.render_justifications, name="arnold-justificatons"),
    url(
        r"^addreason/edit/(?P<jid>\d+)$",
        views.render_justifications,
        name="arnold-justificatons-edit",
    ),
    url(
        r"^addreason/delete/(?P<jid>\d+)$",
        views.delete_justification,
        name="arnold-justificatons-delete",
    ),
    url(
        r"^addquarantinevlan/$",
        views.render_quarantine_vlans,
        name="arnold-quarantinevlans",
    ),
    url(
        r"^addquarantinevlan/edit/(?P<qid>\d+)$",
        views.render_quarantine_vlans,
        name="arnold-quarantinevlans-edit",
    ),
]
