
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

