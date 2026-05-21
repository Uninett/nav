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
    # version is reserved for forward compatibility; currently always 1
    "version": int,
}

WIDGET_FIELDS = {
    "navlet": str,
    "column": int,
    "preferences": dict,
    "order": int,
}


class ConflictMode(str, enum.Enum):
    """Strategy for resolving name collisions during dashboard import."""

    ERROR = "error"
    REPLACE = "replace"
    RENAME = "rename"
    CREATE_NEW = "create_new"


class ImportAction(str, enum.Enum):
    """Describes what an import operation actually did."""

    CREATED = "created"
    REPLACED = "replaced"
    RENAMED = "renamed"


@dataclass
class ImportResult:
    """Result of an import operation."""

    dashboard: AccountDashboard
    action: ImportAction


class DashboardConflictError(ValueError):
    """Raised when a dashboard name conflict prevents import."""


def validate_dashboard_data(data):
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
def import_from_dict(account, data, on_conflict=ConflictMode.ERROR, name_override=None):
    """Import a dashboard from a data dict.

    Args:
        account: The Account that will own the dashboard.
        data: Dashboard data dict (as produced by ``to_json_dict()``).
        on_conflict: Conflict resolution strategy when a dashboard with the
            same name already exists for the account.
        name_override: If given, use this name instead of the one in *data*.

    Returns:
        An ``ImportResult`` with the dashboard and the action taken.
    """
    data = validate_dashboard_data(data)
    name = name_override if name_override is not None else data["name"]

    dashboard, action = _resolve_or_create_dashboard(
        account, name, data["num_columns"], on_conflict
    )
    _create_widgets(dashboard, account, data["widgets"])
    return ImportResult(dashboard=dashboard, action=action)


def list_dashboards(account=None):
    """Return a queryset of dashboards, optionally filtered by account."""
    qs = AccountDashboard.objects.select_related("account").order_by(
        "account__login", "id"
    )
    if account is not None:
        qs = qs.filter(account=account)
    return qs


def _resolve_or_create_dashboard(account, name, num_columns, on_conflict):
    """Find or create the target dashboard based on the conflict strategy.

    Returns a (dashboard, action) tuple.
    """
    on_conflict = ConflictMode(on_conflict)

    if on_conflict is ConflictMode.CREATE_NEW:
        return _create_dashboard(account, name, num_columns), ImportAction.CREATED

    if on_conflict is ConflictMode.RENAME:
        original_name = name
        name = _find_unique_name(account, name)
        action = ImportAction.RENAMED if name != original_name else ImportAction.CREATED
        return _create_dashboard(account, name, num_columns), action

    existing = AccountDashboard.objects.filter(account=account, name=name)
    count = existing.count()

    if on_conflict is ConflictMode.ERROR:
        if count > 0:
            raise DashboardConflictError(
                f"Dashboard {name!r} already exists for user {account.login!r}"
            )
        return _create_dashboard(account, name, num_columns), ImportAction.CREATED

    # ConflictMode.REPLACE
    if count == 0:
        return _create_dashboard(account, name, num_columns), ImportAction.CREATED
    if count > 1:
        raise DashboardConflictError(
            f"Ambiguous: {count} dashboards named {name!r} "
            f"exist for user {account.login!r}"
        )
    dashboard = existing.first()
    dashboard.num_columns = num_columns
    dashboard.save()
    dashboard.widgets.all().delete()
    return dashboard, ImportAction.REPLACED


def _create_dashboard(account, name, num_columns):
    """Create a new dashboard row."""
    dashboard = AccountDashboard(
        account=account,
        name=name,
        num_columns=num_columns,
    )
    dashboard.save()
    return dashboard


def _create_widgets(dashboard, account, widgets):
    """Create widget rows for a dashboard."""
    for widget in widgets:
        AccountNavlet.objects.create(
            dashboard=dashboard,
            account=account,
            **widget,
        )


def _find_unique_name(account, name):
    """Append a numeric suffix to make the name unique for this account."""
    if not AccountDashboard.objects.filter(account=account, name=name).exists():
        return name
    counter = 2
    while True:
        candidate = f"{name} ({counter})"
        exists = AccountDashboard.objects.filter(
            account=account, name=candidate
        ).exists()
        if not exists:
            return candidate
        counter += 1
