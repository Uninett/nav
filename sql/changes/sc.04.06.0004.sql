-- Always default new devices to SNMP v2c
ALTER TABLE netbox
ALTER COLUMN snmp_version SET DEFAULT 2;
