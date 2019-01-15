---
-- Insert new event and alert types for bgpPeerStates
---
INSERT INTO eventtype (
  SELECT 'bgpState', 'The state of this BGP peering session changed', 'y'
  WHERE NOT EXISTS (SELECT * FROM eventtype WHERE eventtypeid = 'bgpState'));

---
-- Insert new alerttypes for degraded and established bgp peering sessions
---
INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'bgpState', 'bgpDown',
         'This BGP peering session is down'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'bgpDown'));

INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'bgpState', 'bgpEstablished',
         'This BGP peering session has been established'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'bgpEstablished'));

INSERT INTO alerttype (
  SELECT nextval('alerttype_alerttypeid_seq'), 'bgpState', 'bgpAdmDown',
         'This BGP peering session is administratively down'
  WHERE NOT EXISTS (SELECT * FROM alerttype WHERE alerttype = 'bgpAdmDown'));
