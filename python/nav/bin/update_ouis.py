#!/usr/bin/env python
# -*- testargs: -h -*-
#
# Copyright (C) 2024 Sikt
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

import argparse
import sys
import logging

from typing import Iterable, Generator, Tuple

import requests
from requests.exceptions import RequestException

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

import django.db

from nav.macaddress import MacPrefix
from nav.logs import init_stderr_logging

_logger = logging.getLogger(__name__)

FILE_URL = "https://standards-oui.ieee.org/oui/oui.txt"
USER_AGENT = "Mozilla/5.0 (X11; Linux i686; rv:135.0) Gecko/20100101 Firefox/135.0"

MAX_ERRORS = 100


def main():
    init_stderr_logging()
    argparse.ArgumentParser(
        description="Updates the database with OUIs and their related organizations"
    ).parse_args()
    run()


def run():
    _logger.debug(f"Downloading OUIs from {FILE_URL}")
    try:
        data = _download_oui_file(FILE_URL)
    except RequestException as error:
        _logger.error("Error while downloading OUIs: %s", error)
        sys.exit(1)
    ouis = _parse_ouis(data)
    _update_database(ouis)
    _logger.debug("Completed updating OUI records")


def _download_oui_file(url: str) -> str:
    headers = {
        'User-Agent': USER_AGENT,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def _parse_ouis(oui_data: str) -> Generator[Tuple[str, str], None, None]:
    """Returns lists of tuples containing OUI and vendor name for
    each vendor
    """
    error_count = 0
    for line in oui_data.split('\n'):
        if "(hex)" not in line:
            continue
        try:
            yield _parse_line(line)
        except ValueError:
            error_count += 1
            if error_count >= MAX_ERRORS:
                _logger.error("Reached max amount of errors (%d), exiting", MAX_ERRORS)
                sys.exit(1)


def _parse_line(line: str) -> Tuple[str, str]:
    prefix, _, vendor = line.strip().split(None, 2)
    oui = str(MacPrefix(prefix)[0])
    return oui, vendor


@django.db.transaction.atomic
def _update_database(ouis: Iterable[Tuple[str, str]]):
    # Begin by dumping everything into a PostgreSQL temporary table
    _logger.debug("Updating database")
    cursor = django.db.connection.cursor()
    cursor.execute(
        """
        CREATE TEMPORARY TABLE new_oui (
            oui macaddr PRIMARY KEY,
            vendor varchar,
            CHECK (oui = trunc(oui)))
        """
    )
    cursor.executemany(
        """
        INSERT INTO new_oui (oui, vendor)
            VALUES (%s, %s)
        ON CONFLICT (oui)
            DO NOTHING
        """,
        ouis,
    )
    # Then make the necessary updates to the live OUI table, letting PostgreSQL do the
    # heavy lifting of resolving conflicts and changes
    cursor.execute(
        """
        INSERT INTO oui (oui, vendor)
        SELECT
            oui,
            vendor
        FROM
            new_oui
        ON CONFLICT (oui)
            DO UPDATE SET
                vendor = EXCLUDED.vendor
            WHERE
                oui.vendor IS DISTINCT FROM EXCLUDED.vendor
        """
    )
    cursor.execute("DELETE FROM oui WHERE oui NOT IN (SELECT oui FROM new_oui)")


if __name__ == '__main__':
    main()
