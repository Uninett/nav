#
# Copyright (C) 2012 (SD -311000) Uninett AS
# Copyright (C) 2022 Sikt
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

from django.urls import path
from nav.web.arnold import views


urlpatterns = [
    path("", views.render_detained_ports, name="arnold_index"),
    path("history/", views.render_history, name="arnold-history"),
    path("details/<int:did>", views.render_details, name="arnold-details"),
    path("detainedports/", views.render_detained_ports, name="arnold-detainedports"),
    path("search/", views.render_search, name="arnold-search"),
    path(
        "manualdetention/",
        views.render_manual_detention_step_one,
        name="arnold-manual-detention",
    ),
    path(
        "manualdetention/<str:target>",
        views.render_manual_detention_step_two,
        name="arnold-manual-detention-step-two",
    ),
    path(
        "enable/<int:did>",
        views.choose_detentions,
        name="arnold-choose-detentions",
    ),
    path("doenable/", views.lift_detentions, name="arnold-lift-detentions"),
    path(
        "predefined/",
        views.render_detention_profiles,
        name="arnold-detention-profiles",
    ),
    path(
        "predefined/add",
        views.render_edit_detention_profile,
        name="arnold-detention-profile-add",
    ),
    path(
        "predefined/edit/<int:did>",
        views.render_edit_detention_profile,
        name="arnold-detention-profile-edit",
    ),
    path("addreason/", views.render_justifications, name="arnold-justifications"),
    path(
        "addreason/edit/<int:jid>",
        views.render_justifications,
        name="arnold-justifications-edit",
    ),
    path(
        "addreason/delete/<int:jid>",
        views.delete_justification,
        name="arnold-justifications-delete",
    ),
    path(
        "addquarantinevlan/",
        views.render_quarantine_vlans,
        name="arnold-quarantinevlans",
    ),
    path(
        "addquarantinevlan/edit/<int:qid>",
        views.render_quarantine_vlans,
        name="arnold-quarantinevlans-edit",
    ),
]
