-- the snmpcheck plugin no longer keeps internal state here
DELETE FROM netboxinfo WHERE key='status' AND var='snmpstate';
