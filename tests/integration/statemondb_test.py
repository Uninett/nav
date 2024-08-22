"""Some simple integration tests for the legacy statemon system"""

from nav.statemon import db


def test_get_checkers_does_not_raise():
    conn = db.db()
    assert conn.get_checkers(True) is not None
