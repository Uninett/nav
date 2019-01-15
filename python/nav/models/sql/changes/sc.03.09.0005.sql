-- Force re-profiling of all devices AGAIN, using the fixed AGAIN code for issue LP#862208
UPDATE snmpoid SET uptodate=FALSE WHERE oidsource ILIKE 'cricket';
