-- -*- coding: utf-8 -*-
\set ON_ERROR_STOP on

-- Add non-ASCII chars to the admin user's login name to test encoding
-- compliance for all pages
UPDATE account SET name = 'Administrator ÆØÅ' WHERE login = 'admin';

-- Add some non-ASCII test data to reveal more potential problems during
-- the shift to Python 3
INSERT INTO location (locationid) VALUES ('bø');
INSERT INTO room (roomid, locationid) VALUES ('bø-123', 'bø');

-- Add a test netbox
INSERT INTO netbox (ip, typeid, sysname, catid, orgid, roomid)
VALUES ('192.168.0.42', (SELECT typeid FROM TYPE WHERE typename = 'hp2626A'), 'test-gsw.example.org', 'GSW', 'myorg', 'bø-123');
INSERT INTO interface (netboxid, ifindex, ifname, ifdescr, iftype, speed, ifphysaddress, ifadminstatus, ifoperstatus, ifalias, vlan)
VALUES ((SELECT netboxid FROM netbox WHERE sysname='test-gsw.example.org'), 1000, '1', 'Port #1', 6, 1000, '0c:0f:fe:eb:00:b5', 1, 1, 'Uplink to space', 42);

-- Add some test prefixes
INSERT INTO vlan (nettype, netident) VALUES ('scope', 'test scope');
INSERT INTO prefix (netaddr, vlanid) VALUES ('10.0.0.0/8', (SELECT vlanid FROM vlan WHERE netident='test scope'));

INSERT INTO vlan (nettype, netident) VALUES ('lan', 'test lan');
INSERT INTO prefix (netaddr, vlanid) VALUES ('10.42.0.0/24', (SELECT vlanid FROM vlan WHERE netident='test lan'));

-- Add some arp data
INSERT INTO arp (netboxid, sysname, ip, mac, start_time)
VALUES (
    (SELECT netboxid FROM netbox WHERE sysname='test-gsw.example.org'),
    'test-gsw.example.org',
    '10.42.0.1',
    '00:00:ca:fe:ba:be',
    '2019-10-02 12:00'::TIMESTAMP);
