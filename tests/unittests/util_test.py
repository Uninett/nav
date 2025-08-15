import logging

import pytest

from nav.util import check_log_level


class TestCheckLogLevel:
    def test_actual_loglevel_above_input_should_return_false(self, *_):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        assert check_log_level(logger, logging.DEBUG) is False

    def test_actual_loglevel_below_input_should_return_true(self, *_):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        assert check_log_level(logger, logging.WARNING)
