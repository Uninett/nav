ALTER TABLE netbox
  ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

COMMENT ON COLUMN netbox.deleted_at IS
  'A timestamp in this column indicates that a delete operation against this record has been requested';
