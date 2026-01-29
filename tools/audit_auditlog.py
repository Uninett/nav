#!/usr/bin/env python3
#
# Copyright (C) 2026 Sikt
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
"""Script to simulate up/down events from pping"""

import argparse
import sys

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.auditlog.models import LogEntry
from nav.models.profiles import Account


def main():
    """Main script controller"""
    parser = create_parser()
    args = parser.parse_args()

    if args.subcommand == "view":
        if args.lurkers:
            view_lurkers()
        elif args.dump:
            view_dump()
        else:
            parser.parse_args(["view", "-h"])
            sys.exit(1)
        return

    if args.subcommand == "fix":
        if args.list:
            list_available_fixes()
        elif args.problem == "delete-account":
            repair_delete_account()
        else:
            parser.parse_args(["fix", "-h"])
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


def create_parser():
    """Create a parser for the script arguments"""
    parser = argparse.ArgumentParser(
        description='Script to fix traces of deleted accounts in auditlog'
    )
    subparsers = parser.add_subparsers(title='subcommands', dest="subcommand")
    view = subparsers.add_parser("view")
    view_group = view.add_mutually_exclusive_group()
    view_group.add_argument(
        "--dump",
        action="store_true",
        help=(
            "dump details of verb, actor, object, target and summary, "
            "suitable for further processing"
        ),
    )
    view_group.add_argument(
        "--lurkers",
        action="store_true",
        help=(
            "list currently exising accounts that have not done anything "
            "in this NAV instance"
        ),
    )
    fix = subparsers.add_parser("fix")
    fix_group = fix.add_mutually_exclusive_group()
    fix_group.add_argument(
        '-l', '--list', action="store_true", help="list available fixes"
    )
    fix_group.add_argument('-p', '--problem', help="fix the named problem")
    return parser


# commands


def view_dump():
    "Print dump suitable for further processing"
    verbs = LogEntry.objects.values_list("verb", flat=True).distinct()
    for verb in verbs:
        entries = LogEntry.objects.filter(verb=verb).order_by('actor_model', 'actor_pk')
        for entry in entries:
            actor = tuple(
                filter(lambda x: x is not None, (entry.actor_model, entry.actor_pk))
            )
            obj = tuple(
                filter(lambda x: x is not None, (entry.object_model, entry.object_pk))
            )
            target = tuple(
                filter(lambda x: x is not None, (entry.target_model, entry.target_pk))
            )
            print(
                f"{verb}: actor {actor}, object {obj}, target {target} "
                f"'{entry.summary}'"
            )


def view_lurkers():
    "Print list of current accounts that have no entries in the audit log"
    actor_pks = [pk for _, pk in get_all_historical_actors()]
    lurkers = Account.objects.exclude(pk__in=actor_pks)
    print("Accounts:", len(actor_pks))
    print("Lurkers:", lurkers.count())
    for lurker in lurkers:
        print("*", lurker.login)


def list_available_fixes():
    "List avaliable fixes"
    print("delete-account: Attempts to set the pk of the object if it is missing")


def repair_delete_account(verbose=True):
    "Add back missing pk to malformed delete-account entries"
    actors = dict(get_all_historical_actors())
    deleted_account_logentries = LogEntry.objects.filter(
        verb="delete-account", object_pk__isnull=True
    )
    lurkers = set()
    for entry in deleted_account_logentries:
        objname = entry.summary.rsplit(' ', 1)[-1]
        if objname in actors:
            entry.object_pk = actors[objname]
            entry.save()
            print(f'Fixed: {entry.id} "{entry.summary}"')
        else:
            lurkers.add(objname)
    if verbose and lurkers:
        print("The following deleted accounts never did anything on this NAV instance:")
        for lurker in lurkers:
            print("*", lurker)


# helpers


def get_all_historical_actors():
    "List all recorded actors (need not be accounts!), including deleted ones"
    actors = set()
    for pk, summary in LogEntry.objects.values_list("actor_pk", "summary").distinct():
        name = summary.split(' ', 1)[0].strip(':')
        actors.add((name, pk))
    return sorted(actors)


if __name__ == '__main__':
    main()
