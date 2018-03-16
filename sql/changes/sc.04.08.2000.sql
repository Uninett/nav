-- django_hstore's implementation of hstore always sets the field to something,
-- so that whether the field is null or not is irrelevant. This is bad django,
-- bad sql, and bad python.
--
-- django.contrib.postgres's implementation does not do this, but we send in
-- nulls all the time, so alter tables accordingly.

ALTER TABLE netbox
    ALTER COLUMN data DROP NOT NULL;
ALTER TABLE org
    ALTER COLUMN data DROP NOT NULL;
ALTER TABLE location
    ALTER COLUMN data DROP NOT NULL;
