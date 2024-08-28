import logging
import configparser
from functools import partial

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.config import NAVConfigParser
from nav.web.sortedstats import CLASSMAP, TIMEFRAMES

_logger = logging.getLogger(__name__)


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
            raise ValueError("Rows must be 1 or higher")
        return rows
