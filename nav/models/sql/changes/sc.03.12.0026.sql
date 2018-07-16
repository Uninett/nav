-- Create a log table for ipdevpoll job runs

CREATE TABLE manage.ipdevpoll_job_log (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  netboxid INTEGER NOT NULL,
  job_name VARCHAR NOT NULL,
  end_time TIMESTAMP NOT NULL,
  duration DOUBLE PRECISION,
  success BOOLEAN NOT NULL,
  "interval" INTEGER,

  CONSTRAINT ipdevpoll_job_log_netbox_fkey FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX ipdevpoll_job_log_netboxjob_btree
  ON ipdevpoll_job_log (netboxid, job_name);
