BEGIN;
DELETE FROM snmpoid WHERE oidkey='hpStackName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpStackName', '1.3.6.1.4.1.11.2.14.11.5.1.10.3.1.0', 'Name of stack', 'hp', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cpu1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cpu1min', '1.3.6.1.4.1.9.2.1.57.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cpu5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cpu5min', '1.3.6.1.4.1.9.2.1.58.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='mem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('mem5minUsed', '1.3.6.1.4.1.9.9.48.1.1.1.5.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_memswapAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_memswapAvail', '1.3.6.1.4.1.2021.4.4.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_cpuIdle';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_cpuIdle', '1.3.6.1.4.1.2021.11.11.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c1900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c1900Bandwidth', '1.3.6.1.4.1.437.1.1.3.7.1.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c5000BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c5000BandwidthMax', '1.3.6.1.4.1.9.5.1.1.19.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpmem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpmem5minUsed', '1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.7.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpcpu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpcpu', '1.3.6.1.4.1.11.2.14.11.5.1.9.6.1.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_memrealAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_memrealAvail', '1.3.6.1.4.1.2021.4.6.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_cpuUser';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_cpuUser', '1.3.6.1.4.1.2021.11.9.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c2900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c2900Bandwidth', '1.3.6.1.4.1.9.9.87.1.5.1.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpmem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpmem5minFree', '1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='tempInlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('tempInlet', '1.3.6.1.4.1.9.9.13.1.3.1.3.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c1900BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c1900BandwidthMax', '1.3.6.1.4.1.437.1.1.3.7.5.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='tempOutlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('tempOutlet', '1.3.6.1.4.1.9.9.13.1.3.1.3.3', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='mem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('mem5minFree', '1.3.6.1.4.1.9.9.48.1.1.1.6.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_load1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_load1min', '1.3.6.1.4.1.2021.10.1.3.1', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_load5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_load5min', '1.3.6.1.4.1.2021.10.1.3.2', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_load15min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_load15min', '1.3.6.1.4.1.2021.10.1.3.3', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_memtotalAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_memtotalAvail', '1.3.6.1.4.1.2021.4.11.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ucd_cpuSystem';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ucd_cpuSystem', '1.3.6.1.4.1.2021.11.10.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c5000Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c5000Bandwidth', '1.3.6.1.4.1.9.5.1.1.8.0', '', 'Cricket', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpHwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.4.0', 'Hardware version number', 'hp', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpSwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.3.0', 'Software version number', 'hp', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuMac', '1.3.6.1.4.1.9.5.14.4.3.1.4.1', 'Bridge table for Cisco menu type switch', 'cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cHubMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cHubMac', '1.3.6.1.4.1.43.10.9.5.1.6', 'Bridge table for 3Com HUBs', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3c9300Mac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3c9300Mac', '1.3.6.1.4.1.43.29.4.10.8.1.5.1', 'Bridge table for 3Com SuperStack 1900', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cSSMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cSSMac', '1.3.6.1.4.1.43.10.22.2.1.3', 'Bridge table for 3Com SuperStack', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cHsrpGrpVirtualIpAddr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cHsrpGrpVirtualIpAddr', '1.3.6.1.4.1.9.9.106.1.2.1.1.11', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardSlotNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardSlotNumber', '1.3.6.1.4.1.9.3.6.11.1.7', 'Slot card slotnumber mapping', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardSwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardSwVersion', '1.3.6.1.4.1.9.3.6.11.1.6', 'Slot card software version', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardHwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardHwVersion', '1.3.6.1.4.1.9.3.6.11.1.5', 'Slot card hardware version', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardSerial', '1.3.6.1.4.1.9.3.6.11.1.4', 'Slot card serial', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardIndex', '1.3.6.1.4.1.9.3.6.11.1.1', 'Slot card type', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cCardDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cCardDescr', '1.3.6.1.4.1.9.3.6.11.1.3', 'Slot card description', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuVlan', '1.3.6.1.4.1.9.5.14.8.1.1.3', 'Port trunk state', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpModules', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.4', 'unitChange', 'hp', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cModel', '1.3.6.1.4.1.9.3.6.11.1.2', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cModel', '1.3.6.1.4.1.43.10.27.1.1.1.19', 'Model', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cDescr', '1.3.6.1.4.1.43.10.27.1.1.1.5', 'Description', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cHwVer', '1.3.6.1.4.1.43.10.27.1.1.1.11', 'Hardware version number', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifHCOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifHCOutOctets', '1.3.6.1.2.1.31.1.1.1.10', 'Number of octets transmitted out of the interface', 'mib-II', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c1900Portname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c1900Portname', '1.3.6.1.4.1.437.1.1.3.3.1.1.3', 'Portname', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpStack';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpStack', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1', 'Lists modules in the stack', 'hp', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpPortType', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2', 'Type of each port (media, duplex)', 'hp', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cIfMauType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cIfMauType', '1.3.6.1.2.1.26.2.1.1.3', 'Speed and dupelx for SWxx00', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cSw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cSw', '1.3.6.1.4.1.9.3.6.11.1.6', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifHCInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifHCInUcastPkts', '1.3.6.1.2.1.31.1.1.1.7', '', 'mib-II', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='c1900Duplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('c1900Duplex', '1.3.6.1.4.1.437.1.1.3.3.1.1.8', 'Duplex status', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cMac', '1.3.6.1.4.1.43.10.27.1.1.1.2', 'MACs on this port', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cSwVer', '1.3.6.1.4.1.43.10.27.1.1.1.12', 'Software version number', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cPS40PortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cPS40PortState', '1.3.6.1.2.1.26.1.1.1.6', 'Port state for 3Com PS40', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuIfIndex', '1.3.6.1.4.1.9.5.14.4.1.1.4', 'Ifindex to port mapping', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuPortStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuPortStatus', '1.3.6.1.4.1.9.5.14.4.1.1.29', 'Port state, up or down', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuTrunk', '1.3.6.1.4.1.9.5.14.4.1.1.44', 'Port trunk state', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='hpVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('hpVlan', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1', 'Vlan for each port', 'hp', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifHCInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifHCInOctets', '1.3.6.1.2.1.31.1.1.1.6', 'Number of octets received on the interface', 'mib-II', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifHCOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifHCOutUcastPkts', '1.3.6.1.2.1.31.1.1.1.11', '', 'mib-II', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3c9300Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3c9300Serial', '1.3.6.1.4.1.43.29.4.18.2.1.7.1', '3com9300', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cL3Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cL3Serial', '1.3.6.1.4.1.9.9.92.1.1.1.2', 'Serial number', 'cL3', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifSerial', '1.3.6.1.2.1.47.1.1.1.1.11.1', 'standard', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cDescr', '1.3.6.1.4.1.9.3.6.11.1.3', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cHw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cHw', '1.3.6.1.4.1.9.3.6.11.1.5', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cIfDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cIfDescr', '1.3.6.1.2.1.2.2.1.2', '3Com ifDescr for port and unit', '3com', true, true, '.*Port (\\d+)\\b.*', true);


DELETE FROM snmpoid WHERE oidkey='3comModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3comModules', '1.3.6.1.4.1.43.10.27.1.1.1.12', 'unitChange', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cHsrpGrpStandbyState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cHsrpGrpStandbyState', '1.3.6.1.4.1.9.9.106.1.2.1.1.15', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portPortName', '1.3.6.1.4.1.9.5.1.4.1.1.4', 'cat-sw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='3cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('3cSerial', '1.3.6.1.4.1.43.10.27.1.1.1.13', 'Serial number', '3com', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ospfIfMetricMetric';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ospfIfMetricMetric', '1.3.6.1.2.1.14.8.1.4', 'cgw', NULL, true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuPortType', '1.3.6.1.4.1.9.5.14.4.1.1.41', 'Port type, media', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cMenuDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cMenuDuplex', '1.3.6.1.4.1.9.5.14.4.1.1.5', 'Port duplex state', 'Cisco', true, true, NULL, false);


DELETE FROM snmpoid WHERE oidkey='typeoid';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('typeoid', '1.3.6.1.2.1.1.2.0', 'all', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='dnscheck';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('dnscheck', '1.3.6.1.2.1.1.5.0', 'Used by the DNSCheck plugin; is identical to sysname', 'mib-II', true, false, NULL, true);


DELETE FROM snmpoid WHERE oidkey='sysUpTime';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('sysUpTime', '1.3.6.1.2.1.1.3.0', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='sysname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('sysname', '1.3.6.1.2.1.1.5.0', 'all', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifVlansAllowed', '1.3.6.1.4.1.9.9.46.1.6.1.1.4', 'cL3-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifAdminStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifAdminStatus', '1.3.6.1.2.1.2.2.1.7', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifDescr', '1.3.6.1.2.1.2.2.1.2', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInDiscards', '1.3.6.1.2.1.2.2.1.13', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cSerial', '1.3.6.1.4.1.9.3.6.3', 'cgw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cdpRemoteIf';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cdpRemoteIf', '1.3.6.1.4.1.9.9.23.1.2.1.1.7', 'CDP remote interface', 'cisco', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifName', '1.3.6.1.2.1.31.1.1.1.1', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifVlan', '1.3.6.1.4.1.9.9.68.1.2.2.1.2', 'ios-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ipAdEntIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ipAdEntIfIndex', '1.3.6.1.2.1.4.20.1.2', 'cgw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='catSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('catSerial', '1.3.6.1.4.1.9.5.1.3.1.1.26', 'Serial number', 'cat', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOperStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOperStatus', '1.3.6.1.2.1.2.2.1.8', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portVlansAllowed', '1.3.6.1.4.1.9.5.1.9.3.1.5', 'cat-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='macPortEntry';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('macPortEntry', '1.3.6.1.2.1.17.4.3.1.2', 'Bridge table for various switches', 'bridge-mib', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portDuplex', '1.3.6.1.4.1.9.5.1.4.1.1.10', 'cat-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInErrors', '1.3.6.1.2.1.2.2.1.14', 'Number of inbound packets that contained errors', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='cdpNeighbour';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('cdpNeighbour', '1.3.6.1.4.1.9.9.23.1.2.1.1.6', 'CDP neighbour', 'cisco', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifNumber', '1.3.6.1.2.1.2.1.0', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutUcastPkts', '1.3.6.1.2.1.2.2.1.17', 'Packets that higher-level protocols requested be transmitted, and which were not addressed to a multicast or broadcast address at this sub-layer', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutNUcastPkts', '1.3.6.1.2.1.2.2.1.18', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='moduleMon';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('moduleMon', '1.3.6.1.2.1.2.2.1.1', 'Used by the module monitor; is identical to ifIndex', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutOctets', '1.3.6.1.2.1.2.2.1.16', 'Number of octets transmitted out of the interface', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInOctets', '1.3.6.1.2.1.2.2.1.10', 'Number of octets received on the interface', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifTrunk', '1.3.6.1.4.1.9.9.46.1.6.1.1.13', 'cL3-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInUcastPkts', '1.3.6.1.2.1.2.2.1.11', 'Packets which were not addressed to a multicast or broadcast address at this sub-layer', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifPhysAddress', '1.3.6.1.2.1.2.2.1.6', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='iosDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('iosDuplex', '1.3.6.1.4.1.9.9.87.1.4.1.1.32.0', 'ios-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifSpeed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifSpeed', '1.3.6.1.2.1.2.2.1.5', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifIndex', '1.3.6.1.2.1.2.2.1.1', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='basePortIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('basePortIfIndex', '1.3.6.1.2.1.17.1.4.1.2', 'Port ifindex mapping', 'bridge-mib', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifPortName', '1.3.6.1.4.1.9.2.2.1.1.28', 'ios-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifMtu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifMtu', '1.3.6.1.2.1.2.2.1.4', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifType', '1.3.6.1.2.1.2.2.1.3', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInNUcastPkts', '1.3.6.1.2.1.2.2.1.12', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifInUnknownProtos';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifInUnknownProtos', '1.3.6.1.2.1.2.2.1.15', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifAlias';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifAlias', '1.3.6.1.2.1.31.1.1.1.18', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='iosTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('iosTrunk', '1.3.6.1.4.1.9.9.87.1.4.1.1.6.0', 'ios-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutErrors', '1.3.6.1.2.1.2.2.1.20', 'Number of outbound packets that could not be transmitted because of errors', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portTrunk', '1.3.6.1.4.1.9.5.1.9.3.1.8', 'cat-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='stpPortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('stpPortState', '1.3.6.1.2.1.17.2.15.1.3', 'Spanning tree port state', 'bridge-mib', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portVlan', '1.3.6.1.4.1.9.5.1.9.3.1.3', 'cat-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifLastChange';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifLastChange', '1.3.6.1.2.1.2.2.1.9', 'standard', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutDiscards', '1.3.6.1.2.1.2.2.1.19', '', 'mib-II', true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ipAdEntIfNetMask';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ipAdEntIfNetMask', '1.3.6.1.2.1.4.20.1.3', 'cgw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='portIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('portIfIndex', '1.3.6.1.4.1.9.5.1.4.1.1.11', 'cat-sw', NULL, true, false, NULL, false);


DELETE FROM snmpoid WHERE oidkey='ifOutQLen';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex) VALUES ('ifOutQLen', '1.3.6.1.2.1.2.2.1.21', '', 'mib-II', true, false, NULL, false);


COMMIT;
