---
-- Drop tables that have not been in use for many NAV versions
---
DROP VIEW rrddatasourcenetbox;
DROP RULE prefix_on_delete_do_clean_rrd_file ON prefix;
DROP RULE rrdfile_deleter ON service;
DROP TABLE rrd_datasource;
DROP TABLE rrd_file;
DROP TABLE netboxsnmpoid;
DROP TABLE snmpoid;
