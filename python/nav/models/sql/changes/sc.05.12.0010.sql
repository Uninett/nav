-- Add column to maint_component table to keep descriptions of components that can no longer referenced
ALTER TABLE maint_component ADD COLUMN description VARCHAR;

UPDATE maint_component c
SET description = n.sysname
FROM netbox n
WHERE c.key = 'netbox' AND c.value = n.netboxid::text;

UPDATE maint_component c
SET description = s.handler || ' at ' || n.sysname
FROM service s
JOIN netbox n ON s.netboxid = n.netboxid
WHERE c.key = 'service' AND c.value = s.serviceid::text;
