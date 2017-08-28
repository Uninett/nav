#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2016 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sends email status reports"""

import argparse
from nav.web.business.reportengine import send_reports
from nav.models.profiles import ReportSubscription


def main(args):
    """Send all reports"""
    send_reports(args.period, args.report_type)


def get_parser():
    """Define the parser"""
    parser = argparse.ArgumentParser()
    period_choices = [p[0] for p in ReportSubscription.PERIODS]
    type_choices = [p[0] for p in ReportSubscription.TYPES]
    parser.add_argument('period',
                        help='The period for this report',
                        choices=period_choices)
    parser.add_argument('report_type',
                        help='The type of report',
                        choices=type_choices)
    return parser


if __name__ == '__main__':
    main(get_parser().parse_args())
