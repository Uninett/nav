#!/usr/bin/env python
#
# Copyright (C) 2024 Uninett AS
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

import logging

from typing import List, Iterable

import requests
from requests.exceptions import RequestException

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from django.db import transaction

from nav.models.oui import OUI

_logger = logging.getLogger(__name__)

FILE_URL = "https://standards-oui.ieee.org/oui/oui.txt"


def main():
    _logger.info(f"Downloading OUIs from {FILE_URL}")
    try:
        data = _download_oui_file(FILE_URL)
    except RequestException as e:
        _logger.error("Error while downloading OUIs: %s", e)
        exit(1)
    ouis = _parse_ouis(data)
    _update_database(ouis)
    _logger.info("Completed updating OUI records")


def _download_oui_file(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


@transaction.atomic
def _update_database(ouis: Iterable[OUI]):
    _logger.info("Deleting existing records")
    OUI.objects.all().delete()
    _logger.info("Creating new records")
    OUI.objects.bulk_create(ouis, ignore_conflicts=True)


def _parse_ouis(oui_data: str) -> List[OUI]:
    """Returns lists of tuples containing OUI and vendor name for
    each vendor
    """
    oui_list = []
    for line in oui_data.split('\n'):
        if "(hex)" not in line:
            continue
        oui_list.append(_parse_line(line))
    return oui_list


def _parse_line(line: str) -> OUI:
    line = line.strip()
    split_line = line.split()
    oui = split_line[0] + "-00-00-00"
    split_vendor = split_line[2:]
    vendor = " ".join(split_vendor)
    return OUI(oui=oui, vendor=vendor)


if __name__ == '__main__':
    main()
