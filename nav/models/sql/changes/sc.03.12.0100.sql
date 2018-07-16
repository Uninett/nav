-- Fix broken log-trimming trigger (LP#1053866)
CREATE OR REPLACE FUNCTION trim_old_ipdevpoll_job_log_entries()
RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM ipdevpoll_job_log
        WHERE id IN (SELECT id FROM ipdevpoll_job_log
                     WHERE job_name=NEW.job_name AND netboxid=NEW.netboxid
                     ORDER BY end_time DESC
                     OFFSET 100);
        RETURN NULL;
    END;
    ' language 'plpgsql';
