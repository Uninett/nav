CREATE TABLE manage.alerthist_ack (
  alert_id INTEGER PRIMARY KEY NOT NULL,
  account_id INTEGER NOT NULL,
  comment VARCHAR DEFAULT NULL,
  date TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT alerthistory_ack_alert FOREIGN KEY (alert_id)
             REFERENCES manage.alerthist (alerthistid)
             ON UPDATE CASCADE ON DELETE CASCADE,

  CONSTRAINT alerthistory_ack_user FOREIGN KEY (account_id)
             REFERENCES profiles.account (id)
             ON UPDATE CASCADE ON DELETE CASCADE

);