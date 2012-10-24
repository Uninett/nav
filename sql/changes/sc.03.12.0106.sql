-- Add unit column to snmpoid table for storing of units
ALTER TABLE snmpoid ADD unit VARCHAR;


-- Insert some default units
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c1900Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c1900BandwidthMax';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c2900Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c5000Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c5000BandwidthMax';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'cpu1min';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'cpu5min';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'hpcpu';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'hpmem5minFree';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'hpmem5minUsed';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'mem5minFree';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'mem5minUsed';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuIdle';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuSystem';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuUser';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load15min';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load1min';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load5min';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memrealAvail';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memswapAvail';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memtotalAvail';
UPDATE snmpoid SET unit = 'timeticks' WHERE oidkey = 'sysUpTime';

UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ipIfStatsHCInOctets.ipv6';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ipIfStatsHCInOctets.ipv4';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifHCInOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifHCInUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifHCOutOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifHCOutUcastPkts';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInDiscards';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInErrors';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInNUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifInOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInUcastPkts';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInUnknownProtos';
UPDATE snmpoid SET unit = 'timeticks' WHERE oidkey = 'ifLastChange';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutDiscards';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutErrors';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutNUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifOutOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutQLen';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutUcastPkts';
