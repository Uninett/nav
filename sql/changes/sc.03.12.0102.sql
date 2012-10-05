-- automatically close snmpAgentStates when community is removed.

CREATE OR REPLACE FUNCTION close_snmpagentstates_on_community_clear()
RETURNS TRIGGER AS E'
    BEGIN
        IF COALESCE(OLD.ro, \'\') IS DISTINCT FROM COALESCE(NEW.ro, \'\')
           AND COALESCE(NEW.ro, \'\') = \'\' THEN
            UPDATE alerthist
            SET end_time=NOW()
            WHERE netboxid=NEW.netboxid
              AND eventtypeid=\'snmpAgentState\'
              AND end_time >= \'infinity\';
        END IF;
        RETURN NULL;
    END;
    ' language 'plpgsql';

CREATE TRIGGER trig_close_snmpagentstates_on_community_clear
    AFTER UPDATE ON netbox
    FOR EACH ROW
    EXECUTE PROCEDURE close_snmpagentstates_on_community_clear();

-- also close any currently wrongfully open SNMP states
UPDATE alerthist
SET end_time=NOW()
FROM netbox
WHERE eventtypeid='snmpAgentState'
  AND end_time >= 'infinity'
  AND alerthist.netboxid = netbox.netboxid
  AND COALESCE(netbox.ro, '') = '';
