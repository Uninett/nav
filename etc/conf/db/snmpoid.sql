
-- 3Com

DELETE FROM snmpoid WHERE oidkey='3cPS40PortState';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cPS40PortState', '1.3.6.1.2.1.26.1.1.1.6','3com','Port state for 3Com PS40');

DELETE FROM snmpoid WHERE oidkey='3cIfMauType';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cIfMauType', '1.3.6.1.2.1.26.2.1.1.3','3com','Speed and dupelx for SWxx00');

DELETE FROM snmpoid WHERE oidkey='3cMac';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cMac', '1.3.6.1.4.1.43.10.27.1.1.1.2','3com','MACs on this port');

DELETE FROM snmpoid WHERE oidkey='3cModel';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cModel', '1.3.6.1.4.1.43.10.27.1.1.1.19','3com','Model');

DELETE FROM snmpoid WHERE oidkey='3cDescr';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cDescr', '1.3.6.1.4.1.43.10.27.1.1.1.5','3com','Description');

DELETE FROM snmpoid WHERE oidkey='3cIfDescr';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, decodehex, match_regex, descr) VALUES ('3cIfDescr', '1.3.6.1.2.1.2.2.1.2','3com','t','.*Port (\\d+)\\b.*','3Com ifDescr for port and unit');

DELETE FROM snmpoid WHERE oidkey='3cSerial';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cSerial', '1.3.6.1.4.1.43.10.27.1.1.1.13','3com','Serial number');

DELETE FROM snmpoid WHERE oidkey='3cHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cHwVer', '1.3.6.1.4.1.43.10.27.1.1.1.11','3com','Hardware version number');

DELETE FROM snmpoid WHERE oidkey='3cSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('3cSwVer', '1.3.6.1.4.1.43.10.27.1.1.1.12','3com','Software version number');


-- Cisco switch

DELETE FROM snmpoid WHERE oidkey='c1900Duplex';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('c1900Duplex', '1.3.6.1.4.1.437.1.1.3.3.1.1.8','Cisco','Duplex status');

DELETE FROM snmpoid WHERE oidkey='c1900Portname';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('c1900Portname', '1.3.6.1.4.1.437.1.1.3.3.1.1.3','Cisco','Portname');


DELETE FROM snmpoid WHERE oidkey='cMenuIfIndex';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuIfIndex', '1.3.6.1.4.1.9.5.14.4.1.1.4','Cisco','Ifindex to port mapping');

DELETE FROM snmpoid WHERE oidkey='cMenuPortStatus';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuPortStatus', '1.3.6.1.4.1.9.5.14.4.1.1.29','Cisco','Port state, up or down');

DELETE FROM snmpoid WHERE oidkey='cMenuPortType';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuPortType', '1.3.6.1.4.1.9.5.14.4.1.1.41','Cisco','Port type, media');

DELETE FROM snmpoid WHERE oidkey='cMenuDuplex';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuDuplex', '1.3.6.1.4.1.9.5.14.4.1.1.5','Cisco','Port duplex state');

DELETE FROM snmpoid WHERE oidkey='cMenuTrunk';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuTrunk', '1.3.6.1.4.1.9.5.14.4.1.1.44','Cisco','Port trunk state');

DELETE FROM snmpoid WHERE oidkey='cMenuVlan';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cMenuVlan', '1.3.6.1.4.1.9.5.14.8.1.1.3','Cisco','Port trunk state');

-- Cisco router

DELETE FROM snmpoid WHERE oidkey='cCardIndex';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardIndex', '1.3.6.1.4.1.9.3.6.11.1.1','Cisco','Slot card type');

DELETE FROM snmpoid WHERE oidkey='cCardDescr';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardDescr', '1.3.6.1.4.1.9.3.6.11.1.3','Cisco','Slot card description');

DELETE FROM snmpoid WHERE oidkey='cCardSerial';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardSerial', '1.3.6.1.4.1.9.3.6.11.1.4','Cisco','Slot card serial');

DELETE FROM snmpoid WHERE oidkey='cCardHwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardHwVersion', '1.3.6.1.4.1.9.3.6.11.1.5','Cisco','Slot card hardware version');

DELETE FROM snmpoid WHERE oidkey='cCardSwVersion';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardSwVersion', '1.3.6.1.4.1.9.3.6.11.1.6','Cisco','Slot card software version');

DELETE FROM snmpoid WHERE oidkey='cCardSlotNumber';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('cCardSlotNumber', '1.3.6.1.4.1.9.3.6.11.1.7','Cisco','Slot card slotnumber mapping');

-- HP switch

DELETE FROM snmpoid WHERE oidkey='hpStack';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpStack', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1','hp','Lists modules in the stack');

DELETE FROM snmpoid WHERE oidkey='hpSerial';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpSerial', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1','hp','Serial number');

DELETE FROM snmpoid WHERE oidkey='hpHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpHwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.4.0','hp','Hardware version number');

DELETE FROM snmpoid WHERE oidkey='hpSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpSwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.3.0','hp','Software version number');

DELETE FROM snmpoid WHERE oidkey='hpPortType';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpPortType', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2','hp','Type of each port (media, duplex)');

DELETE FROM snmpoid WHERE oidkey='hpVlan';
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, descr) VALUES ('hpVlan', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1','hp','Vlan for each port');

