-- linkcheck job was renamed to statuscheck - update existing log entries.
UPDATE ipdevpoll_job_log SET job_name = 'statuscheck' WHERE job_name = 'linkcheck';
