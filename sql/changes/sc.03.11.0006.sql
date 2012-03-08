-- delete the now obsolete uncrecognizedCDP entries, since getBoksMacs is gone.
DELETE FROM netboxinfo WHERE key='unrecognizedCDP';
