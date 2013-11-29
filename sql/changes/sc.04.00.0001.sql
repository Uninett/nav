-- Remove profiling log entries, the job no longer exists
DELETE FROM ipdevpoll_job_log WHERE job_name='profiling';
