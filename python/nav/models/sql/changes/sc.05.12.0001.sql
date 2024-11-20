-- Add column to maint_component table to keep descriptions of components that can no longer referenced
ALTER TABLE maint_component ADD COLUMN description VARCHAR;

UPDATE maint_component c
SET description = n.sysname
FROM netbox n
WHERE c.key = 'netbox' AND c.value = n.netboxid::text;
