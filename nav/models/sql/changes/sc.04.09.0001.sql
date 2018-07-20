-- django_hstore's implementation of hstore always sets the field to something,
-- so that whether the field is null or not is irrelevant. This is bad django,
-- bad sql, and bad python.
--
-- django.contrib.postgres's implementation does not do this, but we send in
-- nothing all the time. Alter behavior so that those columns are never NULL
-- regardless, to be sure we never end up with some fields "empty" and some
-- NULL in the same column.
--
-- DEFAULT '' is the same as DEFAULT {} is the same as DEAULT [] as fra as
-- hstore is concerned.

ALTER TABLE account ALTER COLUMN preferences SET DEFAULT '';
ALTER TABLE apitoken ALTER COLUMN endpoints SET DEFAULT '';
ALTER TABLE location ALTER COLUMN data SET DEFAULT '';
ALTER TABLE netbox ALTER COLUMN data SET DEFAULT '';
ALTER TABLE netboxentity ALTER COLUMN data SET DEFAULT '';
ALTER TABLE org ALTER COLUMN data SET DEFAULT '';
ALTER TABLE room ALTER COLUMN data SET DEFAULT '';
