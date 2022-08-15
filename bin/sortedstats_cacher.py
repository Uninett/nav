#!/usr/bin/env python3
# -*- testargs: hour -*-

import argparse
import logging
import configparser
from functools import partial

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.logs import init_generic_logging
from nav.config import NAVConfigParser
from nav.web.sortedstats import CLASSMAP, TIMEFRAMES
from nav.web.sortedstats.views import collect_result
from nav.daemon import justme, writepidfile, DaemonError

LOGFILE = "sortedstats_cacher.log"
_logger = logging.getLogger('nav.sortedstats_cacher')


class SortedStatsConfig(NAVConfigParser):
    """Configparser for SortedStats"""

    DEFAULT_CONFIG_FILES = ('sortedstats.conf',)

    def get_reports(self, timeframe):
        reports = {}
        for section in self.sections():
            try:
                get = partial(self.get, section)
                if timeframe != get('timeframe'):
                    continue
                timeframe = self.validate_timeframe(get('timeframe'))
                view = self.validate_view(get('view'))
                rows = self.validate_rows(get('rows'))
                reports[section] = {
                    'timeframe': timeframe,
                    'view': view,
                    'rows': rows,
                }
            except (configparser.Error, ValueError) as error:
                _logger.error(f"Error reading config for report {section}: {error}")
        return reports

    def validate_timeframe(self, timeframe):
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Timeframe {timeframe} is not supported")
        return timeframe

    def validate_view(self, view):
        if view not in CLASSMAP:
            raise ValueError(f"View {view} is not supported")
        return view

    def validate_rows(self, rows):
        rows = int(rows)
        if rows < 1:
            raise ValueError(f"Rows must be 1 or higher")
        return rows


def main(timeframe, config):
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
    init_generic_logging(logfile=LOGFILE, stderr=False, read_config=True)
    timeframe = get_parser().parse_args().timeframe
    pidfile = f"sortedstats_cacher_{timeframe}.pid"
    exit_if_running(pidfile)
    writepidfile(pidfile)
    config = SortedStatsConfig()
    main(timeframe, config)
