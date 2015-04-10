-- Clean up only sometimes, not every time

DROP TRIGGER trig_trim_old_ipdevpoll_job_log_entries_on_insert ON ipdevpoll_job_log;

CREATE OR REPLACE FUNCTION trim_old_ipdevpoll_job_log_entries()
RETURNS TRIGGER AS $$
BEGIN
    -- We clean up only about 20% of the time
    IF RANDOM() >= 0.8 THEN
      WITH ranked AS (SELECT id, rank()
                      OVER (PARTITION BY netboxid, job_name ORDER BY end_time DESC)
                      FROM ipdevpoll_job_log)
      DELETE FROM ipdevpoll_job_log USING ranked
            WHERE ipdevpoll_job_log.id=ranked.id AND rank>100;
    END IF;
    RETURN NULL;
END;
$$ language plpgsql;

CREATE TRIGGER trig_trim_old_ipdevpoll_job_log_entries_on_insert
    AFTER INSERT ON ipdevpoll_job_log
    FOR EACH STATEMENT
    EXECUTE PROCEDURE trim_old_ipdevpoll_job_log_entries();
