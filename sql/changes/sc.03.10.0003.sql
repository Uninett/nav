INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('snmpAgentState', 'Tells us whether the SNMP agent on a device is down or up.', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentDown', 'SNMP agent is down or unreachable due to misconfiguration.');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentUp', 'SNMP agent is up.');
