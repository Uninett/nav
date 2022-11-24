-- Delete crazy Juniper devices/modules that cause duplicates all over
DELETE FROM device WHERE serial = 'BUILTIN';

-- force re-collection of module data to ensure things come up-to-date after upgrade
DELETE FROM netboxinfo WHERE key='poll_times' AND var='modules';
