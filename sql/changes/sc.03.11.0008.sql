-- Add newly available status sections to default user's sections.
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (6, 'Thresholds exceeded', 6, 'threshold', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (7, 'SNMP agents down', 7, 'snmpagent', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (8, 'Links down', 8, 'linkstate', 0);
