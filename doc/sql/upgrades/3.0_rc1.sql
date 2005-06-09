/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.0_beta9 to 3.0_beta10.
 *
 * The collection of memory information from devices has remained
 * unimplemented in NAV 3 until now, which prompted the addition of a
 * UNIQUE contraint to the mem table
 *
 * Connect to PostgreSQL as the postgres superuser and run this script
 * like this:
 *
 * psql -f 3.0_beta8.sql manage postgres
 *
 * Please, also run the updated snmpoid.sql script over again, like
 * this:
 *
 * psql -f snmpoid.sql manage postgres
 *
 * We also recommend to let Postgre clean and optimize the database
 *
 * vacuumdb --analyze --full -a
 *
*/

BEGIN;

CREATE INDEX vlan_vlan_btree ON vlan USING btree (vlan);
CREATE INDEX prefix_vlanid_btree ON prefix USING btree (vlanid);
CREATE INDEX netbox_prefixid_btree ON netbox USING btree (prefixid);
CREATE INDEX netboxsnmpoid_snmpoidid_btree ON netboxsnmpoid USING btree (snmpoidid);
CREATE INDEX gwportprefix_gwportid_btree ON gwportprefix USING btree (gwportid);
CREATE INDEX gwportprefix_prefixid_btree ON gwportprefix USING btree (prefixid);
CREATE INDEX swportvlan_swportid_btree ON swportvlan USING btree (swportid);
CREATE INDEX swportvlan_vlanid_btree ON swportvlan USING btree (vlanid);
CREATE INDEX arp_prefixid_btree ON arp USING btree (prefixid);

DROP VIEW netboxmac;
CREATE VIEW netboxmac AS
(SELECT DISTINCT ON (mac) netbox.netboxid, arp.mac
 FROM netbox
 JOIN arp ON (arp.arpid = (SELECT arp.arpid FROM arp WHERE arp.ip=netbox.ip AND end_time='infinity' LIMIT 1)))
UNION DISTINCT
(SELECT DISTINCT ON (mac) module.netboxid,mac
 FROM arp
 JOIN gwportprefix gwp ON
  (arp.ip=gwp.gwip AND (hsrp=true OR (SELECT COUNT(*) FROM gwportprefix WHERE gwp.prefixid=gwportprefix.prefixid AND hsrp=true) = 0))
 JOIN gwport USING(gwportid)
 JOIN module USING (moduleid)
 WHERE arp.end_time='infinity');

CREATE VIEW prefixreport AS (
SELECT host(netaddr),masklen(netaddr) as m,
   vlan,count(gwip) as antgw,nettype,netaddr,netident,orgid,usageid,description,
   (select active_ip_cnt from prefix_active_ip_cnt where prefix_active_ip_cnt .prefixid=prefix.prefixid) AS act,
   prefix.prefixid,vlan.vlanid
    FROM prefix
    JOIN vlan USING(vlanid)
    JOIN gwportprefix USING (prefixid)
    JOIN gwport USING (gwportid)
    GROUP BY netaddr,vlan,nettype,netident,vlan.orgid,usageid,description,act,prefix.prefixid,vlan.vlanid
);

CREATE VIEW netboxreport AS (
SELECT roomid,sysname,ip,catid,
  (select count(*) from netboxcategory where netboxcategory.netboxid=netbox.netboxid) AS sub,typename,orgid,up,
  (select count(*) from module where module.netboxid=netbox.netboxid) AS modules,
  (select count(*) from swport join module using(moduleid) where module.netboxid=netbox.netboxid) AS swport,
  (select count(*) from gwport join module using(moduleid) where module.netboxid=netbox.netboxid) AS gwport,
  'Mem'::varchar AS Mem,
  (select count(*) from netboxsnmpoid where netboxsnmpoid.netboxid=netbox.netboxid) AS snmp,
  val AS Function,netbox.netboxid,prefixid,typeid
  FROM netbox join type using(typeid)
  LEFT JOIN netboxinfo ON (netbox.netboxid=netboxinfo.netboxid AND var='function')
);

COMMIT;
