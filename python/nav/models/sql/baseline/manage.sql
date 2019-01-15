/*
=============================================
        manage
    SQL Initialization script for NAV's
    manage database.  Read the README file
    for more info.

    Run the command:
    psql manage -f manage.sql

	!! WARNING !!

	This SQL script is encoded as unicode (UTF-8), before you do make
	changes and commit, be 100% sure that your editor does not mess it up.

    Check 1 : These norwegian letters looks nice:
    ! æøåÆØÅ !
    Check 2 : This is the Euro currency sign:
    ! € !
=============================================
*/

CREATE TABLE org (
  orgid VARCHAR(30) PRIMARY KEY,
  parent VARCHAR(30),
  descr VARCHAR,
  contact VARCHAR,
  data hstore NOT NULL DEFAULT hstore(''),
  CONSTRAINT org_parent_fkey FOREIGN KEY (parent) REFERENCES org (orgid)
             ON UPDATE CASCADE
);
INSERT INTO org (orgid, descr, contact) VALUES ('myorg', 'Example organization unit', 'nobody');

CREATE TABLE usage (
  usageid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR NOT NULL
);


CREATE TABLE location (
  locationid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR DEFAULT '',
  data hstore DEFAULT hstore('') NOT NULL,
  parent VARCHAR REFERENCES location(locationid) ON UPDATE CASCADE
);
INSERT INTO location (locationid, descr) VALUES ('mylocation', 'Example location');

CREATE TABLE room (
  roomid VARCHAR(30) PRIMARY KEY,
  locationid VARCHAR(30) REFERENCES location,
  descr VARCHAR,
  position POINT,
  data hstore NOT NULL DEFAULT hstore('')
);
INSERT INTO room (roomid, locationid, descr) VALUES ('myroom', 'mylocation', 'Example wiring closet');

CREATE TABLE nettype (
  nettypeid VARCHAR PRIMARY KEY,
  descr VARCHAR,
  edit BOOLEAN DEFAULT FALSE
);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('core','core',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('dummy','dummy',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('elink','elink',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('lan','lan',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('link','link',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('loopback','loopbcak',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('reserved','reserved',TRUE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('private','private',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('scope','scope',TRUE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('static','static',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('unknown','unknow',FALSE);

CREATE TABLE vlan (
  vlanid SERIAL PRIMARY KEY,
  vlan INT4,
  nettype VARCHAR NOT NULL REFERENCES nettype(nettypeid) ON UPDATE CASCADE ON DELETE CASCADE,
  orgid VARCHAR(30) REFERENCES org,
  usageid VARCHAR(30) REFERENCES usage,
  netident VARCHAR,
  description VARCHAR
);

CREATE TABLE prefix (
  prefixid SERIAL PRIMARY KEY,
  netaddr CIDR NOT NULL,
  vlanid INT4 REFERENCES vlan ON UPDATE CASCADE ON DELETE CASCADE,
  UNIQUE(netaddr)
);

CREATE TABLE vendor (
  vendorid VARCHAR(15) PRIMARY KEY
);

CREATE TABLE cat (
  catid VARCHAR(8) PRIMARY KEY,
  descr VARCHAR,
  req_snmp BOOLEAN NOT NULL
);

INSERT INTO cat values ('GW','Routers (layer 3 device)','t');
INSERT INTO cat values ('GSW','A layer 2 and layer 3 device','t');
INSERT INTO cat values ('SW','Core switches (layer 2), typically with many vlans','t');
INSERT INTO cat values ('EDGE','Edge switch without vlans (layer 2)','t');
INSERT INTO cat values ('WLAN','Wireless equipment','t');
INSERT INTO cat values ('SRV','Server','f');
INSERT INTO cat values ('OTHER','Other equipment','f');
INSERT INTO cat VALUES ('ENV', 'Environmental probes', true);
INSERT INTO cat VALUES ('POWER', 'Power distribution equipment', true);


CREATE TABLE device (
  deviceid SERIAL PRIMARY KEY,
  serial VARCHAR,
  hw_ver VARCHAR,
  fw_ver VARCHAR,
  sw_ver VARCHAR,
  discovered TIMESTAMP NULL DEFAULT NOW(),
  UNIQUE(serial)
);

CREATE TABLE type (
  typeid SERIAL PRIMARY KEY,
  vendorid VARCHAR(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  typename VARCHAR NOT NULL,
  sysObjectID VARCHAR NOT NULL,
  descr VARCHAR,
  UNIQUE (vendorid, typename),
  UNIQUE (sysObjectID)
);

CREATE TABLE netbox (
  netboxid SERIAL PRIMARY KEY,
  ip INET NOT NULL,
  roomid VARCHAR(30) NOT NULL CONSTRAINT netbox_roomid_fkey REFERENCES room ON UPDATE CASCADE,
  typeid INT4 CONSTRAINT netbox_typeid_fkey REFERENCES type ON UPDATE CASCADE ON DELETE CASCADE,
  sysname VARCHAR UNIQUE NOT NULL,
  catid VARCHAR(8) NOT NULL CONSTRAINT netbox_catid_fkey REFERENCES cat ON UPDATE CASCADE ON DELETE CASCADE,
  orgid VARCHAR(30) NOT NULL CONSTRAINT netbox_orgid_fkey REFERENCES org ON UPDATE CASCADE,
  ro VARCHAR,
  rw VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s'), -- y=up, n=down, s=shadow
  snmp_version INT4 NOT NULL DEFAULT 2,
  upsince TIMESTAMP NOT NULL DEFAULT NOW(),
  uptodate BOOLEAN NOT NULL DEFAULT false,
  discovered TIMESTAMP NULL DEFAULT NOW(),
  data hstore DEFAULT hstore('') NOT NULL,
  UNIQUE(ip)
);

-- View to match each netbox with a prefix
-- Multiple prefixes may match netbox.ip, but only the one with the longest
-- mask is interesting.
CREATE VIEW netboxprefix AS
  SELECT netbox.netboxid,
         (SELECT prefix.prefixid
          FROM prefix
          WHERE netbox.ip << prefix.netaddr::inet
          ORDER BY masklen(prefix.netaddr::inet) DESC
          LIMIT 1) AS prefixid
  FROM netbox;

CREATE TABLE netbox_vtpvlan (
  id SERIAL,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  vtpvlan INT4,
  PRIMARY KEY(id),
  UNIQUE(netboxid, vtpvlan)
);

CREATE TABLE netboxgroup (
    netboxgroupid VARCHAR,
    descr VARCHAR NOT NULL,

    PRIMARY KEY (netboxgroupid)
);
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('AD','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('ADC','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('BACKUP','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('DNS','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('FS','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('LDAP','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('MAIL','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('NOTES','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('STORE','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('TEST','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('UNIX','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('UNIX-STUD','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('WEB','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('WIN','Description');
INSERT INTO netboxgroup (netboxgroupid,descr) VALUES ('WIN-STUD','Description');

CREATE TABLE netboxcategory (
  id SERIAL,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  category VARCHAR NOT NULL REFERENCES netboxgroup ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY(netboxid, category)
);


CREATE TABLE netboxinfo (
  netboxinfoid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  key VARCHAR,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(netboxid, key, var, val)
);

CREATE TABLE module (
  moduleid SERIAL PRIMARY KEY,
  deviceid INT4 NOT NULL REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  module INT4,
  name VARCHAR NOT NULL,
  model VARCHAR,
  descr VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n'), -- y=up, n=down
  downsince TIMESTAMP,

  CONSTRAINT module_netboxid_key UNIQUE (netboxid, name)
);

CREATE TABLE mem (
  memid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  memtype VARCHAR NOT NULL,
  device VARCHAR NOT NULL,
  size INT4 NOT NULL,
  used INT4,
  UNIQUE(netboxid, memtype, device)
);


-- New consolidated interface table
-- See MIB-II, IF-MIB, RFC 1229
CREATE TABLE interface (
  interfaceid SERIAL NOT NULL,
  netboxid INT4 NOT NULL,
  moduleid INT4,
  ifindex INT4,
  ifname VARCHAR,
  ifdescr VARCHAR,
  iftype INT4,
  speed DOUBLE PRECISION,
  ifphysaddress MACADDR,
  ifadminstatus INT4, -- 1=up, 2=down, 3=testing
  ifoperstatus INT4,  -- 1=up, 2=down, 3=testing, 4=unknown, 5=dormant, 6=notPresent, 7=lowerLayerDown
  iflastchange INT4,
  ifconnectorpresent BOOLEAN,
  ifpromiscuousmode BOOLEAN,
  ifalias VARCHAR,

  -- non IF-MIB values
  baseport INT4,  -- baseport number from BRIDGE-MIB, if any.
                  -- A non-null value should be a good indicator that this is a switch port.
  media VARCHAR,
  vlan INT4,
  trunk BOOLEAN,
  duplex CHAR(1) CHECK (duplex='f' OR duplex='h'), -- f=full, h=half

  to_netboxid INT4,
  to_interfaceid INT4,

  gone_since TIMESTAMP,

  CONSTRAINT interface_pkey PRIMARY KEY (interfaceid),
  CONSTRAINT interface_netboxid_fkey
             FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT interface_moduleid_fkey
             FOREIGN KEY (moduleid)
             REFERENCES module (moduleid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_to_netboxid_fkey
             FOREIGN KEY (to_netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_to_interfaceid_fkey
             FOREIGN KEY (to_interfaceid)
             REFERENCES interface (interfaceid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_netboxid_ifindex_unique
             UNIQUE (netboxid, ifindex)
);

-- this should be populated with entries parsed from
-- http://www.iana.org/assignments/ianaiftype-mib
CREATE TABLE iana_iftype (
  iftype INT4 NOT NULL,
  name VARCHAR NOT NULL,
  descr VARCHAR,

  CONSTRAINT iftype_pkey PRIMARY KEY (iftype)
);

CREATE TABLE gwportprefix (
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  prefixid INT4 NOT NULL REFERENCES prefix ON UPDATE CASCADE ON DELETE CASCADE,
  gwip INET NOT NULL,
  virtual BOOL NOT NULL DEFAULT false,
  UNIQUE(gwip)
);

-- Routing protocol attributes
CREATE TABLE rproto_attr (
  id SERIAL NOT NULL,
  interfaceid INT4 NOT NULL,
  protoname VARCHAR NOT NULL, -- bgp/ospf/isis
  metric INT4,

  CONSTRAINT rproto_attr_pkey
             PRIMARY KEY (id),
  CONSTRAINT rproto_attr_interfaceid_fkey
             FOREIGN KEY (interfaceid)
             REFERENCES interface (interfaceid)
             ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  vlanid INT4 NOT NULL REFERENCES vlan ON UPDATE CASCADE ON DELETE CASCADE,
  direction CHAR(1) NOT NULL DEFAULT 'x', -- u=up, n=down, x=undefined?
  UNIQUE (interfaceid, vlanid)
);

CREATE TABLE swportallowedvlan (
  interfaceid INT4 NOT NULL PRIMARY KEY REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring VARCHAR
);


CREATE TABLE swportblocked (
  swportblockedid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,

  CONSTRAINT swportblocked_uniq UNIQUE (interfaceid, vlan)
);

-- View to mimic old swport table
CREATE VIEW swport AS (
  SELECT
    interfaceid AS swportid,
    moduleid,
    ifindex,
    baseport AS port,
    ifdescr AS interface,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link,
    speed,
    duplex,
    media,
    vlan,
    trunk,
    ifalias AS portname,
    to_netboxid,
    to_interfaceid AS to_swportid
  FROM interface
  WHERE interfaceid NOT IN (SELECT interfaceid FROM gwportprefix)
);

-- View to mimic old gwport table
CREATE VIEW gwport AS (
  SELECT
    i.interfaceid AS gwportid,
    moduleid,
    ifindex,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link,
    NULL::INT4 AS masterindex,
    ifdescr AS interface,
    speed,
    metric,
    ifalias AS portname,
    to_netboxid,
    to_interfaceid AS to_swportid
  FROM interface i
  JOIN gwportprefix gwpfx ON (i.interfaceid=gwpfx.interfaceid)
  LEFT JOIN rproto_attr ra ON (i.interfaceid=ra.interfaceid AND ra.protoname='ospf')
);

-- View to see only switch ports
CREATE VIEW interface_swport AS (
  SELECT
    interface.*,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link
  FROM
    interface
  WHERE
    baseport IS NOT NULL
);

-- View to see only router ports
CREATE VIEW interface_gwport AS (
  SELECT
    interface.*,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link
  FROM
    interface
  JOIN
    (SELECT interfaceid FROM gwportprefix GROUP BY interfaceid) routerports USING (interfaceid)
);

CREATE TABLE cabling (
  cablingid SERIAL PRIMARY KEY,
  roomid VARCHAR(30) NOT NULL REFERENCES room ON UPDATE CASCADE ON DELETE CASCADE,
  jack VARCHAR NOT NULL,
  building VARCHAR NOT NULL,
  targetroom VARCHAR NOT NULL,
  descr VARCHAR,
  category VARCHAR NOT NULL,
UNIQUE(roomid,jack));

CREATE TABLE patch (
  patchid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  cablingid INT4 NOT NULL REFERENCES cabling ON UPDATE CASCADE ON DELETE CASCADE,
  split VARCHAR NOT NULL DEFAULT 'no',
UNIQUE(interfaceid,cablingid));

-- Remove floating devices.
-- Devices that don't have a serial and no connected modules or netboxes.
-- Triggers on delete on module and netbox.
CREATE OR REPLACE FUNCTION remove_floating_devices() RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM device WHERE
            deviceid NOT IN (SELECT deviceid FROM netbox) AND
            deviceid NOT IN (SELECT deviceid FROM module) AND
            serial IS NULL;
        RETURN NULL;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_module_delete_prune_devices
    AFTER DELETE ON module
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();

CREATE TRIGGER trig_netbox_delete_prune_devices
    AFTER DELETE ON netbox
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();


------------------------------------------------------------------
------------------------------------------------------------------


CREATE TABLE arp (
  arpid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ip INET NOT NULL,
  mac MACADDR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity'
);

-- Rule to automatically close open arp entries related to a given prefix
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL
     WHERE prefixid=OLD.prefixid AND end_time='infinity';

-- View for listing all IP addresses that appear to be alive at the moment.
CREATE OR REPLACE VIEW manage.live_clients AS
  SELECT arp.ip, arp.mac
    FROM arp
   WHERE arp.end_time = 'infinity';

CREATE TABLE cam (
  camid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ifindex INT4 NOT NULL,
  module VARCHAR(4),
  port VARCHAR,
  mac MACADDR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity',
  misscnt INT4 DEFAULT '0'
);


-- Rules to automatically close open cam and arp entries related to a given netbox
CREATE OR REPLACE RULE netbox_close_arp AS ON DELETE TO netbox
  DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

CREATE OR REPLACE RULE netbox_close_cam AS ON DELETE TO netbox
  DO UPDATE cam SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';


-- VIEWs -----------------------

CREATE VIEW prefix_active_ip_cnt AS
(SELECT prefix.prefixid, COUNT(arp.ip) AS active_ip_cnt
 FROM prefix
 LEFT JOIN arp ON arp.ip << prefix.netaddr
 WHERE arp.end_time = 'infinity'
 GROUP BY prefix.prefixid);

CREATE VIEW prefix_max_ip_cnt AS
(SELECT prefixid,
  CASE POW(2,32-MASKLEN(netaddr))-2 WHEN -1 THEN 0
   ELSE
  POW(2,32-MASKLEN(netaddr))-2 END AS max_ip_cnt
 FROM prefix);

-- This view gives the allowed vlan for a given hexstring i swportallowedvlan
CREATE VIEW allowedvlan AS (
  SELECT
    interfaceid, vlan AS allowedvlan
  FROM
    (SELECT interfaceid, decode(hexstring, 'hex') AS octetstring
     FROM swportallowedvlan) AS allowed_octets
  CROSS JOIN
    generate_series(0, 4095) AS vlan
  WHERE
    vlan < length(octetstring)*8 AND
    (CASE
       WHEN length(octetstring)>=128
         THEN get_bit(octetstring, (vlan/8)*8+7-(vlan%8))
       ELSE get_bit(octetstring,(length(octetstring)*8-vlan+7>>3<<3)-8+(vlan%8))
     END) = 1
);

CREATE VIEW allowedvlan_both AS
  (select interfaceid,interfaceid as interfaceid2,allowedvlan from allowedvlan ORDER BY allowedvlan) union
  (select  interface.interfaceid,to_interfaceid as interfaceid2,allowedvlan from interface join allowedvlan
    on (interface.to_interfaceid=allowedvlan.interfaceid) ORDER BY allowedvlan);

------------------------------------------------------------------------------
-- rrd metadb tables
------------------------------------------------------------------------------

-- This table contains the different systems that has rrd-data.
-- Replaces table eventprocess
CREATE TABLE subsystem (
  name      VARCHAR PRIMARY KEY, -- name of the system, e.g. Cricket
  descr     VARCHAR  -- description of the system
);

INSERT INTO subsystem (name) VALUES ('eventEngine');
INSERT INTO subsystem (name) VALUES ('pping');
INSERT INTO subsystem (name) VALUES ('serviceping');
INSERT INTO subsystem (name) VALUES ('moduleMon');
INSERT INTO subsystem (name) VALUES ('thresholdMon');
INSERT INTO subsystem (name) VALUES ('trapParser');
INSERT INTO subsystem (name) VALUES ('cricket');
INSERT INTO subsystem (name) VALUES ('deviceManagement');
INSERT INTO subsystem (name) VALUES ('getDeviceData');
INSERT INTO subsystem (name) VALUES ('devBrowse');
INSERT INTO subsystem (name) VALUES ('maintenance');
INSERT INTO subsystem (name) VALUES ('snmptrapd');
INSERT INTO subsystem (name) VALUES ('powersupplywatch');
INSERT INTO subsystem (name) VALUES ('ipdevpoll');
INSERT INTO subsystem (name) VALUES ('macwatch');



------------------------------------------------------------------------------------------
-- event system tables
------------------------------------------------------------------------------------------

-- event tables
CREATE TABLE eventtype (
  eventtypeid VARCHAR(32) PRIMARY KEY,
  eventtypedesc VARCHAR,
  stateful CHAR(1) NOT NULL CHECK (stateful='y' OR stateful='n')
);
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('boxState','Tells us whether a network-unit is down or up.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('serviceState','Tells us whether a service on a server is up or down.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('moduleState','Tells us whether a module in a device is working or not.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('thresholdState','Tells us whether the load has passed a certain threshold.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('linkState','Tells us whether a link is up or down.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('boxRestart','Tells us that a network-unit has done a restart','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('info','Basic information','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('notification','Notification event, typically between NAV systems','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceActive','Lifetime event for a device','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceState','Registers the state of a device','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceNotice','Registers a notice on a device','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('maintenanceState','Tells us if something is set on maintenance','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('apState','Tells us whether an access point has disassociated or associated from the controller','y');
INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('snmpAgentState', 'Tells us whether the SNMP agent on a device is down or up.', 'y');
INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('chassisState', 'The state of this chassis has changed', 'y');
INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('aggregateLinkState', 'The state of this aggregated link changed', 'y');
INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('psuState', 'Reports state changes in power supply units', 'y');
INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('fanState', 'Reports state changes in fan units', 'y');



CREATE TABLE eventq (
  eventqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  target VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid VARCHAR NOT NULL DEFAULT '',
  time TIMESTAMP NOT NULL DEFAULT NOW (),
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL DEFAULT 'x' CHECK (state='x' OR state='s' OR state='e'), -- x = stateless, s = start, e = end
  value INT4 NOT NULL DEFAULT '100',
  severity INT4 NOT NULL DEFAULT '50'
);

CREATE SEQUENCE eventqvar_id_seq;
CREATE TABLE eventqvar (
  id integer NOT NULL DEFAULT nextval('eventqvar_id_seq'),
  eventqid INT4 REFERENCES eventq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,

  CONSTRAINT eventqvar_pkey PRIMARY KEY(id),
  CONSTRAINT eventqvar_eventqid_key UNIQUE(eventqid, var) -- only one val per var per event
);
ALTER SEQUENCE eventqvar_id_seq OWNED BY eventqvar.id;



-- alert tables

CREATE TABLE alerttype (
  alerttypeid SERIAL PRIMARY KEY,
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttype VARCHAR,
  alerttypedesc VARCHAR,
  CONSTRAINT alerttype_eventalert_unique UNIQUE (eventtypeid, alerttype)
);
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxDownWarning','Warning sent before declaring the box down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxShadowWarning','Warning sent before declaring the box in shadow.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxDown','Box declared down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxUp','Box declared up.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxShadow','Box declared down, but is in shadow.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxSunny','Box declared up from a previous shadow state.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleDownWarning','Warning sent before declaring the module down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleDown','Module declared down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleUp','Module declared up.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('serviceState','httpDown','http service not responding.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('serviceState','httpUp','http service responding.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('maintenanceState','onMaintenance','Box put on maintenance.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('maintenanceState','offMaintenance','Box taken off maintenance.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('thresholdState','exceededThreshold','Threshold exceeded.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('thresholdState','belowThreshold','Value below threshold.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('info','dnsMismatch','Mismatch between sysname and dnsname.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('info','serialChanged','Serial number for the device has changed.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxRestart','coldStart','The IP device has coldstarted');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxRestart','warmStart','The IP device has warmstarted');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceInIPOperation','The device is now in operation with an active IP address');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceInStack','The device is now in operation as a chassis module');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceRMA','RMA event for device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceError','Error situation on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceSwUpgrade','Software upgrade on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceHwUpgrade','Hardware upgrade on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('apState','apUp','AP associated with controller');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('apState','apDown','AP disassociated from controller');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentDown', 'SNMP agent is down or unreachable due to misconfiguration.');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentUp', 'SNMP agent is up.');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('chassisState', 'chassisDown', 'This chassis is no longer visible in the stack');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('chassisState', 'chassisUp', 'This chassis is visible in the stack again');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('aggregateLinkState', 'linkDegraded', 'This aggregate link has been degraded');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('aggregateLinkState', 'linkRestored', 'This aggregate link has been restored');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('info','macWarning','Mac appeared on port');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuNotOK', 'A PSU has entered a non-OK state');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuOK', 'A PSU has returned to an OK state');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanNotOK', 'A fan unit has entered a non-OK state');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanOK', 'A fan unit has returned to an OK state');



CREATE TABLE alerthist (
  alerthistid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  subid VARCHAR NOT NULL DEFAULT '',
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP DEFAULT 'infinity',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttypeid INT4 REFERENCES alerttype ON UPDATE CASCADE ON DELETE CASCADE,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);

-- Rule to automatically close module related alert states when modules are
-- deleted.
CREATE OR REPLACE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW()
     WHERE eventtypeid IN ('moduleState', 'linkState')
       AND end_time='infinity'
       AND deviceid=OLD.deviceid;

CREATE TABLE alerthistmsg (
  id SERIAL,
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alerthistid, state, msgtype, language)
);

CREATE TABLE alerthistvar (
  id SERIAL,
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alerthistid, state, var) -- only one val per var per state per alert
);


CREATE TABLE alertq (
  alertqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid VARCHAR NOT NULL DEFAULT '',
  time TIMESTAMP NOT NULL,
  eventtypeid VARCHAR(32) REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttypeid INT4 REFERENCES alerttype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  value INT4 NOT NULL,
  severity INT4 NOT NULL,
  alerthistid INTEGER NULL,
  CONSTRAINT alertq_alerthistid_fkey FOREIGN KEY (alerthistid) REFERENCES alerthist (alerthistid)
             ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE alertqmsg (
  id SERIAL,
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alertqid, msgtype, language)
);

CREATE TABLE alertqvar (
  id SERIAL,
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alertqid, var) -- only one val per var per event
);


------------------------------------------------------------------------------
-- servicemon tables
------------------------------------------------------------------------------

CREATE TABLE service (
  serviceid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  active BOOL DEFAULT true,
  handler VARCHAR,
  version VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s') -- y=up, n=down, s=shadow
);

CREATE TABLE serviceproperty (
  id SERIAL,
  serviceid INT4 NOT NULL REFERENCES service ON UPDATE CASCADE ON DELETE CASCADE,
  property VARCHAR(64) NOT NULL,
  value VARCHAR,
  PRIMARY KEY(serviceid, property)
);

------------------------------------------------------------------------------
-- messages/maintenance v2 tables
------------------------------------------------------------------------------

CREATE TABLE message (
    messageid SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    tech_description TEXT,
    publish_start TIMESTAMP,
    publish_end TIMESTAMP,
    author VARCHAR NOT NULL,
    last_changed TIMESTAMP,
    replaces_message INT REFERENCES message,
    replaced_by INT REFERENCES message
);

CREATE OR REPLACE FUNCTION message_replace() RETURNS TRIGGER AS '
    DECLARE
        -- Old replaced_by value of the message beeing replaced
        old_replaced_by INTEGER;
    BEGIN
        -- Remove references that are no longer correct
        IF TG_OP = ''UPDATE'' THEN
            IF OLD.replaces_message <> NEW.replaces_message OR
                (OLD.replaces_message IS NOT NULL AND NEW.replaces_message IS NULL) THEN
                EXECUTE ''UPDATE message SET replaced_by = NULL WHERE messageid = ''
                || quote_literal(OLD.replaces_message);
            END IF;
        END IF;

        -- It does not replace any message, exit
        IF NEW.replaces_message IS NULL THEN
            RETURN NEW;
        END IF;

        -- Update the replaced_by field of the replaced message with a
        -- reference to the replacer
        SELECT INTO old_replaced_by replaced_by FROM message
            WHERE messageid = NEW.replaces_message;
        IF old_replaced_by <> NEW.messageid OR old_replaced_by IS NULL THEN
            EXECUTE ''UPDATE message SET replaced_by = ''
            || quote_literal(NEW.messageid)
            || '' WHERE messageid = ''
            || quote_literal(NEW.replaces_message);
        END IF;

        RETURN NEW;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_message_replace
	AFTER INSERT OR UPDATE ON message
	FOR EACH ROW
	EXECUTE PROCEDURE message_replace();

CREATE OR REPLACE VIEW message_with_replaced AS
    SELECT
        m.messageid, m.title,
	m.description, m.tech_description,
        m.publish_start, m.publish_end, m.author, m.last_changed,
        m.replaces_message, m.replaced_by,
        rm.title AS replaces_message_title,
        rm.description AS replaces_message_description,
        rm.tech_description AS replaces_message_tech_description,
        rm.publish_start AS replaces_message_publish_start,
        rm.publish_end AS replaces_message_publish_end,
        rm.author AS replaces_message_author,
        rm.last_changed AS replaces_message_last_changed,
        rb.title AS replaced_by_title,
        rb.description AS replaced_by_description,
        rb.tech_description AS replaced_by_tech_description,
        rb.publish_start AS replaced_by_publish_start,
        rb.publish_end AS replaced_by_publish_end,
        rb.author AS replaced_by_author,
        rb.last_changed AS replaced_by_last_changed
    FROM
    	message m LEFT JOIN message rm ON (m.replaces_message = rm.messageid)
    	LEFT JOIN message rb ON (m.replaced_by = rb.messageid);

CREATE TABLE maint_task (
    maint_taskid SERIAL PRIMARY KEY,
    maint_start TIMESTAMP NOT NULL,
    maint_end TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    author VARCHAR NOT NULL,
    state VARCHAR NOT NULL
);

CREATE TABLE maint_component (
    id SERIAL,
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    PRIMARY KEY (maint_taskid, key, value)
);

CREATE TABLE message_to_maint_task (
    id SERIAL,
    messageid INT NOT NULL REFERENCES message ON UPDATE CASCADE ON DELETE CASCADE,
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (messageid, maint_taskid)
);

CREATE OR REPLACE VIEW maint AS
    SELECT * FROM maint_task NATURAL JOIN maint_component;

------------------------------------------------------------------------------
-- log of schema changes
------------------------------------------------------------------------------
CREATE TABLE schema_change_log (
    id SERIAL PRIMARY KEY,
    major INTEGER NOT NULL,
    minor INTEGER NOT NULL,
    point INTEGER NOT NULL,
    script_name VARCHAR NOT NULL,
    date_applied TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE OR REPLACE RULE netbox_status_close_arp AS ON UPDATE TO netbox
   WHERE NEW.up='n'
   DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';


CREATE TABLE manage.sensor (
  sensorid SERIAL PRIMARY KEY,
  netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
  oid VARCHAR,
  unit_of_measurement VARCHAR,
  precision integer default 0,
  data_scale VARCHAR,
  human_readable VARCHAR,
  name VARCHAR,
  internal_name VARCHAR,
  mib VARCHAR
);

CREATE TABLE manage.powersupply_or_fan (
    powersupplyid SERIAL PRIMARY KEY,
    netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
    deviceid INT REFERENCES device(deviceid) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR NOT NULL,
    model VARCHAR,
    descr VARCHAR,
    physical_class VARCHAR not null,
    downsince TIMESTAMP default null,
    sensor_oid VARCHAR,
    up CHAR(1) NOT NULL DEFAULT 'u' CHECK (up='y' OR up='n' or up='u' or up='w')
);


-- Ensure any associated service alerts are closed when a service is deleted
CREATE RULE close_alerthist_services
  AS ON DELETE TO service DO
  UPDATE alerthist SET end_time=NOW()
  WHERE
    eventtypeid='serviceState'
    AND end_time='infinity'
    AND subid = old.serviceid::text;

-- Rule to automatically resolve netbox related alert states when netboxes are
-- deleted.
CREATE OR REPLACE RULE close_alerthist_netboxes AS ON DELETE TO netbox
  DO UPDATE alerthist SET end_time=NOW()
     WHERE netboxid=OLD.netboxid
       AND end_time='infinity';

-- swp_netbox replacement table
CREATE TABLE manage.adjacency_candidate (
  adjacency_candidateid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_interfaceid INT4 REFERENCES interface ON UPDATE CASCADE ON DELETE SET NULL,
  source VARCHAR NOT NULL,
  misscnt INT4 NOT NULL DEFAULT 0,
  CONSTRAINT adjacency_candidate_uniq UNIQUE(netboxid, interfaceid, to_netboxid, source)
);

DELETE FROM netboxinfo WHERE key='unrecognizedCDP';

-- new unrecognized neighbors table
CREATE TABLE manage.unrecognized_neighbor (
  id SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  remote_id VARCHAR NOT NULL,
  remote_name VARCHAR NOT NULL,
  source VARCHAR NOT NULL,
  since TIMESTAMP NOT NULL DEFAULT NOW(),
  ignored_since TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE unrecognized_neighbor IS 'Unrecognized neighboring devices reported by support discovery protocols';




-- Create a log table for ipdevpoll job runs
CREATE TABLE manage.ipdevpoll_job_log (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  netboxid INTEGER NOT NULL,
  job_name VARCHAR NOT NULL,
  end_time TIMESTAMP NOT NULL,
  duration DOUBLE PRECISION,
  success BOOLEAN,
  "interval" INTEGER,

  CONSTRAINT ipdevpoll_job_log_netbox_fkey FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE
);


-- automatically close snmpAgentStates when community is removed.

CREATE OR REPLACE FUNCTION close_snmpagentstates_on_community_clear()
RETURNS TRIGGER AS E'
    BEGIN
        IF COALESCE(OLD.ro, \'\') IS DISTINCT FROM COALESCE(NEW.ro, \'\')
           AND COALESCE(NEW.ro, \'\') = \'\' THEN
            UPDATE alerthist
            SET end_time=NOW()
            WHERE netboxid=NEW.netboxid
              AND eventtypeid=\'snmpAgentState\'
              AND end_time >= \'infinity\';
        END IF;
        RETURN NULL;
    END;
    ' language 'plpgsql';

CREATE TRIGGER trig_close_snmpagentstates_on_community_clear
    AFTER UPDATE ON netbox
    FOR EACH ROW
    EXECUTE PROCEDURE close_snmpagentstates_on_community_clear();


-- Notify the eventEngine immediately as new events are inserted in the queue
CREATE OR REPLACE RULE eventq_notify AS ON INSERT TO eventq DO ALSO NOTIFY new_event;


-- Create table for netbios names

CREATE TABLE netbios (
  netbiosid SERIAL PRIMARY KEY,
  ip INET NOT NULL,
  mac MACADDR,
  name VARCHAR NOT NULL,
  server VARCHAR NOT NULL,
  username VARCHAR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity'
);

-- fix view that gives wrong ip count in VRRP/HSRP environments
CREATE OR REPLACE VIEW manage.prefix_active_ip_cnt AS
(SELECT prefix.prefixid, COUNT(DISTINCT arp.ip) AS active_ip_cnt
 FROM prefix
 LEFT JOIN arp ON arp.ip << prefix.netaddr
 WHERE arp.end_time = 'infinity'
 GROUP BY prefix.prefixid);

-- Create a table for interface stacking information
CREATE TABLE manage.interface_stack (
  id SERIAL PRIMARY KEY, -- dummy primary key for Django
  higher INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  lower INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE (higher, lower)
);


CREATE OR REPLACE VIEW manage.netboxmac AS

SELECT DISTINCT ON (mac) netboxid, mac FROM (
(

 -- Attempt to get MAC for netbox' monitored IP
 SELECT DISTINCT netbox.netboxid, arp.mac
 FROM netbox
 JOIN arp ON (arp.ip = netbox.ip AND arp.end_time = 'infinity')

) UNION (

 -- Attempt to get MAC for router's interface addresses and virtual addresses
 SELECT interface.netboxid, arp.mac
 FROM arp
 JOIN gwportprefix gwp ON arp.ip = gwp.gwip
 LEFT JOIN (SELECT prefixid, COUNT(*) > 0 AS has_virtual
            FROM gwportprefix
            WHERE virtual=true
            GROUP BY prefixid) AS prefix_virtual_ports ON (gwp.prefixid = prefix_virtual_ports.prefixid)
 JOIN interface USING (interfaceid)
 WHERE arp.end_time = 'infinity'
   AND (gwp.virtual = true OR has_virtual IS NULL)

) UNION (

 -- Get MAC directly from interface physical addresses
 SELECT DISTINCT ON (interface.ifphysaddress) interface.netboxid, interface.ifphysaddress AS mac
   FROM interface
   -- physical ethernet interfaces are assumed to be iftype=6
  WHERE interface.iftype = 6 AND interface.ifphysaddress IS NOT NULL

)

) AS foo
WHERE mac <> '00:00:00:00:00:00' -- exclude invalid MACs
ORDER BY mac, netboxid;

CREATE OR REPLACE FUNCTION never_use_null_subid()
RETURNS trigger AS $$
  BEGIN
    NEW.subid = COALESCE(NEW.subid, '');
    RETURN NEW;
  END;
$$ language plpgsql;

CREATE TRIGGER eventq_subid_fix BEFORE INSERT OR UPDATE ON eventq
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();

CREATE TRIGGER alertq_subid_fix BEFORE INSERT OR UPDATE ON alertq
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();

CREATE TRIGGER alerthist_subid_fix BEFORE INSERT OR UPDATE ON alerthist
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();

CREATE TABLE netboxentity (
  netboxentityid SERIAL NOT NULL,
  netboxid INTEGER NOT NULL,

  index INTEGER NOT NULL,
  source VARCHAR NOT NULL,
  descr VARCHAR,
  vendor_type VARCHAR,
  contained_in_id INTEGER,
  physical_class INTEGER,
  parent_relpos INTEGER,
  name VARCHAR,
  hardware_revision VARCHAR,
  firmware_revision VARCHAR,
  software_revision VARCHAR,
  deviceid INTEGER,
  mfg_name VARCHAR,
  model_name VARCHAR,
  alias VARCHAR,
  asset_id VARCHAR,
  fru BOOLEAN,
  mfg_date TIMESTAMP WITH TIME ZONE,
  uris VARCHAR,
  data hstore NOT NULL DEFAULT hstore(''),
  gone_since TIMESTAMP,

  CONSTRAINT netboxentity_pkey PRIMARY KEY (netboxentityid),
  CONSTRAINT netboxentity_netboxid_fkey
             FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_contained_in_id_fkey
             FOREIGN KEY (contained_in_id)
             REFERENCES netboxentity (netboxentityid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_deviceid_fkey
             FOREIGN KEY (deviceid)
             REFERENCES device (deviceid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_netboxid_source_index_unique
             UNIQUE (netboxid, source, index) INITIALLY DEFERRED

);

-- Modernize existing close_alerthist_modules rule

CREATE OR REPLACE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW()
     WHERE eventtypeid = 'moduleState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.moduleid::text;

-- Make similar rule for chassis devices

CREATE OR REPLACE RULE close_alerthist_chassis AS ON DELETE TO netboxentity
  WHERE OLD.physical_class = 3  -- chassis class magic number
  DO UPDATE alerthist SET end_time=NOW()
     WHERE eventtypeid = 'chassisState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.netboxentityid::text;

-- Make similar rule for interface devices

CREATE OR REPLACE RULE close_alerthist_interface AS ON DELETE TO interface
  DO UPDATE alerthist SET end_time=NOW()
     WHERE eventtypeid = 'linkState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.interfaceid::text;

CREATE VIEW enterprise_number AS

WITH enterprise AS (
  SELECT vendorid,
         (string_to_array(sysobjectid, '.'))[7]::INTEGER AS enterprise
  FROM manage.type)
SELECT vendorid, enterprise, count(*)
FROM enterprise
GROUP BY vendorid, enterprise
ORDER BY enterprise, count DESC, vendorid;

COMMENT ON VIEW enterprise_number IS
'Shows the most common enterprise numbers associated with each vendorid, based on the type table';

-- Create a table for interface aggregation information
CREATE TABLE manage.interface_aggregate (
  id SERIAL PRIMARY KEY, -- dummy primary key for Django
  aggregator INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  interface INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE (aggregator, interface)
);


-- Create table for storing prefix tags
CREATE TABLE prefix_usage (
    prefix_usage_id SERIAL PRIMARY KEY,
    prefixid        INTEGER REFERENCES prefix (prefixid)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    usageid         VARCHAR REFERENCES usage (usageid)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE (prefixid, usageid)
);

INSERT INTO schema_change_log (major, minor, point, script_name)
    VALUES (4, 6, 56, 'initial install');
