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
"""Script to view the auditlog and repair known problems"""

import argparse
import sys
from textwrap import wrap

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.auditlog.models import LogEntry
from nav.auditlog.utils import get_all_historical_actors, get_lurkers, get_zombies
from nav.models.profiles import Account


def register_argument(registry, name, description, function):
    registry[name] = {'description': description, "function": function}


def list_registered_commands(registry):
    "List registered commands in given registry"
    for key, value in registry.items():
        print(f"{key}:")
        for line in wrap(
            value['description'],
            initial_indent="\t",
            subsequent_indent="\t",
            break_long_words=False,
        ):
            print(line)

        print()


KNOWN_REPORTS = {}
KNOWN_REPAIRS = {}


def main():
    """Main script controller"""
    parser = create_parser()
    args = parser.parse_args()

    if args.subcommand == "view":
        if args.list:
            list_registered_commands(KNOWN_REPORTS)
        elif args.report in KNOWN_REPORTS:
            view = KNOWN_REPORTS[args.report]["function"]
            view()
        else:
            parser.parse_args(["view", "-h"])
            sys.exit(1)
        return

    if args.subcommand == "fix":
        if args.list:
            list_registered_commands(KNOWN_REPAIRS)
        elif args.repair in KNOWN_REPAIRS:
            repair = KNOWN_REPAIRS[args.problem]["function"]
            repair()
        else:
            parser.parse_args(["fix", "-h"])
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


def create_parser():
    """Create a parser for the script arguments"""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(title='subcommands', dest="subcommand")
    view = subparsers.add_parser("view")
    view_group = view.add_mutually_exclusive_group()
    view_group.add_argument(
        '-l', '--list', action="store_true", help="list and describe available reports"
    )
    view_group.add_argument(
        "-r",
        "--report",
        help="Generate and print the named report",
        choices=KNOWN_REPORTS.keys(),
    )

    fix = subparsers.add_parser("fix")
    fix_group = fix.add_mutually_exclusive_group()
    fix_group.add_argument(
        '-l', '--list', action="store_true", help="list and describe available fixes"
    )
    fix_group.add_argument(
        '-r',
        '--report',
        help="fix the named problem",
        choices=KNOWN_REPAIRS.keys(),
    )
    return parser


# commands, view


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


register_argument(
    KNOWN_REPORTS,
    "dump",
    (
        "Dump details of verb, actor, object, target and summary, "
        "suitable for further processing"
    ),
    view_dump,
)


def view_lurkers():
    "Print list of current accounts that have no entries in the audit log"
    lurkers = get_lurkers()
    print("Lurkers:", lurkers.count())
    for lurker in lurkers:
        print("*", lurker.login)


register_argument(
    KNOWN_REPORTS,
    "lurkers",
    (
        "List currently existing accounts that have not done anything "
        "in this NAV instance"
    ),
    view_lurkers,
)


def view_zombies():
    """Print list of still existing accounts that have been deleted according to
    the auditlog.
    """
    zombies = get_zombies()
    print("zombies:", zombies.count())
    for zombie in zombies:
        print("*", zombie.pk, zombie.login)


register_argument(
    KNOWN_REPORTS,
    "zombies",
    (
        "List currently existing accounts that according to the audit log "
        "should no longer exist."
    ),
    view_zombies,
)


# commands, fix


def _find_unused_ids():
    # Assumes actors are accounts
    account_ids = set(Account.objects.values_list('id', flat=True))
    actor_ids = set([int(_id) for _, _id in get_all_historical_actors()])
    used_ids = account_ids | actor_ids
    max_id = max(used_ids)
    all_ids = range(1, max_id + 1)
    free_ids = sorted(all_ids - actor_ids)
    return free_ids


def repair_delete_account_entries(verbose: bool = True):
    """Add back missing pk to malformed delete-account entries

    "Lurkers" are accounts that have no entries in the actor-column.
    Their pk's are faked because there is no way to recover them.
    """
    actors = dict(get_all_historical_actors())
    deleted_account_logentries = LogEntry.objects.filter(
        verb="delete-account", object_pk__isnull=True
    )
    deleted_count = deleted_account_logentries.count()
    if verbose and deleted_count:
        print(f"Will fix {deleted_count} entries")
    leftovers = []
    for entry in deleted_account_logentries:
        objname = entry.summary.rsplit(' ', 1)[-1]  # final word in line
        if objname in actors:
            entry.object_pk = actors[objname]
            entry.save()
            if verbose:
                print(f'Fixed: {entry.id} "{entry.summary}"')
        else:
            leftovers.append(entry)

    free_ids = _find_unused_ids()
    for entry in leftovers:
        entry.object_pk = str(free_ids.pop(0))
        entry.save()
        if verbose:
            print(f'Fixed: {entry.id} "{entry.summary}" (lurker)')


register_argument(
    KNOWN_REPAIRS,
    "delete-account-fix-object",
    (
        "For delete-account entries:\n"
        "Attempts to set the pk of the object if it is missing"
    ),
    repair_delete_account_entries,
)


def delete_account_remove_zombies():
    "Delete accounts have an entry in the object column of delete-account"
    zombies = get_zombies()
    zombies.delete()


register_argument(
    KNOWN_REPAIRS,
    "delete-account-remove-zombies",
    (
        "For delete-account entries:\n"
        "Actually delete accounts that have a delete-account entry "
        "but for some reason still exists"
    ),
    delete_account_remove_zombies,
)


if __name__ == '__main__':
    main()
