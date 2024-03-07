#!/usr/bin/env python3
# -*- testargs: hour -*-

import argparse
import logging

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.logs import init_generic_logging
from nav.web.sortedstats import TIMEFRAMES
from nav.web.sortedstats.views import collect_result
from nav.web.sortedstats.config import SortedStatsConfig
from nav.daemon import justme, writepidfile, DaemonError

LOGFILE = "sortedstats_cacher.log"
_logger = logging.getLogger('nav.sortedstats_cacher')


def main():
    init_generic_logging(logfile=LOGFILE, stderr=False, read_config=True)
    timeframe = get_parser().parse_args().timeframe
    pidfile = f"sortedstats_cacher_{timeframe}.pid"
    exit_if_running(pidfile)
    writepidfile(pidfile)
    config = SortedStatsConfig()
    run(timeframe, config)


def run(timeframe, config):
    _logger.info("Running for timeframe %s", timeframe)
    reports = config.get_reports(timeframe)
    for report_name, report in reports.items():
        _logger.info(f"Collecting results for report {report_name}")
        try:
            collect_result(report['view'], report['timeframe'], report['rows'])
        except (PermissionError, ValueError, KeyError) as error:
            _logger.error(f"Error collecting results for report {report_name}: {error}")


def get_parser():
    parser = argparse.ArgumentParser()
    timeframe_choices = TIMEFRAMES.keys()
    parser.add_argument(
        'timeframe',
        help='The timeframe to collect stats for',
        choices=timeframe_choices,
    )
    return parser


def exit_if_running(pidfile):
    try:
        justme(pidfile)
    except DaemonError as error:
        print(error)
        exit(1)


if __name__ == '__main__':
    main()
