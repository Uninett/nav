-- Ensure no sysnames are blank, and enforce it as a constraint
UPDATE netbox
  SET sysname=ip::TEXT
  WHERE LENGTH(TRIM(BOTH FROM sysname)) = 0;

ALTER TABLE netbox
  ADD CONSTRAINT netbox_sysname_notblank CHECK (LENGTH(TRIM(BOTH FROM sysname)) > 0);
