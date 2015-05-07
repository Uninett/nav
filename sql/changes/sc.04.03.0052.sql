---
-- Insert new eventtype for stack state events
---
INSERT INTO eventtype (
  SELECT 'stackState', 'The state of this stack has changed', 'y'
  WHERE NOT EXISTS (SELECT * FROM eventtype WHERE eventtypeid = 'stackState'));

---
-- Insert new alerttypes for stack state alerts
---
INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'stackState', 'stackDegraded',
         'The stack has lost one or more chassis'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'stackDegraded'));

INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'stackState', 'stackOk',
         'All chassis in the stack are ok'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'stackOk'));
