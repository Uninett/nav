#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Shared import/export logic for NAV dashboards."""

import enum
from dataclasses import dataclass

from django.db import transaction

from nav.models.profiles import AccountDashboard, AccountNavlet

DASHBOARD_FIELDS = {
    "name": str,
    "num_columns": int,
    "widgets": list,
    "version": int,
}

WIDGET_FIELDS = {
    "navlet": str,
    "column": int,
    "preferences": dict,
    "order": int,
}


class ImportAction(str, enum.Enum):
    """Describes what an import operation actually did."""

    CREATED = "created"


@dataclass
class ImportResult:
    """Result of an import operation."""

    dashboard: AccountDashboard
    action: ImportAction


def validate_dashboard_data(data: dict):
    """Validate and sanitize dashboard data from a JSON dict.

    Returns a sanitized copy of the data with unknown keys removed.
    Raises ValueError if the data is invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Dashboard data must be a dict")

    for field, dtype in DASHBOARD_FIELDS.items():
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(data[field], dtype):
            raise ValueError(
                f"Field {field!r} must be {dtype.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    if not data["name"].strip():
        raise ValueError("Dashboard name must not be empty")

    sanitized_widgets = []
    for i, widget in enumerate(data["widgets"]):
        if not isinstance(widget, dict):
            raise ValueError(f"Widget {i} must be a dict")
        for field, dtype in WIDGET_FIELDS.items():
            if field not in widget:
                raise ValueError(f"Widget {i} missing required field: {field}")
            if not isinstance(widget[field], dtype):
                raise ValueError(
                    f"Widget {i} field {field!r} must be {dtype.__name__}, "
                    f"got {type(widget[field]).__name__}"
                )
        if widget["column"] < 1 or widget["column"] > data["num_columns"]:
            raise ValueError(
                f"Widget {i} column {widget['column']} out of range "
                f"(1..{data['num_columns']})"
            )
        sanitized = {k: v for k, v in widget.items() if k in WIDGET_FIELDS}
        sanitized_widgets.append(sanitized)

    return {
        "name": data["name"],
        "num_columns": data["num_columns"],
        "widgets": sanitized_widgets,
        "version": data["version"],
    }


@transaction.atomic
def import_from_dict(account, data):
    """Import a dashboard from a data dict, always creating a new dashboard.

    Args:
        account: The Account that will own the dashboard.
        data: Dashboard data dict (as produced by ``to_json_dict()``).

    Returns:
        An ``ImportResult`` with the dashboard and the action taken.
    """
    data = validate_dashboard_data(data)

    dashboard = AccountDashboard(
        account=account,
        name=data["name"],
        num_columns=data["num_columns"],
    )
    dashboard.save()
    for widget in data["widgets"]:
        AccountNavlet.objects.create(
            dashboard=dashboard,
            account=account,
            **widget,
        )
    return ImportResult(dashboard=dashboard, action=ImportAction.CREATED)
