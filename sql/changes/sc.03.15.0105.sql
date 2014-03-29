-- Fix cascading deletes in accounttool foreign keys (LP#1293621)

ALTER TABLE accounttool DROP CONSTRAINT accounttool_accountid_fkey;
ALTER TABLE accounttool ADD CONSTRAINT accounttool_accountid_fkey
  FOREIGN KEY (accountid)
  REFERENCES account(id)
  ON DELETE CASCADE ON UPDATE CASCADE;
