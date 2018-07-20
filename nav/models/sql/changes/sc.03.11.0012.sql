-- force re-collection of module/serial number data to fix data mangled by LP#1034864
DELETE FROM netboxinfo WHERE key='poll_times' AND var='modules';
