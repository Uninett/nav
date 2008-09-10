CREATE SCHEMA vlanplot;
SET search_path = vlanplot;

-------- vlanPlot tables ------
CREATE TABLE vp_netbox_grp_info (
  vp_netbox_grp_infoid SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  hideicons BOOL NOT NULL DEFAULT false,
  iconname VARCHAR,
  x INT4 NOT NULL DEFAULT '0',
  y INT4 NOT NULL DEFAULT '0'
);
-- Default network
INSERT INTO vp_netbox_grp_info (vp_netbox_grp_infoid,name,hideicons) VALUES (0,'_Top',false);

CREATE TABLE vp_netbox_grp (
  vp_netbox_grp_infoid INT4 REFERENCES vp_netbox_grp_info ON UPDATE CASCADE ON DELETE CASCADE,
  pnetboxid INT4 NOT NULL,
  UNIQUE(vp_netbox_grp_infoid, pnetboxid)
);

CREATE TABLE vp_netbox_xy (
  vp_netbox_xyid SERIAL PRIMARY KEY, 
  pnetboxid INT4 NOT NULL,
  x INT4 NOT NULL,
  y INT4 NOT NULL,
  vp_netbox_grp_infoid INT4 NOT NULL REFERENCES vp_netbox_grp_info ON UPDATE CASCADE ON DELETE CASCADE,
  UNIQUE(pnetboxid, vp_netbox_grp_infoid)
);


-------- vlanPlot end ------

RESET search_path;
