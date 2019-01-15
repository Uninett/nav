-- clean up remnants of LP#1269714
-- (Physically replacing a device may cause all further SNMP polling of it to
--  stop)

UPDATE alerthist
SET end_time=NOW()
WHERE alerthistid IN (SELECT alerthistid
                      FROM alerthist ah
                      JOIN netbox n USING (netboxid)
                      WHERE eventtypeid = 'snmpAgentState'
                            AND end_time >= 'infinity'
                            AND ah.deviceid <> n.deviceid);

INSERT INTO vendor (
  SELECT 'unknown' AS vendorid
  WHERE NOT EXISTS (
    SELECT vendorid FROM vendor WHERE vendorid='unknown'));
