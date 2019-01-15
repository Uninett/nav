-- allow jobs to be logged with no success indicator, i.e. the job was
-- checked but nothing ran.
ALTER TABLE ipdevpoll_job_log ALTER COLUMN success DROP NOT NULL;
