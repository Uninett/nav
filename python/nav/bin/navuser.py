#!/usr/bin/env python
# -*- testargs: list -*-
#
# Copyright (C) 2016 Uninett AS
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
"""
A command line interface to list and modify NAV web user accounts
"""

import argparse
import copy
import sys
from getpass import getpass, getuser

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from django.db import transaction

from nav.auditlog.models import LogEntry
from nav.models.profiles import Account, AccountGroup


def main(argv=None):
    """Main program"""
    args = parse_args(argv)

    args.func(args)


def listusers(args):
    accounts = Account.objects.order_by('login')
    if args.verbose:
        longest1 = max(len(acc.login) for acc in accounts)
        longest2 = max(len(acc.name) for acc in accounts)
        msg = "{login:%ss}  {name:%ss}  {attrs}" % (longest1, longest2)
    else:
        msg = "{login}"

    for account in accounts:
        attrs = []
        if account.ext_sync:
            attrs.append(account.ext_sync)
        if not account.is_active:
            attrs.append('locked')
        attrs = '[%s]' % ','.join(attrs) if attrs else ''
        print(msg.format(login=account.login, name=account.name, attrs=attrs).strip())


def adduser(args):
    try:
        Account.objects.get(login=args.login)
        print("User %s already exists" % args.login, file=sys.stderr)
        sys.exit(1)
    except Account.DoesNotExist:
        pass

    account = Account(login=args.login, name=args.name)
    account.save()

    if args.admin:
        admin = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        admin.accounts.add(account)
        msg = "Admin user %s created"
    else:
        msg = "User %s created"

    _add_log_entry(
        verb='create-account',
        template='{actor} created {object}',
        after=account,
        object=account,
    )

    print(msg % args.login, file=sys.stderr)


@transaction.atomic
def removeuser(args):
    _add_log_entry(
        verb='delete-account',
        template='{actor} deleted {object}',
        before=args.login,
        object=args.login,
    )
    args.login.delete()
    print("User %s has been removed" % args.login.login, file=sys.stderr)


def adminify(args):
    action = args.action
    try:
        account = Account.objects.get(login=args.login)
    except Account.DoesNotExist:
        print("User %s does not exist" % args.login, file=sys.stderr)
        sys.exit(1)

    if action == 'add':
        admin = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        admin.accounts.add(account)
        msg = "User %s was made an admin" % args.login
        _add_log_entry(
            verb='edit-account-add-group',
            template='{actor} added user {object} to group {target}',
            target=admin,
            object=account,
        )
    elif action == 'remove':
        admin = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        admin.accounts.remove(account)
        msg = "User %s is no longer an admin" % args.login
        _add_log_entry(
            verb='edit-account-remove-group',
            template='{actor} removed user {object} from group {target}',
            target=admin,
            object=account,
        )
    else:
        msg = "Unknown argument %s" % action
    print(msg, file=sys.stderr)


def passwd(args):
    account = args.login

    if account.is_default_account():
        print(
            "It is not possible to set a password for the default account.",
            file=sys.stderr,
        )
        sys.exit(1)

    if sys.stdin.isatty():
        if account.password and not args.noverify:
            password = getpass('(current) NAV password: ', stream=sys.stderr)
            if not account.check_password(password):
                print("Authentication error", file=sys.stderr)
                sys.exit(1)

        password = getpass('Enter new NAV password: ', stream=sys.stderr)
        password2 = getpass('Retype new NAV password: ', stream=sys.stderr)
        if password2 != password:
            print("Sorry, passwords do not match", file=sys.stderr)
            sys.exit(2)
    else:
        password = sys.stdin.readline().strip('\n')

    if len(password) >= Account.MIN_PASSWD_LENGTH:
        old_account = copy.deepcopy(account)
        account.set_password(password)
        account.save()
        _add_log_entry(
            verb='edit-account-password',
            template='{actor} edited {account}: password changed',
            before=old_account,
            after=account,
            object=account,
        )
        print("New password saved", file=sys.stderr)
    else:
        print(
            "Password must be at least {} characters".format(Account.MIN_PASSWD_LENGTH),
            file=sys.stderr,
        )
        sys.exit(3)


def verify(args):
    account = args.login
    if sys.stdin.isatty():
        try:
            password = getpass('Password: ', stream=sys.stderr)
        except KeyboardInterrupt:
            sys.exit("Interrupted")
    else:
        password = sys.stdin.readline().strip('\n')

    if not account.check_password(password):
        sys.exit("Password could not be verified")


def lock(args):
    if not args.login.is_active:
        print("Cannot lock %s, already locked" % args.login.login, file=sys.stderr)
        sys.exit(1)

    args.login.is_active = False
    args.login.save()
    _add_log_entry(
        verb='lock-account',
        template='{actor} locked {object}',
        after=args.login,
        object=args.login,
    )
    print("User %s locked" % args.login.login, file=sys.stderr)


def unlock(args):
    if args.login.is_active:
        print("Cannot unlock %s, already unlocked" % args.login.login, file=sys.stderr)
        sys.exit(1)

    args.login.is_active = True
    args.login.save()
    _add_log_entry(
        verb='unlock-account',
        template='{actor} unlocked {object}',
        after=args.login,
        object=args.login,
    )
    print("User %s unlocked" % args.login.login, file=sys.stderr)


##########################
#                        #
# Other helper functions #
#                        #
##########################


def usergetter(login):
    try:
        return Account.objects.get(login=login)
    except Account.DoesNotExist:
        raise argparse.ArgumentTypeError("No such user account: %s" % login)


def _add_log_entry(verb: str, template: str, **kwargs):
    actor = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    navuser_user = getuser()
    template = f"{template} ({navuser_user} via navuser)"
    LogEntry.add_log_entry(actor=actor, verb=verb, template=template, **kwargs)


def parse_args(argv=None):
    """Builds an ArgumentParser and returns parsed program arguments"""
    parser = argparse.ArgumentParser(
        description="Lists and manipulates NAV web user accounts"
    )
    subparsers = parser.add_subparsers(help='sub-command help', dest="command")
    subparsers.required = True

    listparser = subparsers.add_parser('list', help='Lists user accounts')
    listparser.add_argument(
        '--verbose', '-v', action='store_true', help="Be verbose about it"
    )
    listparser.set_defaults(func=listusers)

    passwdparser = subparsers.add_parser(
        'passwd', help='Sets the password of a user account'
    )
    passwdparser.add_argument(
        'login', type=usergetter, help="The login name of the user"
    )
    passwdparser.add_argument(
        '--noverify', '-n', action='store_true', help="Do not verify existing password"
    )
    passwdparser.set_defaults(func=passwd)

    verifyparser = subparsers.add_parser(
        'verify', help='Verifies the password of a user account'
    )
    verifyparser.add_argument(
        'login', type=usergetter, help="The login name of the user"
    )
    verifyparser.set_defaults(func=verify)

    addparser = subparsers.add_parser('add', help='Adds a new user account')
    addparser.add_argument('login', help="The login name of the user")
    addparser.add_argument('--name', '-n', default='', help="The full name of the user")
    addparser.add_argument(
        '--admin', action='store_true', help="Give the user full admin access"
    )
    addparser.set_defaults(func=adduser)

    removeparser = subparsers.add_parser('remove', help='Removes a user')
    removeparser.set_defaults(func=removeuser)
    removeparser.add_argument(
        'login', type=usergetter, help="The login name of the user"
    )

    adminifyparser = subparsers.add_parser(
        'admin', help='Sets whether an existing user belongs to the admin group'
    )
    adminifyparser.add_argument('login', help="The login name of the user")
    adminifyparser.set_defaults(func=adminify)
    adminifygroupparser = adminifyparser.add_mutually_exclusive_group(required=True)
    adminifygroupparser.add_argument(
        '-a',
        '--add',
        dest='action',
        help='Add the user to the admin group',
        action='store_const',
        const='add',
    )
    adminifygroupparser.add_argument(
        '-r',
        '--remove',
        dest='action',
        help='Remove the user from the admin group',
        action='store_const',
        const='remove',
    )

    lockparser = subparsers.add_parser('lock', help='Locks a user')
    lockparser.set_defaults(func=lock)
    lockparser.add_argument('login', type=usergetter, help="The login name of the user")

    unlockparser = subparsers.add_parser('unlock', help='Unlocks a user')
    unlockparser.set_defaults(func=unlock)
    unlockparser.add_argument(
        'login', type=usergetter, help="The login name of the user"
    )

    return parser.parse_args(argv)


if __name__ == '__main__':
    main()
