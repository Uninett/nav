#
# Copyright (C) 2006, 2013 Uninett AS
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
"""The smsd queue for the NAV database.

This smsd queue takes care of all communication between smsd and the NAV
database. Replacing the NAV database with some other queue/input should be
possible by implementing the interface seen in this class.

Generally, a phone number is a user and vice versa.

"""

import logging
import sys

import nav.db


class NAVDBQueue(object):
    """The smsd queue for the NAV database."""

    def __init__(self):
        # Create logger
        self.logger = logging.getLogger("nav.smsd.queue")

        # Open DB connection early so we can detect errors early
        try:
            self._connect()
        except Exception as error:  # noqa: BLE001
            self.logger.exception("Queue failed to initialize. Exiting. (%s)", error)
            sys.exit(1)

    def cancel(self, minage='0'):
        """
        Mark all unsent messages as ignored.

        Input:
            minage  Minimum age required for canceling message, default '0'.
                    Format as PostgreSQL interval type, e.g. '1 day 12 hours'.

        Returns number of messages canceled.
        """

        dbconn = self._connect()
        db = dbconn.cursor()

        data = dict(minage=str(minage))

        # Test minage
        if minage != '0':
            sql = "SELECT interval %(minage)s"
            try:
                db.execute(sql, data)
            except nav.db.driver.ProgrammingError:
                self.logger.warning(
                    "'autocancel' value (%s) is not valid. "
                    + "Check config for errors.",
                    minage,
                )
                return 0
            except Exception:  # noqa: BLE001
                self.logger.exception(
                    "Unknown exception caught in " + "cancel(). Exiting."
                )
                sys.exit(1)

        # Ignore messages
        sql = """UPDATE smsq SET sent = 'I'
            WHERE sent = 'N' AND time < now() - interval %(minage)s"""
        db.execute(sql, data)
        dbconn.commit()

        return db.rowcount

    def getusers(self, sent='N'):
        """
        Get users which has messages with given sent status (normally unsent).

        Returns a sorted list with the phone numbers for all users with
        messages with given sent status.
        """

        users = []
        dbconn = self._connect()
        db = dbconn.cursor()

        data = dict(sent=sent)
        sql = """SELECT DISTINCT phone
            FROM smsq
            WHERE sent = %(sent)s
            ORDER BY phone"""
        db.execute(sql, data)
        result = db.fetchall()
        # Rollback so we don't have old open transactions which foobars the
        # usage of now() in setsentstatus()
        dbconn.rollback()

        # Create a simple list without the tuples
        for row in result:
            users.append(row[0])

        return users

    def getusermsgs(self, user, sent='N'):
        """
        Get the user's messages which has given sent status (normally unsent).

        Returns a list of messsages ordered with the most severe first. Each
        message is a tuple with the ID, text, and severity of the message.
        """

        dbconn = self._connect()
        db = dbconn.cursor()

        data = dict(phone=user, sent=sent)
        sql = """SELECT id, msg, severity
            FROM smsq
            WHERE phone = %(phone)s AND sent = %(sent)s
            ORDER BY severity ASC, time ASC"""
        db.execute(sql, data)
        result = db.fetchall()
        # Rollback so we don't have old open transactions which foobars the
        # usage of now() in setsentstatus()
        dbconn.rollback()

        return result

    def getmsgs(self, sent='N'):
        """
        Get all messages with given sent status (normally unsent).

        Returns a list of dictionaries containing messages details of SMS in
        queue with the specified status.
        """

        dbconn = self._connect()
        db = dbconn.cursor()

        data = dict(sent=sent)
        sql = """SELECT smsq.id as smsqid, name, msg, time
            FROM smsq
            JOIN account ON (account.id = smsq.accountid)
            WHERE sent = %(sent)s ORDER BY time ASC"""
        db.execute(sql, data)

        result = []
        for smsqid, name, msg, time in db.fetchall():
            result.append(
                dict(
                    id=smsqid, name=name, msg=msg, time=time.strftime("%Y-%m-%d %H:%M")
                )
            )

        # Rollback so we don't have old open transactions which foobars the
        # usage of now() in setsentstatus()
        dbconn.rollback()

        return result

    def setsentstatus(self, identifier, sent, smsid=0):
        """
        Set the sent status of a message given ID and status.

        Returns number of messages changed.
        """

        dbconn = self._connect()
        db = dbconn.cursor()

        if sent == 'Y' or sent == 'I':
            sql = """UPDATE smsq
                SET sent = %(sent)s, smsid = %(smsid)s, timesent = now()
                WHERE id = %(id)s"""
        else:
            sql = """UPDATE smsq
                SET sent = %(sent)s, smsid = %(smsid)s
                WHERE id = %(id)s"""

        data = dict(sent=sent, smsid=smsid, id=identifier)
        db.execute(sql, data)
        dbconn.commit()

        return db.rowcount

    def inserttestmsgs(self, uid, phone, msg):
        """
        Insert test messages into the SMS queue for debugging purposes.

        Returns a integer indicating how many rows have been inserted.
        """

        dbconn = self._connect()
        db = dbconn.cursor()

        data = dict(uid=uid, phone=phone, msg=msg)
        sql = """INSERT INTO smsq (accountid, time, phone, msg) VALUES (
                 %(uid)s, now(), %(phone)s, %(msg)s)"""

        db.execute(sql, data)
        dbconn.commit()

        return db.rowcount

    @staticmethod
    @nav.db.retry_on_db_loss(delay=5)
    def _connect():
        return nav.db.getConnection('smsd', 'navprofile')
