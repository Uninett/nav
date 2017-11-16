-- Add field for read/write to APIToken

ALTER TABLE apitoken ADD permission VARCHAR DEFAULT 'read';
ALTER TABLE apitoken
      ADD CONSTRAINT check_permissions
      CHECK (permission in ('read', 'write'));
UPDATE apitoken SET permission = 'read';
