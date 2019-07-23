-- These unique constraints never had explicit names in the NAV schema, causing
-- their names to become inconsistent between PostgreSQL versions.  This
-- explicitly renames those constraints that still have the implicit names given
-- by old PostgreSQL versions, to match those implicit names given by newer
-- versions:

ALTER INDEX IF EXISTS alerthistmsg_alerthistid_key RENAME TO alerthistmsg_alerthistid_state_msgtype_language_key;
ALTER INDEX IF EXISTS alerthistvar_alerthistid_key RENAME TO alerthistvar_alerthistid_state_var_key;
ALTER INDEX IF EXISTS alertqmsg_alertqid_key RENAME TO alertqmsg_alertqid_msgtype_language_key;
ALTER INDEX IF EXISTS alertqvar_alertqid_key RENAME TO alertqvar_alertqid_var_key;
ALTER INDEX IF EXISTS cabling_roomid_key RENAME TO cabling_roomid_jack_key;
ALTER INDEX IF EXISTS identity_mac_key RENAME TO identity_mac_swportid_key;
ALTER INDEX IF EXISTS log_message_type_priority_key RENAME TO log_message_type_priority_facility_mnemonic_key;
ALTER INDEX IF EXISTS mem_netboxid_key RENAME TO mem_netboxid_memtype_device_key;
ALTER INDEX IF EXISTS netboxinfo_netboxid_key RENAME TO netboxinfo_netboxid_key_var_val_key;
ALTER INDEX IF EXISTS netbox_vtpvlan_netboxid_key RENAME TO netbox_vtpvlan_netboxid_vtpvlan_key;
ALTER INDEX IF EXISTS patch_interfaceid_key RENAME TO patch_interfaceid_cablingid_key;
ALTER INDEX IF EXISTS swportvlan_interfaceid_key RENAME TO swportvlan_interfaceid_vlanid_key;
ALTER INDEX IF EXISTS type_vendorid_key RENAME TO type_vendorid_typename_key;
