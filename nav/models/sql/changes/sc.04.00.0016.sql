-- Fix cascading deletes in account_navlet foreign keys (LP#1293616)

ALTER TABLE account_navlet DROP CONSTRAINT account_navlet_account_fkey;
ALTER TABLE account_navlet ADD CONSTRAINT account_navlet_account_fkey
  FOREIGN KEY (account)
  REFERENCES account(id)
  ON DELETE CASCADE ON UPDATE CASCADE;
