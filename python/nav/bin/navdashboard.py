#!/usr/bin/env python
# -*- testargs: list -*-
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
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A command line interface to list, export and import NAV dashboards."""

import json
import sys
import argparse

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.models.profiles import Account, AccountDashboard
from nav.web.webfront.dashboard_io import (
    ConflictMode,
    ImportAction,
    import_from_dict,
    list_dashboards,
    validate_dashboard_data,
)


def main():
    """Main program"""
    args = parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


def parse_args():
    """Build an ArgumentParser and return parsed program arguments."""
    parser = argparse.ArgumentParser(
        description="List, export and import NAV dashboards",
    )
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    subparsers.required = True

    _add_list_parser(subparsers)
    _add_export_parser(subparsers)
    _add_import_parser(subparsers)

    args = parser.parse_args()
    if args.command == "export":
        _validate_export_args(parser, args)
    return args


def cmd_list(args):
    """List dashboards."""
    account = resolve_user(args.user, missing_ok=False) if args.user else None
    dashboards = list_dashboards(account=account)

    if args.format == "json":
        result = [
            {
                "id": d.id,
                "name": d.name,
                "account": d.account.login,
                "num_columns": d.num_columns,
                "is_shared": d.is_shared,
                "widget_count": d.widgets.count(),
            }
            for d in dashboards
        ]
        print(json.dumps(result, indent=2))
    else:
        rows = [(str(d.id), d.account.login, f'"{d.name}"') for d in dashboards]
        if rows:
            widths = [max(len(r[i]) for r in rows) for i in range(3)]
            for row in rows:
                print(f"{row[0]:>{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}")


def cmd_export(args):
    """Export a dashboard as JSON."""
    dashboard = find_dashboard_for_export(args)
    output = json.dumps(dashboard.to_json_dict(), indent=2, sort_keys=True)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
            f.write("\n")
        print(f"Exported to {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_import(args):
    """Import a dashboard from a JSON file."""
    account = resolve_user(args.user, missing_ok=args.missing_user_ok)
    if account is None:
        return

    if args.file == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.file) as f:
            data = json.load(f)

    if args.dry_run:
        validated = validate_dashboard_data(data)
        name = args.name if args.name else validated["name"]
        print(
            f"Dry run: would import dashboard {name!r} "
            f"with {len(validated['widgets'])} widgets "
            f"for user {account.login!r} "
            f"(on_conflict={args.on_conflict!r})",
            file=sys.stderr,
        )
        return

    result = import_from_dict(
        account,
        data,
        on_conflict=args.on_conflict,
        name_override=args.name,
    )

    if args.shared is not None:
        result.dashboard.is_shared = args.shared
        result.dashboard.save()

    action = _ACTION_LABELS[result.action]
    shared_note = " (shared)" if result.dashboard.is_shared else ""
    print(
        f"{action} dashboard {result.dashboard.name!r} "
        f"(id={result.dashboard.id}) "
        f"for user {account.login!r}{shared_note}",
        file=sys.stderr,
    )


_ACTION_LABELS = {
    ImportAction.CREATED: "Created",
    ImportAction.REPLACED: "Replaced",
    ImportAction.RENAMED: "Renamed and created",
}


def resolve_user(login, missing_ok=False):
    """Resolve a login name to an Account, or handle missing users."""
    try:
        return Account.objects.get(login=login)
    except Account.DoesNotExist:
        if missing_ok:
            print(f"Warning: user {login!r} does not exist", file=sys.stderr)
            return None
        print(f"Error: user {login!r} does not exist", file=sys.stderr)
        sys.exit(1)


def find_dashboard_for_export(args):
    """Resolve a dashboard for export by --id or --user/--name."""
    if args.id is not None:
        try:
            return AccountDashboard.objects.get(id=args.id)
        except AccountDashboard.DoesNotExist:
            print(
                f"Error: no dashboard with id {args.id}",
                file=sys.stderr,
            )
            sys.exit(1)

    account = resolve_user(args.user, missing_ok=args.missing_user_ok)
    if account is None:
        sys.exit(0)

    matches = AccountDashboard.objects.filter(account=account, name=args.name)
    count = matches.count()
    if count == 0:
        print(
            f"Error: no dashboard named {args.name!r} for user {account.login!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    if count > 1:
        print(
            f"Error: {count} dashboards named {args.name!r} "
            f"for user {account.login!r} (use --id to disambiguate)",
            file=sys.stderr,
        )
        sys.exit(1)
    return matches.first()


def _add_list_parser(subparsers):
    list_parser = subparsers.add_parser("list", help="List dashboards")
    list_parser.add_argument("--user", "-u", help="Filter by account login")
    list_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    list_parser.set_defaults(func=cmd_list)


def _add_export_parser(subparsers):
    export_parser = subparsers.add_parser(
        "export",
        help="Export a dashboard",
        description="Export by --id, or by --user/--name combo.",
    )
    export_parser.add_argument("--id", type=int, help="Dashboard ID")
    export_parser.add_argument("--user", "-u", help="Account login")
    export_parser.add_argument("--name", "-n", help="Dashboard name")
    export_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    export_parser.add_argument(
        "--missing-user-ok",
        action="store_true",
        help="Exit 0 with warning if user does not exist",
    )
    export_parser.set_defaults(func=cmd_export)


def _add_import_parser(subparsers):
    import_parser = subparsers.add_parser("import", help="Import a dashboard")
    import_parser.add_argument("--user", "-u", required=True, help="Account login")
    import_parser.add_argument(
        "--file", required=True, help="JSON file to import (use - for stdin)"
    )
    import_parser.add_argument(
        "--on-conflict",
        choices=[m.value for m in ConflictMode if m is not ConflictMode.CREATE_NEW],
        default=ConflictMode.ERROR.value,
        help="Conflict resolution (default: error)",
    )
    import_parser.add_argument("--name", "-n", help="Override dashboard name")
    import_parser.add_argument(
        "--missing-user-ok",
        action="store_true",
        help="Exit 0 with warning if user does not exist",
    )
    shared_group = import_parser.add_mutually_exclusive_group()
    shared_group.add_argument(
        "--shared",
        action="store_const",
        const=True,
        dest="shared",
        help="Make the imported dashboard public/shared",
    )
    shared_group.add_argument(
        "--no-shared",
        action="store_const",
        const=False,
        dest="shared",
        help="Make the imported dashboard private",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without modifying the database",
    )
    import_parser.set_defaults(func=cmd_import, shared=None)


def _validate_export_args(parser, args):
    """Validate export argument combinations."""
    if args.id is not None and (args.user or args.name):
        parser.error("--id cannot be combined with --user/--name")
    if args.id is None and not (args.user and args.name):
        parser.error("provide either --id or both --user and --name")


if __name__ == "__main__":
    main()
