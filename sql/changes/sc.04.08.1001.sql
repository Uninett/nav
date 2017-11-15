-- remove obsolete things that seem to hang around on some, but not all,
-- upgraded installations (i.e. these things are just fine in the baseline,
-- but may have become issues for those who have been upgrading NAV versions
-- repeatedly for a long time).

DROP FUNCTION IF EXISTS drop_constraint();

ALTER TABLE cam
  DROP CONSTRAINT IF EXISTS cam_netboxid_sysname_module_port_mac_start_time_key,
  DROP CONSTRAINT IF EXISTS cam_netboxid_key;

ALTER INDEX IF EXISTS subcat_pkey RENAME TO netboxgroup_pkey;
