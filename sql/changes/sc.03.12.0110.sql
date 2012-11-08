-- ensure CDP records are collected freshly after upgrade,
-- to quickly facilitate the fix for LP#1068097
DELETE FROM netboxinfo WHERE key='poll_times' AND var='cdp';
