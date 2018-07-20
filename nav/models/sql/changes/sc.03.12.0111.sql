-- Alter unit on octets

UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ipIfStatsHCInOctets.ipv6';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ipIfStatsHCInOctets.ipv4';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifHCInOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifHCOutOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifInOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifOutOctets';
