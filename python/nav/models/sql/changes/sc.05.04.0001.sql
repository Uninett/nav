-- force re-collection of module data to not classify transceivers as modules anymore
DELETE FROM netboxinfo WHERE key='poll_times' AND var='modules';
