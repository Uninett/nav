DELETE FROM snmpoid WHERE snmpoidid='stpPortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('stpPortState', '1.3.6.1.2.1.17.2.15.1.3', 'Spanning tree port state', 'bridge-mib');

DELETE FROM snmpoid WHERE snmpoidid='basePortIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('basePortIfIndex', '1.3.6.1.2.1.17.1.4.1.2', 'Port ifindex mapping', 'bridge-mib');

DELETE FROM snmpoid WHERE snmpoidid='cdpRemoteIf';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cdpRemoteIf', '1.3.6.1.4.1.9.9.23.1.2.1.1.7', 'CDP remote interface', 'cisco');

DELETE FROM snmpoid WHERE snmpoidid='macPortEntry';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('macPortEntry', '1.3.6.1.2.1.17.4.3.1.2', 'Bridge table for various switches', 'bridge-mib');

DELETE FROM snmpoid WHERE snmpoidid='cdpNeighbour';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cdpNeighbour', '1.3.6.1.4.1.9.9.23.1.2.1.1.6', 'CDP neighbour', 'cisco');

DELETE FROM snmpoid WHERE snmpoidid='hpStackName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpStackName', '1.3.6.1.4.1.11.2.14.11.5.1.10.3.1.0', 'Name of stack', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='cpu1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cpu1min', '1.3.6.1.4.1.9.2.1.57.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='cpu5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cpu5min', '1.3.6.1.4.1.9.2.1.58.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='mem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('mem5minUsed', '1.3.6.1.4.1.9.9.48.1.1.1.5.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_memswapAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_memswapAvail', '1.3.6.1.4.1.2021.4.4.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_cpuIdle';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_cpuIdle', '1.3.6.1.4.1.2021.11.11.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='c1900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c1900Bandwidth', '1.3.6.1.4.1.437.1.1.3.7.1.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='c5000BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c5000BandwidthMax', '1.3.6.1.4.1.9.5.1.1.19.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='hpmem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpmem5minUsed', '1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.7.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cSerial', '1.3.6.1.4.1.9.3.6.3', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='hpcpu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpcpu', '1.3.6.1.4.1.11.2.14.11.5.1.9.6.1.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_memrealAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_memrealAvail', '1.3.6.1.4.1.2021.4.6.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_cpuUser';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_cpuUser', '1.3.6.1.4.1.2021.11.9.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='c2900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c2900Bandwidth', '1.3.6.1.4.1.9.9.87.1.5.1.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='hpmem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpmem5minFree', '1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='tempInlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('tempInlet', '1.3.6.1.4.1.9.9.13.1.3.1.3.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='c1900BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c1900BandwidthMax', '1.3.6.1.4.1.437.1.1.3.7.5.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='tempOutlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('tempOutlet', '1.3.6.1.4.1.9.9.13.1.3.1.3.3', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='mem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('mem5minFree', '1.3.6.1.4.1.9.9.48.1.1.1.6.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_load1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_load1min', '1.3.6.1.4.1.2021.10.1.3.1', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_load5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_load5min', '1.3.6.1.4.1.2021.10.1.3.2', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_load15min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_load15min', '1.3.6.1.4.1.2021.10.1.3.3', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_memtotalAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_memtotalAvail', '1.3.6.1.4.1.2021.4.11.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='ucd_cpuSystem';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ucd_cpuSystem', '1.3.6.1.4.1.2021.11.10.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='c5000Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c5000Bandwidth', '1.3.6.1.4.1.9.5.1.1.8.0', '', 'Cricket');

DELETE FROM snmpoid WHERE snmpoidid='hpHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpHwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.4.0', 'Hardware version number', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='hpSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpSwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.3.0', 'Software version number', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='hpSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpSerial', '1.3.6.1.2.1.47.1.1.1.1.11.1', 'Serial number', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='cMenuMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuMac', '1.3.6.1.4.1.9.5.14.4.3.1.4.1', 'Bridge table for Cisco menu type switch', 'cisco');

DELETE FROM snmpoid WHERE snmpoidid='3cHubMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cHubMac', '1.3.6.1.4.1.43.10.9.5.1.6', 'Bridge table for 3Com HUBs', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3c9300Mac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3c9300Mac', '1.3.6.1.4.1.43.29.4.10.8.1.5.1', 'Bridge table for 3Com SuperStack 1900', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3cSSMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cSSMac', '1.3.6.1.4.1.43.10.22.2.1.3', 'Bridge table for 3Com SuperStack', '3com');

DELETE FROM snmpoid WHERE snmpoidid='ifOutDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutDiscards', '1.3.6.1.2.1.2.2.1.19', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifOutQLen';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutQLen', '1.3.6.1.2.1.2.2.1.21', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInUnknownProtos';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInUnknownProtos', '1.3.6.1.2.1.2.2.1.15', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='cHsrpGrpVirtualIpAddr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cHsrpGrpVirtualIpAddr', '1.3.6.1.4.1.9.9.106.1.2.1.1.11', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cCardSlotNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardSlotNumber', '1.3.6.1.4.1.9.3.6.11.1.7', 'Slot card slotnumber mapping', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cCardSwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardSwVersion', '1.3.6.1.4.1.9.3.6.11.1.6', 'Slot card software version', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cCardHwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardHwVersion', '1.3.6.1.4.1.9.3.6.11.1.5', 'Slot card hardware version', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cCardSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardSerial', '1.3.6.1.4.1.9.3.6.11.1.4', 'Slot card serial', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cCardIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardIndex', '1.3.6.1.4.1.9.3.6.11.1.1', 'Slot card type', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cCardDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cCardDescr', '1.3.6.1.4.1.9.3.6.11.1.3', 'Slot card description', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cMenuVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuVlan', '1.3.6.1.4.1.9.5.14.8.1.1.3', 'Port trunk state', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='ifOperStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOperStatus', '1.3.6.1.2.1.2.2.1.8', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifPortName', '1.3.6.1.4.1.9.2.2.1.1.28', 'ios-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='portIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portIfIndex', '1.3.6.1.4.1.9.5.1.4.1.1.11', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='hpModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpModules', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.4', 'unitChange', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cModel', '1.3.6.1.4.1.9.3.6.11.1.2', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='iosDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('iosDuplex', '1.3.6.1.4.1.9.9.87.1.4.1.1.32.0', 'ios-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='3cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cModel', '1.3.6.1.4.1.43.10.27.1.1.1.19', 'Model', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cDescr', '1.3.6.1.4.1.43.10.27.1.1.1.5', 'Description', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3cHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cHwVer', '1.3.6.1.4.1.43.10.27.1.1.1.11', 'Hardware version number', '3com');

DELETE FROM snmpoid WHERE snmpoidid='ifHCOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifHCOutOctets', '1.3.6.1.2.1.31.1.1.1.10', 'Number of octets transmitted out of the interface', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifPhysAddress', '1.3.6.1.2.1.2.2.1.6', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='c1900Portname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c1900Portname', '1.3.6.1.4.1.437.1.1.3.3.1.1.3', 'Portname', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='ifMtu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifMtu', '1.3.6.1.2.1.2.2.1.4', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifIndex', '1.3.6.1.2.1.2.2.1.1', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='hpStack';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpStack', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1', 'Lists modules in the stack', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='ifType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifType', '1.3.6.1.2.1.2.2.1.3', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInDiscards', '1.3.6.1.2.1.2.2.1.13', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='hpPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpPortType', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2', 'Type of each port (media, duplex)', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='ifSpeed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifSpeed', '1.3.6.1.2.1.2.2.1.5', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifLastChange';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifLastChange', '1.3.6.1.2.1.2.2.1.9', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='3cIfMauType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cIfMauType', '1.3.6.1.2.1.26.2.1.1.3', 'Speed and dupelx for SWxx00', '3com');

DELETE FROM snmpoid WHERE snmpoidid='cSw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cSw', '1.3.6.1.4.1.9.3.6.11.1.6', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifHCInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifHCInUcastPkts', '1.3.6.1.2.1.31.1.1.1.7', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='c1900Duplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('c1900Duplex', '1.3.6.1.4.1.437.1.1.3.3.1.1.8', 'Duplex status', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='3cMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cMac', '1.3.6.1.4.1.43.10.27.1.1.1.2', 'MACs on this port', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3cSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cSwVer', '1.3.6.1.4.1.43.10.27.1.1.1.12', 'Software version number', '3com');

DELETE FROM snmpoid WHERE snmpoidid='3cPS40PortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cPS40PortState', '1.3.6.1.2.1.26.1.1.1.6', 'Port state for 3Com PS40', '3com');

DELETE FROM snmpoid WHERE snmpoidid='ifAlias';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifAlias', '1.3.6.1.2.1.31.1.1.1.18', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInErrors', '1.3.6.1.2.1.2.2.1.14', 'Number of inbound packets that contained errors', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='cMenuIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuIfIndex', '1.3.6.1.4.1.9.5.14.4.1.1.4', 'Ifindex to port mapping', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='ifOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutUcastPkts', '1.3.6.1.2.1.2.2.1.17', 'Packets that higher-level protocols requested be transmitted, and which were not addressed to a multicast or broadcast address at this sub-layer', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='cMenuPortStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuPortStatus', '1.3.6.1.4.1.9.5.14.4.1.1.29', 'Port state, up or down', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cMenuTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuTrunk', '1.3.6.1.4.1.9.5.14.4.1.1.44', 'Port trunk state', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='ifOutNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutNUcastPkts', '1.3.6.1.2.1.2.2.1.18', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='hpVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('hpVlan', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1', 'Vlan for each port', 'hp');

DELETE FROM snmpoid WHERE snmpoidid='ifHCInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifHCInOctets', '1.3.6.1.2.1.31.1.1.1.6', 'Number of octets received on the interface', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifHCOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifHCOutUcastPkts', '1.3.6.1.2.1.31.1.1.1.11', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='3c9300Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3c9300Serial', '1.3.6.1.4.1.43.29.4.18.2.1.7.1', '3com9300', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cL3Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cL3Serial', '1.3.6.1.4.1.9.9.92.1.1.1.2', 'Serial number', 'cL3');

DELETE FROM snmpoid WHERE snmpoidid='catSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('catSerial', '1.3.6.1.4.1.9.5.1.3.1.1.26', 'Serial number', 'cat');

DELETE FROM snmpoid WHERE snmpoidid='ifOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutOctets', '1.3.6.1.2.1.2.2.1.16', 'Number of octets transmitted out of the interface', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInOctets', '1.3.6.1.2.1.2.2.1.10', 'Number of octets received on the interface', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInUcastPkts', '1.3.6.1.2.1.2.2.1.11', 'Packets which were not addressed to a multicast or broadcast address at this sub-layer', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifInNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifInNUcastPkts', '1.3.6.1.2.1.2.2.1.12', '', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifSerial', '1.3.6.1.2.1.47.1.1.1.1.11.1', 'standard', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cDescr', '1.3.6.1.4.1.9.3.6.11.1.3', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cHw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cHw', '1.3.6.1.4.1.9.3.6.11.1.5', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='3cIfDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cIfDescr', '1.3.6.1.2.1.2.2.1.2', '3Com ifDescr for port and unit', '3com', true, true, '.*Port (\\d+)\\b.*', true);

DELETE FROM snmpoid WHERE snmpoidid='ifOutErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifOutErrors', '1.3.6.1.2.1.2.2.1.20', 'Number of outbound packets that could not be transmitted because of errors', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ifVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifVlansAllowed', '1.3.6.1.4.1.9.9.46.1.6.1.1.4', 'cL3-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='3comModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3comModules', '1.3.6.1.4.1.43.10.27.1.1.1.12', 'unitChange', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifVlan', '1.3.6.1.4.1.9.9.68.1.2.2.1.2', 'ios-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifDescr', '1.3.6.1.2.1.2.2.1.2', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='ipAdEntIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ipAdEntIfIndex', '1.3.6.1.2.1.4.20.1.2', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cHsrpGrpStandbyState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cHsrpGrpStandbyState', '1.3.6.1.4.1.9.9.106.1.2.1.1.15', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='sysname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('sysname', '1.3.6.1.2.1.1.5.0', 'all', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifAdminStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifAdminStatus', '1.3.6.1.2.1.2.2.1.7', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='portDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portDuplex', '1.3.6.1.4.1.9.5.1.4.1.1.10', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='portVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portVlansAllowed', '1.3.6.1.4.1.9.5.1.9.3.1.5', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='typeoid';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('typeoid', '1.3.6.1.2.1.1.2.0', 'all', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ipAdEntIfNetMask';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ipAdEntIfNetMask', '1.3.6.1.2.1.4.20.1.3', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifName', '1.3.6.1.2.1.31.1.1.1.1', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='portPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portPortName', '1.3.6.1.4.1.9.5.1.4.1.1.4', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifNumber', '1.3.6.1.2.1.2.1.0', 'standard', 'mib-II');

DELETE FROM snmpoid WHERE snmpoidid='portVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portVlan', '1.3.6.1.4.1.9.5.1.9.3.1.3', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='3cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('3cSerial', '1.3.6.1.4.1.43.10.27.1.1.1.13', 'Serial number', '3com');

DELETE FROM snmpoid WHERE snmpoidid='ospfIfMetricMetric';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ospfIfMetricMetric', '1.3.6.1.2.1.14.8.1.4', 'cgw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='ifTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('ifTrunk', '1.3.6.1.4.1.9.9.46.1.6.1.1.13', 'cL3-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='iosTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('iosTrunk', '1.3.6.1.4.1.9.9.87.1.4.1.1.6.0', 'ios-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='cMenuPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuPortType', '1.3.6.1.4.1.9.5.14.4.1.1.41', 'Port type, media', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='cMenuDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('cMenuDuplex', '1.3.6.1.4.1.9.5.14.4.1.1.5', 'Port duplex state', 'Cisco');

DELETE FROM snmpoid WHERE snmpoidid='portTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('portTrunk', '1.3.6.1.4.1.9.5.1.9.3.1.8', 'cat-sw', NULL);

DELETE FROM snmpoid WHERE snmpoidid='moduleMon';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource) VALUES ('moduleMon', '1.3.6.1.2.1.2.2.1.1', 'Used by the module monitor; is identical to ifIndex', 'mib-II');

