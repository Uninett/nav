-- Force re-collection of various data where collection code may have changed in 4.3.
DELETE FROM netboxinfo WHERE key='poll_times';
