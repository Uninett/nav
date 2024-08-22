#!/usr/bin/env python
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

import sys
import logging

from typing import Iterable, Generator

import requests
from requests.exceptions import RequestException

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from django.db import transaction

from nav.models.oui import OUI
from nav.macaddress import MacPrefix
from nav.logs import init_stderr_logging

_logger = logging.getLogger(__name__)

FILE_URL = "https://standards-oui.ieee.org/oui/oui.txt"

MAX_ERRORS = 100


def main():
    init_stderr_logging()
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
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def _parse_ouis(oui_data: str) -> Generator[OUI, None, None]:
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


def _parse_line(line: str) -> OUI:
    prefix, _, vendor = line.strip().split(None, 2)
    oui = str(MacPrefix(prefix)[0])
    return OUI(oui=oui, vendor=vendor)


@transaction.atomic
def _update_database(ouis: Iterable[OUI]):
    _logger.info("Deleting existing records")
    OUI.objects.all().delete()
    _logger.info("Creating new records")
    OUI.objects.bulk_create(ouis, ignore_conflicts=True)


if __name__ == '__main__':
    main()
