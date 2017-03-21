ALTER TABLE netbox
  ADD COLUMN masterid INTEGER DEFAULT NULL,
  ADD CONSTRAINT netbox_masterid_fkey
    FOREIGN KEY (masterid)
    REFERENCES netbox(netboxid)
    ON DELETE CASCADE ON UPDATE CASCADE;

COMMENT ON COLUMN netbox.masterid IS
  'In the case of virtual sub-units, this field references the physical master unit';

