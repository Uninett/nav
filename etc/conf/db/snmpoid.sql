
-- HP switch

DELETE FROM snmpoid WHERE oidkey='hpStack';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpStack', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1','Lists modules in the stack');

DELETE FROM snmpoid WHERE oidkey='hpSerial';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpSerial', '1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1','Serial number');

DELETE FROM snmpoid WHERE oidkey='hpHwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpHwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.4.0','Hardware version number');

DELETE FROM snmpoid WHERE oidkey='hpSwVer';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpSwVer', '1.3.6.1.4.1.11.2.14.11.5.1.1.3.0','Software version number');

DELETE FROM snmpoid WHERE oidkey='hpPortType';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpPortType', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2','Type of each port (media, duplex)');

DELETE FROM snmpoid WHERE oidkey='hpVlan';
INSERT INTO snmpoid (oidkey, snmpoid, descr) VALUES ('hpVlan', '1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1','Vlan for each port');

