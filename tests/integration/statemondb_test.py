"""Some simple integration tests for the legacy statemon system"""

from nav.statemon import db


def test_get_checkers_does_not_raise():
    conn = db.db()
    assert conn.get_checkers(True) is not None


def test_when_reading_inet_columns_over_binary_protocol_then_returns_str():
    """statemon callers expect the plain strings psycopg2 returned, regardless
    of whether psycopg3 uses the text or the binary wire protocol.
    """
    conn = db.db()
    conn.connect()
    with conn.db.cursor(binary=True) as cursor:
        cursor.execute("SELECT '10.0.0.1'::inet, '10.0.0.0/24'::cidr")
        inet_value, cidr_value = cursor.fetchone()
    assert inet_value == '10.0.0.1'
    assert isinstance(inet_value, str)
    assert cidr_value == '10.0.0.0/24'
    assert isinstance(cidr_value, str)
