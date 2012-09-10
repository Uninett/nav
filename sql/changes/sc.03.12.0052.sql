-- Insert oids used to check for ipv6 interface counters
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib) VALUES ('ipIfStatsHCInOctets.ipv4', '1.3.6.1.2.1.4.31.3.1.6.1', 'Cricket', 'IP-MIB');
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib) VALUES ('ipIfStatsHCInOctets.ipv6', '1.3.6.1.2.1.4.31.3.1.6.2', 'Cricket', 'IP-MIB');
