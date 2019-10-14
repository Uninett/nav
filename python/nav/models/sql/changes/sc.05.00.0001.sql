-- Remove obsolete and non-functioning trigger
DROP TRIGGER IF EXISTS
   trig_module_delete_prune_devices
   ON module;

DROP TRIGGER IF EXISTS
   trig_netbox_delete_prune_devices
   ON netbox;

DROP FUNCTION IF EXISTS remove_floating_devices();
