---
-- Insert new event and alert types for degraded link events
---
INSERT INTO eventtype (
  SELECT 'aggregateLinkState', 'The state of this aggregated link changed', 'y'
  WHERE NOT EXISTS (SELECT * FROM eventtype WHERE eventtypeid = 'aggregateLinkState'));

---
-- Insert new alerttypes for degradation and restoration of aggregated links
---
INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'aggregateLinkState', 'linkDegraded',
         'This aggregate link has been degraded'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'linkDegraded'));

INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'aggregateLinkState', 'linkRestored',
         'This aggregate link has been restored'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'linkRestored'));
