--
-- Automated dump by dumpsnmpoid.py initiated at 2005-07-05 11:10:01 GMT
--
BEGIN;
DELETE FROM snmpoid WHERE oidkey='3c9300Mac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3c9300Mac','1.3.6.1.4.1.43.29.4.10.8.1.5.1','Bridge table for 3Com SuperStack 1900','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3c9300Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3c9300Serial','1.3.6.1.4.1.43.29.4.18.2.1.7.1','3com9300',NULL,'0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cDescr','1.3.6.1.4.1.43.10.27.1.1.1.5','Description','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cHubMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cHubMac','1.3.6.1.4.1.43.10.9.5.1.6','Bridge table for 3Com HUBs','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cHwVer','1.3.6.1.4.1.43.10.27.1.1.1.11','Hardware version number','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cIfDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cIfDescr','1.3.6.1.2.1.2.2.1.2','3Com ifDescr for port and unit','3com','1',E'.*(Unit|Port) (\\d+)\\b.*','1','ifDescr','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='3cIfMauType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cIfMauType','1.3.6.1.2.1.26.2.1.1.3','Speed and dupelx for SWxx00','3com','1',NULL,'0','ifMauType','MAU-MIB');

DELETE FROM snmpoid WHERE oidkey='3cMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cMac','1.3.6.1.4.1.43.10.27.1.1.1.2','MACs on this port','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cModel','1.3.6.1.4.1.43.10.27.1.1.1.19','Model','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cPS40PortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cPS40PortState','1.3.6.1.2.1.26.1.1.1.6','Port state for 3Com PS40','3com','1',NULL,'0','rpMauMediaAvailable','MAU-MIB');

DELETE FROM snmpoid WHERE oidkey='3cSSMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cSSMac','1.3.6.1.4.1.43.10.22.2.1.3','Bridge table for 3Com SuperStack','3com','1',NULL,'0','secureAddrMAC','SECURITY-MIB');

DELETE FROM snmpoid WHERE oidkey='3cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cSerial','1.3.6.1.4.1.43.10.27.1.1.1.13','Serial number','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3cSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3cSwVer','1.3.6.1.4.1.43.10.27.1.1.1.12','Software version number','3com','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='3comModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('3comModules','1.3.6.1.4.1.43.10.27.1.1.1.12','unitChange',NULL,'1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='basePortIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('basePortIfIndex','1.3.6.1.2.1.17.1.4.1.2','Port ifindex mapping','bridge-mib','1',NULL,'0','dot1dBasePortIfIndex','BRIDGE-MIB');

DELETE FROM snmpoid WHERE oidkey='c1900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c1900Bandwidth','1.3.6.1.4.1.437.1.1.3.7.1.0','','Cricket','0',NULL,'0','bandwidthUsageCurrent','ESSWITCH.MIB');

DELETE FROM snmpoid WHERE oidkey='c1900BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c1900BandwidthMax','1.3.6.1.4.1.437.1.1.3.7.5.0','','Cricket','0',NULL,'0','bandwidthUsageCurrentPeakEntry','ESSWITCH.MIB');

DELETE FROM snmpoid WHERE oidkey='c1900Duplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c1900Duplex','1.3.6.1.4.1.437.1.1.3.3.1.1.8','Duplex status','Cisco','1',NULL,'0','swPortFullDuplex','ESSWITCH.MIB');

DELETE FROM snmpoid WHERE oidkey='c1900Portname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c1900Portname','1.3.6.1.4.1.437.1.1.3.3.1.1.3','Portname','Cisco','1',NULL,'0','swPortName','ESSWITCH.MIB');

DELETE FROM snmpoid WHERE oidkey='c2900Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c2900Bandwidth','1.3.6.1.4.1.9.9.87.1.5.1.0','','Cricket','0',NULL,'0','c2900BandwidthUsageCurrent','CISCO-C2900-MIB');

DELETE FROM snmpoid WHERE oidkey='c5000Bandwidth';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c5000Bandwidth','1.3.6.1.4.1.9.5.1.1.8.0','','Cricket','0',NULL,'0','sysTraffic','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='c5000BandwidthMax';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('c5000BandwidthMax','1.3.6.1.4.1.9.5.1.1.19.0','','Cricket','0',NULL,'0','sysTrafficPeak','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardContainedByIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardContainedByIndex','1.3.6.1.4.1.9.3.6.11.1.8','cardIndex of the parent card which directly contains this card, or 0 if contained by the chassis','Cisco','1',NULL,'0',NULL,'OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardDescr','1.3.6.1.4.1.9.3.6.11.1.3','Slot card description','Cisco','1',NULL,'0','cardDescr','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardHwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardHwVersion','1.3.6.1.4.1.9.3.6.11.1.5','Slot card hardware version','Cisco','1',NULL,'0','cardHwVersion','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardIndex','1.3.6.1.4.1.9.3.6.11.1.1','Slot card type','Cisco','1',NULL,'0','cardIndex','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardSerial','1.3.6.1.4.1.9.3.6.11.1.4','Slot card serial','Cisco','1',E'[^0]|\\w{2,}','0','cardSerial','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardSlotNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardSlotNumber','1.3.6.1.4.1.9.3.6.11.1.7','Slot card slotnumber mapping','Cisco','1',NULL,'0','cardSlotNumber','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cCardSwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cCardSwVersion','1.3.6.1.4.1.9.3.6.11.1.6','Slot card software version','Cisco','1',NULL,'0','cardSwVersion','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cChassisId';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cChassisId','1.3.6.1.4.1.9.3.6.3','Cisco',NULL,'1',NULL,'0','chassisId','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cChassisSlots';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cChassisSlots','1.3.6.1.4.1.9.3.6.12','Cisco',NULL,'1',NULL,'0','chassisSlots','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cChassisType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cChassisType','1.3.6.1.4.1.9.3.6.1','Cisco',NULL,'1',NULL,'0','chassisType','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cChassisVersion';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cChassisVersion','1.3.6.1.4.1.9.3.6.2','Cisco',NULL,'1',NULL,'0','chassisVersion','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cDescr','1.3.6.1.4.1.9.3.6.11.1.3','cgw',NULL,'1',NULL,'0','cardDescr','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cHsrpGrpStandbyState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cHsrpGrpStandbyState','1.3.6.1.4.1.9.9.106.1.2.1.1.15','cgw',NULL,'1',NULL,'0','cHsrpGrpStandbyState','CISCO-HSRP-MIB');

DELETE FROM snmpoid WHERE oidkey='cHsrpGrpVirtualIpAddr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cHsrpGrpVirtualIpAddr','1.3.6.1.4.1.9.9.106.1.2.1.1.11','cgw',NULL,'1',NULL,'0','cHsrpGrpVirtualIpAddr','CISCO-HSRP-MIB');

DELETE FROM snmpoid WHERE oidkey='cHw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cHw','1.3.6.1.4.1.9.3.6.11.1.5','cgw',NULL,'1',NULL,'0','cardHwVersion','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cInetNetToMediaPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cInetNetToMediaPhysAddress','1.3.6.1.4.1.9.10.86.1.1.3.1.3','ARP cache',NULL,'1',NULL,'0','cInetNetToMediaPhysAddress','CISCO-IETF-IP-MIB');

DELETE FROM snmpoid WHERE oidkey='cIpAddressIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cIpAddressIfIndex','1.3.6.1.4.1.9.10.86.1.1.2.1.3','cgw',NULL,'1',NULL,'0','cIpAddressIfIndex','CISCO-IETF-IP-MIB');

DELETE FROM snmpoid WHERE oidkey='cIpAddressPrefix';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cIpAddressPrefix','1.3.6.1.4.1.9.10.86.1.1.2.1.5','cgw',NULL,'1',NULL,'0','cIpAddressPrefix','CISCO-IETF-IP-MIB');

DELETE FROM snmpoid WHERE oidkey='cL3FwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cL3FwVer','1.3.6.1.4.1.9.9.92.1.1.1.7','Firmware version','cL3','1',NULL,'0',NULL,'CISCO-ENTITY-ASSET-MIB');

DELETE FROM snmpoid WHERE oidkey='cL3HwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cL3HwVer','1.3.6.1.4.1.9.9.92.1.1.1.4','Hardware version','cL3','1',NULL,'0','ceAssetHardwareRevision','CISCO-ENTITY-ASSET-MIB');

DELETE FROM snmpoid WHERE oidkey='cL3Model';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cL3Model','1.3.6.1.4.1.9.9.92.1.1.1.3','Model number','cL3','1',NULL,'0','ceAssetOrderablePartNumber','CISCO-ENTITY-ASSET-MIB');

DELETE FROM snmpoid WHERE oidkey='cL3Serial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cL3Serial','1.3.6.1.4.1.9.9.92.1.1.1.2','Serial number','cL3','1',NULL,'0','ceAssetSerialNumber','CISCO-ENTITY-ASSET-MIB');

DELETE FROM snmpoid WHERE oidkey='cL3SwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cL3SwVer','1.3.6.1.4.1.9.9.92.1.1.1.8','Software version','cL3','1',NULL,'0','ceAssetFirmwareRevision','CISCO-ENTITY-ASSET-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuDuplex','1.3.6.1.4.1.9.5.14.4.1.1.5','Port duplex state','Cisco','1',NULL,'0','ciscoEsPortDuplex','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuIfIndex','1.3.6.1.4.1.9.5.14.4.1.1.4','Ifindex to port mapping','Cisco','1',NULL,'0','ciscoEsPortIfIndex','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuMac';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuMac','1.3.6.1.4.1.9.5.14.4.3.1.4.1','Bridge table for Cisco menu type switch','cisco','1',NULL,'0','ciscoEsPortStnLocation','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuPortStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuPortStatus','1.3.6.1.4.1.9.5.14.4.1.1.29','Port state, up or down','Cisco','1',NULL,'0','ciscoEsPortLinkState','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuPortType','1.3.6.1.4.1.9.5.14.4.1.1.41','Port type, media','Cisco','1',NULL,'0','ciscoEsPortType','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuTrunk','1.3.6.1.4.1.9.5.14.4.1.1.44','Port trunk state','Cisco','1',NULL,'0','ciscoEsPortISLOperStatus','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cMenuVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cMenuVlan','1.3.6.1.4.1.9.5.14.8.1.1.3','Port trunk state','Cisco','1',NULL,'0','ciscoEsVLANPortPorts','CISCO-ES-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='cModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cModel','1.3.6.1.4.1.9.3.6.11.1.2','cgw',NULL,'1',NULL,'0','cardType','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cSerial','1.3.6.1.4.1.9.3.6.3','cgw',NULL,'1',NULL,'0','chassisId','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='cSw';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cSw','1.3.6.1.4.1.9.3.6.11.1.6','cgw',NULL,'1',NULL,'0','cardSwVersion','OLD-CISCO-CHASSIS-MIB');

DELETE FROM snmpoid WHERE oidkey='catModuleFwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catModuleFwVer','1.3.6.1.4.1.9.5.1.3.1.1.19','Module firmware version','cat','1',NULL,'0',NULL,'CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='catModuleHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catModuleHwVer','1.3.6.1.4.1.9.5.1.3.1.1.18','Module hardware version','cat','1',NULL,'0',NULL,'CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='catModuleModel';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catModuleModel','1.3.6.1.4.1.9.5.1.3.1.1.17','Module model','cat','1',NULL,'0',NULL,'CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='catModuleSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catModuleSerial','1.3.6.1.4.1.9.5.1.3.1.1.26','Serial number','cat','1',NULL,'0',NULL,'CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='catModuleSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catModuleSwVer','1.3.6.1.4.1.9.5.1.3.1.1.20','Module software version','cat','1',NULL,'0',NULL,'CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='catSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('catSerial','1.3.6.1.4.1.9.5.1.2.19','Serial number','cat','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='cdpNeighbour';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cdpNeighbour','1.3.6.1.4.1.9.9.23.1.2.1.1.6','CDP neighbour','cisco','1',NULL,'0','cdpCacheDeviceId','CISCO-CDP-MIB');

DELETE FROM snmpoid WHERE oidkey='cdpRemoteIf';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cdpRemoteIf','1.3.6.1.4.1.9.9.23.1.2.1.1.7','CDP remote interface','cisco','1',NULL,'0','cdpCacheDevicePort','CISCO-CDP-MIB');

DELETE FROM snmpoid WHERE oidkey='cpu1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cpu1min','1.3.6.1.4.1.9.2.1.57.0','','Cricket','0',NULL,'0','avgBusy1','OLD-CISCO-CPU-MIB');

DELETE FROM snmpoid WHERE oidkey='cpu5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('cpu5min','1.3.6.1.4.1.9.2.1.58.0','','Cricket','0',NULL,'0','avgBusy5','OLD-CISCO-CPU-MIB');

DELETE FROM snmpoid WHERE oidkey='dnscheck';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('dnscheck','1.3.6.1.2.1.1.5.0','Used by the DNSCheck plugin; is identical to sysname','mib-II','0',NULL,'1','sysName','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='flashFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('flashFree','1.3.6.1.4.1.9.9.10.1.1.4.1.1.5','Flash free','cisco','1',NULL,'0','ciscoFlashPartitionFreeSpace','CISCO-FLASH-MIB');

DELETE FROM snmpoid WHERE oidkey='flashName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('flashName','1.3.6.1.4.1.9.9.10.1.1.4.1.1.10','Flash name','cisco','1',NULL,'0',' ciscoFlashPartitionName','CISCO-FLASH-MIB');

DELETE FROM snmpoid WHERE oidkey='flashSize';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('flashSize','1.3.6.1.4.1.9.9.10.1.1.4.1.1.4','Flash size','cisco','1',NULL,'0','ciscoFlashPartitionSize','CISCO-FLASH-MIB');

DELETE FROM snmpoid WHERE oidkey='hpFwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpFwVer','1.3.6.1.4.1.11.2.14.11.5.1.1.4.0','Firmware revision number','hp','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpModules';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpModules','1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.4','unitChange','hp','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpPortType','1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2','Type of each port (media, duplex)','hp','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpStack';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpStack','1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1','Lists modules in the stack','hp','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpStackName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpStackName','1.3.6.1.4.1.11.2.14.11.5.1.10.3.1.0','Name of stack','hp','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpStackStatsMemberOperStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpStackStatsMemberOperStatus','1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.5','HP stack member status','hp','1',NULL,'0','hpStackStatsMemberOperStatus','HP-MIB');

DELETE FROM snmpoid WHERE oidkey='hpSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpSwVer','1.3.6.1.4.1.11.2.14.11.5.1.1.3.0','Software version number','hp','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpVlan','1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1','Vlan for each port','hp','1',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpcpu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpcpu','1.3.6.1.4.1.11.2.14.11.5.1.9.6.1.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpmem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpmem5minFree','1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6.1','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='hpmem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('hpmem5minUsed','1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.7.1','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ifAdminStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifAdminStatus','1.3.6.1.2.1.2.2.1.7','standard','mib-II','1',NULL,'0','ifAdminStatus','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifAlias';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifAlias','1.3.6.1.2.1.31.1.1.1.18','standard','mib-II','1',NULL,'0','ifAlias','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifDescr','1.3.6.1.2.1.2.2.1.2','standard','mib-II','1',NULL,'0','ifDescr','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifHCInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifHCInOctets','1.3.6.1.2.1.31.1.1.1.6','The total number of octets received on the interface, including framing characters. This object is a 64-bit version of ifInOctets.','mib-II','1',NULL,'0','ifHCInOctets','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifHCInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifHCInUcastPkts','1.3.6.1.2.1.31.1.1.1.7','','mib-II','1',NULL,'0','ifHCInUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifHCOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifHCOutOctets','1.3.6.1.2.1.31.1.1.1.10','The total number of octets transmitted out of the interface, including framing characters. This object is a 64-bit version of ifOutOctets.','mib-II','1',NULL,'0','ifHCOutOctets','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifHCOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifHCOutUcastPkts','1.3.6.1.2.1.31.1.1.1.11','','mib-II','1',NULL,'0','ifHCOutUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInDiscards','1.3.6.1.2.1.2.2.1.13','','mib-II','1',NULL,'0','ifInDiscards','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInErrors','1.3.6.1.2.1.2.2.1.14','Number of inbound packets that contained errors','mib-II','1',NULL,'0','ifInErrors','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInNUcastPkts','1.3.6.1.2.1.2.2.1.12','','mib-II','1',NULL,'0','ifInNUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInOctets','1.3.6.1.2.1.2.2.1.10','Number of octets received on the interface','mib-II','1',NULL,'0','ifInOctets','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInUcastPkts','1.3.6.1.2.1.2.2.1.11','Packets which were not addressed to a multicast or broadcast address at this sub-layer','mib-II','1',NULL,'0','ifInUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifInUnknownProtos';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifInUnknownProtos','1.3.6.1.2.1.2.2.1.15','','mib-II','1',NULL,'0','ifInUnknownProtos','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifIndex','1.3.6.1.2.1.2.2.1.1','standard','mib-II','1',NULL,'0','ifIndex','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifLastChange';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifLastChange','1.3.6.1.2.1.2.2.1.9','standard','mib-II','1',NULL,'0','ifLastChange','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifMtu';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifMtu','1.3.6.1.2.1.2.2.1.4','standard','mib-II','1',NULL,'0','ifMtu','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifName','1.3.6.1.2.1.31.1.1.1.1','standard','mib-II','1',NULL,'0','ifName','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifNumber';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifNumber','1.3.6.1.2.1.2.1.0','standard','mib-II','0',NULL,'0','ifNumber','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOperStatus';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOperStatus','1.3.6.1.2.1.2.2.1.8','standard','mib-II','1',NULL,'0','ifOperStatus','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutDiscards';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutDiscards','1.3.6.1.2.1.2.2.1.19','','mib-II','1',NULL,'0','ifOutDiscards','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutErrors';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutErrors','1.3.6.1.2.1.2.2.1.20','Number of outbound packets that could not be transmitted because of errors','mib-II','1',NULL,'0','ifOutErrors','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutNUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutNUcastPkts','1.3.6.1.2.1.2.2.1.18','','mib-II','1',NULL,'0','ifOutNUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutOctets';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutOctets','1.3.6.1.2.1.2.2.1.16','Number of octets transmitted out of the interface','mib-II','1',NULL,'0','ifOutOctets','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutQLen';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutQLen','1.3.6.1.2.1.2.2.1.21','','mib-II','1',NULL,'0','ifOutQLen','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifOutUcastPkts';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifOutUcastPkts','1.3.6.1.2.1.2.2.1.17','Packets that higher-level protocols requested be transmitted, and which were not addressed to a multicast or broadcast address at this sub-layer','mib-II','1',NULL,'0','ifOutUcastPkts','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifPhysAddress','1.3.6.1.2.1.2.2.1.6','standard','mib-II','1',NULL,'0','ifPhysAddress','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifPortName','1.3.6.1.4.1.9.2.2.1.1.28','ios-sw',NULL,'1',NULL,'0','locIfDescr','OLD-CISCO-INTERFACES-MIB');

DELETE FROM snmpoid WHERE oidkey='ifSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifSerial','1.3.6.1.2.1.47.1.1.1.1.11.1','standard',NULL,'0',NULL,'0','entPhysicalSerialNum','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='ifSpeed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifSpeed','1.3.6.1.2.1.2.2.1.5','standard','mib-II','1',NULL,'0','ifSpeed','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifHighSpeed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifHighSpeed','1.3.6.1.2.1.31.1.1.1.15','Interface speed as a number of Mbps','mib-II','1',NULL,'0','ifHighSpeed','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifTrunk','1.3.6.1.4.1.9.9.46.1.6.1.1.14','cL3-sw',NULL,'1',NULL,'0','vlanTrunkPortDynamicStatus','CISCO-VTP-MIB');

DELETE FROM snmpoid WHERE oidkey='ifType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifType','1.3.6.1.2.1.2.2.1.3','standard','mib-II','1',NULL,'0','ifType','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ifVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifVlan','1.3.6.1.4.1.9.9.68.1.2.2.1.2','ios-sw',NULL,'1',NULL,'0','vmVlan','CISCO-VLAN-MEMBERSHIP-MIB');

DELETE FROM snmpoid WHERE oidkey='ifVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ifVlansAllowed','1.3.6.1.4.1.9.9.46.1.6.1.1.4','cL3-sw',NULL,'1',NULL,'0','vlanTrunkPortVlansEnabled','CISCO-VTP-MIB');

DELETE FROM snmpoid WHERE oidkey='iosDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('iosDuplex','1.3.6.1.4.1.9.9.87.1.4.1.1.32.0','ios-sw',NULL,'1',NULL,'0','c2900PortDuplexStatus','CISCO-C2900-MIB');

DELETE FROM snmpoid WHERE oidkey='iosPortIfindex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('iosPortIfindex','1.3.6.1.4.1.9.9.87.1.4.1.1.25.0','ios-sw',NULL,'1',NULL,'0','c2900PortIfIndex','CISCO-C2900-MIB');

DELETE FROM snmpoid WHERE oidkey='iosTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('iosTrunk','1.3.6.1.4.1.9.9.87.1.4.1.1.6.0','ios-sw',NULL,'1',NULL,'0','c2900PortMayForwardFrames','CISCO-C2900-MIB');

DELETE FROM snmpoid WHERE oidkey='ipAdEntIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipAdEntIfIndex','1.3.6.1.2.1.4.20.1.2','cgw',NULL,'1',NULL,'0','ipAdEntIfIndex','IP-MIB');

DELETE FROM snmpoid WHERE oidkey='ipAdEntIfNetMask';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipAdEntIfNetMask','1.3.6.1.2.1.4.20.1.3','cgw',NULL,'1',NULL,'0','ipAdEntNetMas','IP-MIB');

DELETE FROM snmpoid WHERE oidkey='ipNetToMediaPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipNetToMediaPhysAddress','1.3.6.1.2.1.4.22.1.2','ARP cache','mib-II','1',NULL,'0','ipNetToMediaPhysAddress','RFC1213-MIB');

DELETE FROM snmpoid WHERE oidkey='ipRouteDest';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteDest','1.3.6.1.2.1.4.21.1.1','The destination IP address of this route',NULL,'1',NULL,'0','ipRouteDest','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipRouteIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteIfIndex','1.3.6.1.2.1.4.21.1.2','The index value which uniquely identifies the local interface through which the next hop of this route should be reached',NULL,'1',NULL,'0','ipRouteIfIndex','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipRouteMask';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteMask','1.3.6.1.2.1.4.21.1.11','Indicate the mask to be logical-ANDed with the destination address before being compared to the value in the ipRouteDest field',NULL,'1',NULL,'0','ipRouteMask','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipRouteNextHop';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteNextHop','1.3.6.1.2.1.4.21.1.7','The IP address of the next hop of this route',NULL,'1',NULL,'0','ipRouteNextHop','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipRouteProto';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteProto','1.3.6.1.2.1.4.21.1.9','The routing mechanism via which this route was learned',NULL,'1',NULL,'0','ipRouteProto','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipRouteType';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipRouteType','1.3.6.1.2.1.4.21.1.8','The type of route, 1=other, 2=invalid, 3=direct, 4=indirect',NULL,'1',NULL,'0','ipRouteType','RFC1213');

DELETE FROM snmpoid WHERE oidkey='ipv6AddrPfxLength';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipv6AddrPfxLength','1.3.6.1.2.1.55.1.8.1.2','Prefices','IPV6-MIB','1',NULL,'0','ipv6AddrPfxLength','IPV6-MIB');

DELETE FROM snmpoid WHERE oidkey='ipv6NetToMediaPhysAddress';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ipv6NetToMediaPhysAddress','1.3.6.1.2.1.55.1.12.1.2','ARP cache','IPV6-MIB','1',NULL,'0','ipv6NetToMediaPhysAddress','IPV6-MIB');

DELETE FROM snmpoid WHERE oidkey='macPortEntry';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('macPortEntry','1.3.6.1.2.1.17.4.3.1.2','Bridge table for various switches','bridge-mib','1',NULL,'0','dot1dTpFdbPort','BRIDGE-MIB');

DELETE FROM snmpoid WHERE oidkey='mem5minFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('mem5minFree','1.3.6.1.4.1.9.9.48.1.1.1.6.1','','Cricket','0',NULL,'0','ciscoMemoryPoolFree','CISCO-MEMORY-POOL-MIB');

DELETE FROM snmpoid WHERE oidkey='mem5minUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('mem5minUsed','1.3.6.1.4.1.9.9.48.1.1.1.5.1','','Cricket','0',NULL,'0','ciscoMemoryPoolUsed','CISCO-MEMORY-POOL-MIB');

DELETE FROM snmpoid WHERE oidkey='memFree';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('memFree','1.3.6.1.4.1.9.9.48.1.1.1.6','Mem free','cisco','1',NULL,'0','ciscoMemoryPoolFree','CISCO-MEMORY-POOL-MIB');

DELETE FROM snmpoid WHERE oidkey='memName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('memName','1.3.6.1.4.1.9.9.48.1.1.1.2','Mem name','cisco','1',NULL,'0','ciscoMemoryPoolName','CISCO-MEMORY-POOL-MIB');

DELETE FROM snmpoid WHERE oidkey='memUsed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('memUsed','1.3.6.1.4.1.9.9.48.1.1.1.5','Mem used','cisco','1',NULL,'0','ciscoMemoryPoolUsed','CISCO-MEMORY-POOL-MIB');

DELETE FROM snmpoid WHERE oidkey='moduleMon';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('moduleMon','1.3.6.1.2.1.2.2.1.1','Used by the module monitor; is identical to ifIndex','mib-II','1',NULL,'0','ifIndex','IF-MIB');

DELETE FROM snmpoid WHERE oidkey='ospfIfMetricMetric';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ospfIfMetricMetric','1.3.6.1.2.1.14.8.1.4','cgw',NULL,'1',NULL,'0','ospfIfMetricValue','OSPF-MIB');

DELETE FROM snmpoid WHERE oidkey='physClass';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physClass','1.3.6.1.2.1.47.1.1.1.1.5','An indication of the general hardware type of the physical entity','mib-II','1',NULL,'0','entPhysicalClass','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physContainedIn';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physContainedIn','1.3.6.1.2.1.47.1.1.1.1.4','The value of entPhysicalIndex for the physical entity which contains this physical entity','mib-II','1',NULL,'0','entPhysicalContainedIn','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physDescr','1.3.6.1.2.1.47.1.1.1.1.2','A textual description of physical entity','mib-II','1',NULL,'0','entPhysicalDescr','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physFwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physFwVer','1.3.6.1.2.1.47.1.1.1.1.9','The vendor-specific firmware revision string for the physical entity','mib-II','1',NULL,'0','entPhysicalFirmwareRev','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physHwVer','1.3.6.1.2.1.47.1.1.1.1.8','The vendor-specific hardware revision string for the physical entity','mib-II','1',NULL,'0','entPhysicalHardwareRev','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physMfgName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physMfgName','1.3.6.1.2.1.47.1.1.1.1.12','The name of the manufacturer of this physical component','mib-II','1',NULL,'0','entPhysicalMfgName','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physModelName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physModelName','1.3.6.1.2.1.47.1.1.1.1.13','The vendor-specific model name identifier string associated with this physical component','mib-II','1',NULL,'0','entPhysicalModelName','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physName','1.3.6.1.2.1.47.1.1.1.1.7','The textual name of the physical entity','mib-II','1',NULL,'0','entPhysicalName','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physParentRelPos';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physParentRelPos','1.3.6.1.2.1.47.1.1.1.1.6','','mib-II','1',NULL,'0','entPhysicalParentRelPos','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physSerial','1.3.6.1.2.1.47.1.1.1.1.11','The vendor-specific serial number string for the physical entity','mib-II','1',NULL,'0','entPhysicalSerialNum','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='physSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('physSwVer','1.3.6.1.2.1.47.1.1.1.1.10','The vendor-specific software revision string for the physical entity','mib-II','1',NULL,'0','entPhysicalSoftwareRev','ENTITY-MIB');

DELETE FROM snmpoid WHERE oidkey='portDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portDuplex','1.3.6.1.4.1.9.5.1.4.1.1.10','cat-sw',NULL,'1',NULL,'0','portDuplex','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='portIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portIfIndex','1.3.6.1.4.1.9.5.1.4.1.1.11','cat-sw',NULL,'1',NULL,'0','portIfIndex','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='portPortName';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portPortName','1.3.6.1.4.1.9.5.1.4.1.1.4','cat-sw',NULL,'1',NULL,'0','portName','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='portTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portTrunk','1.3.6.1.4.1.9.5.1.9.3.1.8','cat-sw',NULL,'1',NULL,'0','vlanPortIslOperStatus','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='portVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portVlan','1.3.6.1.4.1.9.5.1.9.3.1.3','cat-sw',NULL,'1',NULL,'0','vlanPortVlan','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='portVlansAllowed';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('portVlansAllowed','1.3.6.1.4.1.9.5.1.9.3.1.5','cat-sw',NULL,'1',NULL,'0','vlanPortIslVlansAllowed','CISCO-STACK-MIB');

DELETE FROM snmpoid WHERE oidkey='stpPortState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('stpPortState','1.3.6.1.2.1.17.2.15.1.3','Spanning tree port state','bridge-mib','1',NULL,'0','dot1dStpPortState','BRIDGE-MIB');

DELETE FROM snmpoid WHERE oidkey='sysDescr';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('sysDescr','1.3.6.1.2.1.1.1.0','','mib-II','0',NULL,'0','sysDescr','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='sysLocation';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('sysLocation','1.3.6.1.2.1.1.6','System location','mib-II','1',NULL,'0','sysLocation','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='sysUpTime';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('sysUpTime','1.3.6.1.2.1.1.3.0','','mib-II','0',NULL,'0','sysUpTime','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='sysname';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('sysname','1.3.6.1.2.1.1.5.0','all',NULL,'0',NULL,'0','sysName','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='tempInlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('tempInlet','1.3.6.1.4.1.9.9.13.1.3.1.3.1','','Cricket','0',NULL,'0','ciscoEnvMonTemperatureStatusValue','CISCO-ENVMON-MIB');

DELETE FROM snmpoid WHERE oidkey='tempOutlet';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('tempOutlet','1.3.6.1.4.1.9.9.13.1.3.1.3.3','','Cricket','0',NULL,'0','ciscoEnvMonTemperatureStatusValue','CISCO-ENVMON-MIB');

DELETE FROM snmpoid WHERE oidkey='typeoid';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('typeoid','1.3.6.1.2.1.1.2.0','all',NULL,'0',NULL,'0','sysObjectID','SNMPv2-MIB');

DELETE FROM snmpoid WHERE oidkey='ucd_cpuIdle';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_cpuIdle','1.3.6.1.4.1.2021.11.11.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_cpuSystem';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_cpuSystem','1.3.6.1.4.1.2021.11.10.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_cpuUser';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_cpuUser','1.3.6.1.4.1.2021.11.9.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_load15min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_load15min','1.3.6.1.4.1.2021.10.1.3.3','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_load1min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_load1min','1.3.6.1.4.1.2021.10.1.3.1','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_load5min';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_load5min','1.3.6.1.4.1.2021.10.1.3.2','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_memrealAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_memrealAvail','1.3.6.1.4.1.2021.4.6.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_memswapAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_memswapAvail','1.3.6.1.4.1.2021.4.4.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='ucd_memtotalAvail';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('ucd_memtotalAvail','1.3.6.1.4.1.2021.4.11.0','','Cricket','0',NULL,'0',NULL,NULL);

DELETE FROM snmpoid WHERE oidkey='vtpVlanState';
INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex, oidname, mib)
VALUES ('vtpVlanState','1.3.6.1.4.1.9.9.46.1.3.1.1.2','The state of this VLAN','cisco','1',NULL,'0','vtpVlanState','CISCO-VTP-MIB');

UPDATE snmpoid SET defaultfreq=3600 WHERE oidkey IN ('moduleMon', '3cPS40PortState', 'hpStackStatsMemberOperStatus');
UPDATE snmpoid SET defaultfreq=1800 WHERE oidkey IN ('ipNetToMediaPhysAddress', 'cInetNetToMediaPhysAddress', 'ipv6NetToMediaPhysAddress');

UPDATE snmpoid SET getnext=true, uptodate=true;
UPDATE netbox SET uptodate=false;

COMMIT;
