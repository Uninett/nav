-- Insert oids used to check for ipv6 interface counters
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib)
  SELECT 'ipIfStatsHCInOctets.ipv4', '1.3.6.1.2.1.4.31.3.1.6.1', 'Cricket', 'IP-MIB' WHERE NOT EXISTS (
    SELECT * FROM snmpoid WHERE oidkey = 'ipIfStatsHCInOctets.ipv4'
  )
;

INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib)
  SELECT 'ipIfStatsHCInOctets.ipv6', '1.3.6.1.2.1.4.31.3.1.6.2', 'Cricket', 'IP-MIB' WHERE NOT EXISTS (
    SELECT * FROM snmpoid WHERE oidkey = 'ipIfStatsHCInOctets.ipv6'
  )
;
