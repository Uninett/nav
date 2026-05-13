"""Integration test to verify the postgresql backend connects on Django 5.2."""

from django.conf import settings
from django.db import connection


class TestDatabaseBackend:
    def test_when_checking_engine_then_it_should_use_postgresql(self, db):
        engine = settings.DATABASES['default']['ENGINE']
        assert engine == 'django.db.backends.postgresql'

    def test_when_connecting_then_it_should_use_postgresql_vendor(self, db):
        assert connection.vendor == 'postgresql'

    def test_when_querying_then_it_should_return_version(self, db):
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            row = cursor.fetchone()
        assert 'PostgreSQL' in row[0]
