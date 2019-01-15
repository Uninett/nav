-- Fix uniqueness on quarantine vlans

DELETE FROM quarantine_vlans WHERE quarantineid in (
  SELECT q2.quarantineid
  FROM quarantine_vlans q1
  JOIN quarantine_vlans q2
    ON (q1.vlan = q2.vlan AND q1.quarantineid < q2.quarantineid)
    ORDER BY q1.quarantineid);

ALTER TABLE quarantine_vlans ADD CONSTRAINT quarantine_vlan_unique UNIQUE (vlan);
