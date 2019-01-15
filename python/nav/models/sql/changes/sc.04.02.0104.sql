-- Fix LP#1437318. Prune old log entries outside the db
DROP TRIGGER IF EXISTS
   trig_trim_old_ipdevpoll_job_log_entries_on_insert
   ON ipdevpoll_job_log;

DROP FUNCTION IF EXISTS trim_old_ipdevpoll_job_log_entries();
