import logging

from nav.django.settings import Suppress503


class TestSuppress503:
    def test_when_status_code_is_503_it_should_reject_record(self):
        record = logging.LogRecord("test", logging.ERROR, "", 0, "msg", (), None)
        record.status_code = 503

        assert Suppress503().filter(record) is False

    def test_when_status_code_is_500_it_should_accept_record(self):
        record = logging.LogRecord("test", logging.ERROR, "", 0, "msg", (), None)
        record.status_code = 500

        assert Suppress503().filter(record) is True

    def test_when_no_status_code_it_should_accept_record(self):
        record = logging.LogRecord("test", logging.ERROR, "", 0, "msg", (), None)

        assert Suppress503().filter(record) is True
