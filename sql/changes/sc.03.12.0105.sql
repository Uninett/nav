-- rename logging jobs to ip2mac in ipdevpoll job log table
UPDATE ipdevpoll_job_log SET job_name = 'ip2mac' WHERE job_name = 'logging';
