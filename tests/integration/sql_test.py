# testing the sql schemas
from nav.db import getConnection


def test_public_namespace_should_be_empty():
    cursor = getConnection('default').cursor()
    cursor.execute(
        """SELECT relname
                      FROM pg_class c
                      JOIN pg_namespace n ON (c.relnamespace=n.oid)
                      WHERE nspname='public'
                      ORDER BY nspname"""
    )

    names = [n for (n,) in cursor.fetchall()]
    assert len(names) == 0, (
        "Objects have been defined in the public namespace: " + ".".join(names)
    )
