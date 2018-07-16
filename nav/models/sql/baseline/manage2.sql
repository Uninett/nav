/*

  manage2.sql

  This file is used for defining objects in the `manage` namespace that depend
  on objects in the `profiles` namespace. This is necessary because
  `manage.sql` is run before `profiles.sql`, and objects in `profiles.sql`
  depend on objects in `manage.sql`, and dependency cycles are bad.

*/

------------------------------------------------------------------------------
-- mac watch table for storing watched mac addresses
------------------------------------------------------------------------------
CREATE TABLE manage.macwatch (
  id SERIAL PRIMARY KEY,
  mac MACADDR NOT NULL,
  userid INT REFERENCES profiles.account(id) ON DELETE SET NULL ON UPDATE CASCADE,
  description VARCHAR,
  created TIMESTAMP DEFAULT NOW(),
  prefix_length INT DEFAULT NULL,

  CONSTRAINT macwatch_unique_mac UNIQUE (mac)
);


-- Registry of macwatch matches
-- (since watch rules may have wildcards and/or mac prefixes)
CREATE TABLE macwatch_match (
  id SERIAL PRIMARY KEY,
  macwatch INT NOT NULL REFERENCES macwatch(id) ON DELETE CASCADE ON UPDATE CASCADE,
  cam INT NOT NULL REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  posted TIMESTAMP DEFAULT NOW()
);


------------------------------------------------------------------------------
-- Create table for room images
------------------------------------------------------------------------------
CREATE TABLE image (
  imageid SERIAL PRIMARY KEY,
  roomid VARCHAR REFERENCES room(roomid) NOT NULL,
  title VARCHAR NOT NULL,
  path VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  created TIMESTAMP NOT NULL,
  uploader INT REFERENCES profiles.account(id),
  priority INT
);

------------------------------------------------------------------------------
-- Create basic token storage for api tokens
------------------------------------------------------------------------------
CREATE TABLE apitoken (
  id SERIAL PRIMARY KEY,
  token VARCHAR not null,
  expires TIMESTAMP not null,
  client INT REFERENCES profiles.account(id),
  scope INT DEFAULT 0,
  created TIMESTAMP DEFAULT now(),
  last_used TIMESTAMP,
  comment TEXT,
  revoked BOOLEAN default FALSE,
  endpoints hstore
);


------------------------------------------------------------------------------
-- Threshold rules and related functions
------------------------------------------------------------------------------
CREATE TABLE manage.thresholdrule (
  id SERIAL PRIMARY KEY,
  target VARCHAR NOT NULL,
  alert VARCHAR NOT NULL,
  clear VARCHAR,
  raw BOOLEAN NOT NULL DEFAULT FALSE,
  description VARCHAR,
  creator_id INTEGER DEFAULT NULL,
  created TIMESTAMP DEFAULT NOW(),
  period INTEGER DEFAULT NULL,

  CONSTRAINT thresholdrule_creator_fkey FOREIGN KEY (creator_id)
             REFERENCES profiles.account (id)
             ON UPDATE CASCADE ON DELETE SET NULL

);

-- automatically close thresholdState when threshold rules are removed
CREATE OR REPLACE FUNCTION close_thresholdstate_on_thresholdrule_delete()
RETURNS TRIGGER AS $$
  BEGIN
    IF TG_OP = 'DELETE'
      OR (TG_OP = 'UPDATE' AND
          (OLD.alert <> NEW.alert OR OLD.target <> NEW.target))
    THEN
      UPDATE alerthist
      SET end_time = NOW()
      WHERE subid LIKE (CAST(OLD.id AS text) || ':%')
            AND eventtypeid = 'thresholdState'
            AND end_time >= 'infinity';
    END IF;
    RETURN NULL;
  END;
$$ language 'plpgsql';

CREATE TRIGGER trig_close_thresholdstate_on_thresholdrule_delete
    AFTER UPDATE OR DELETE ON manage.thresholdrule
    FOR EACH ROW
    EXECUTE PROCEDURE close_thresholdstate_on_thresholdrule_delete();


------------------------------------------------------------------------------
-- Alerthist acknowledgements
------------------------------------------------------------------------------
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
