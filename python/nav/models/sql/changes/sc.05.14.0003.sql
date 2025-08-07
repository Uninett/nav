ALTER TABLE manage.jwtrefreshtoken ADD permission VARCHAR DEFAULT 'read';
ALTER TABLE manage.jwtrefreshtoken
      ADD CONSTRAINT check_permissions
      CHECK (permission in ('read', 'write'));
UPDATE manage.jwtrefreshtoken SET permission = 'read' WHERE permission IS NULL;

ALTER TABLE manage.jwtrefreshtoken ADD COLUMN endpoints hstore;
