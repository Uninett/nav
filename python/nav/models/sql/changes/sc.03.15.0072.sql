-- Fix cascading deletes in interface_stack foreign keys (LP#1246226)

ALTER TABLE interface_stack DROP CONSTRAINT interface_stack_higher_fkey;
ALTER TABLE interface_stack ADD CONSTRAINT interface_stack_higher_fkey
  FOREIGN KEY (higher)
  REFERENCES interface(interfaceid)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE interface_stack DROP CONSTRAINT interface_stack_lower_fkey;
ALTER TABLE interface_stack ADD CONSTRAINT interface_stack_lower_fkey
  FOREIGN KEY (lower)
  REFERENCES interface(interfaceid)
  ON DELETE CASCADE ON UPDATE CASCADE;
