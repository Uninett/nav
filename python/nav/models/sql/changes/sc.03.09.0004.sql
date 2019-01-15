-- Force re-profiling of all devices using the fixed code for issue LP#862208
UPDATE snmpoid SET uptodate=FALSE WHERE oidsource ILIKE 'cricket';
