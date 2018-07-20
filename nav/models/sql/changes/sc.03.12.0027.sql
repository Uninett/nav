-- Never keep more than 100 ipdevpoll_job_log entries per job per netbox
CREATE OR REPLACE FUNCTION trim_old_ipdevpoll_job_log_entries()
RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM ipdevpoll_job_log
        WHERE id IN (SELECT id FROM ipdevpoll_job_log
                     WHERE job_name=NEW.job_name AND netboxid=NEW.netboxid
                     ORDER BY end_time ASC
                     OFFSET 100);
        RETURN NULL;
    END;
    ' language 'plpgsql';

CREATE TRIGGER trig_trim_old_ipdevpoll_job_log_entries_on_insert
    AFTER INSERT ON ipdevpoll_job_log
    FOR EACH ROW
    EXECUTE PROCEDURE trim_old_ipdevpoll_job_log_entries();
