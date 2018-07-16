---
-- Insert new event and alert types for stack state events
---
INSERT INTO eventtype (
  SELECT 'chassisState', 'The state of this chassis has changed', 'y'
  WHERE NOT EXISTS (SELECT * FROM eventtype WHERE eventtypeid = 'chassisState'));

---
-- Insert new alerttypes for chassie state alerts
---
INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'chassisState', 'chassisDown',
         'This chassis is no longer visible in the stack'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'chassisDown'));

INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'chassisState', 'chassisUp',
         'This chassis is visible in the stack again'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'chassisUp'));
