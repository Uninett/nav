------------------------------------------------------------------------------
-- mac watch table for storing watched mac addresses
------------------------------------------------------------------------------
CREATE TABLE manage.macwatch (
  id SERIAL PRIMARY KEY,
  camid INT REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  mac MACADDR NOT NULL,
  posted TIMESTAMP,
  userid INT REFERENCES profiles.account(id) ON DELETE SET NULL ON UPDATE CASCADE,
  login VARCHAR,
  description VARCHAR,
  created TIMESTAMP DEFAULT NOW()
);

-- Create table for images

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

ALTER SEQUENCE eventqvar_id_seq OWNED BY manage.eventqvar.id;
ALTER SEQUENCE profiles.accountgroup_accounts_id_seq OWNED BY profiles.accountgroup_accounts.id;
ALTER SEQUENCE profiles.accountproperty_id_seq OWNED BY profiles.accountproperty.id;
ALTER SEQUENCE profiles.alertsender_id_seq OWNED BY profiles.alertsender.id;
ALTER SEQUENCE profiles.alertprofile_id_seq OWNED BY profiles.alertprofile.id;
ALTER SEQUENCE profiles.alertaddress_id_seq OWNED BY profiles.alertaddress.id;
ALTER SEQUENCE profiles.timeperiod_id_seq OWNED BY profiles.timeperiod.id;
ALTER SEQUENCE profiles.filtergroup_group_permission_id_seq OWNED BY profiles.filtergroup_group_permission.id;
ALTER SEQUENCE profiles.filtergroup_id_seq OWNED BY profiles.filtergroup.id;
ALTER SEQUENCE profiles.filtergroupcontent_id_seq OWNED BY profiles.filtergroupcontent.id;
ALTER SEQUENCE profiles.expression_id_seq OWNED BY profiles.expression.id;
ALTER SEQUENCE profiles.filter_id_seq OWNED BY profiles.filter.id;
ALTER SEQUENCE profiles.operator_operator_id_seq OWNED BY profiles.operator.operator_id;
ALTER SEQUENCE profiles.operator_id_seq OWNED BY profiles.operator.id;
ALTER SEQUENCE profiles.matchfield_id_seq OWNED BY profiles.matchfield.id;
ALTER SEQUENCE profiles.alertsubscription_id_seq OWNED BY profiles.alertsubscription.id;
ALTER SEQUENCE profiles.navbarlink_id_seq OWNED BY profiles.navbarlink.id;
ALTER SEQUENCE profiles.accountorg_id_seq OWNED BY profiles.accountorg.id;
ALTER SEQUENCE profiles.account_id_seq OWNED BY profiles.account.id;
ALTER SEQUENCE profiles.accountgroup_id_seq OWNED BY profiles.accountgroup.id;
ALTER SEQUENCE profiles.accountgroupprivilege_id_seq OWNED BY profiles.accountgroupprivilege.id;
ALTER SEQUENCE profiles.privilege_id_seq OWNED BY profiles.privilege.privilegeid;
ALTER SEQUENCE profiles.statuspreference_organization_id_seq OWNED BY profiles.statuspreference_organization.id;
ALTER SEQUENCE profiles.statuspreference_id_seq OWNED BY profiles.statuspreference.id;
ALTER SEQUENCE profiles.statuspreference_category_id_seq OWNED BY profiles.statuspreference_category.id;

INSERT INTO subsystem (
  SELECT 'macwatch' AS name
  WHERE NOT EXISTS (
    SELECT name FROM subsystem WHERE name='macwatch'));

-- Added because macwatch may use mac-address prefixes
CREATE TABLE macwatch_match(
  id SERIAL PRIMARY KEY,
  macwatch INT NOT NULL REFERENCES macwatch(id) ON DELETE CASCADE ON UPDATE CASCADE,
  cam INT NOT NULL REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  posted TIMESTAMP DEFAULT NOW()
);

INSERT INTO macwatch_match (macwatch, cam, posted)
  SELECT id, camid, posted
    FROM macwatch
  WHERE camid IS NOT NULL;

ALTER TABLE macwatch ADD COLUMN prefix_length INT DEFAULT NULL;
ALTER TABLE macwatch ADD CONSTRAINT macwatch_unique_mac UNIQUE (mac);
ALTER TABLE macwatch DROP COLUMN camid;
ALTER TABLE macwatch DROP COLUMN posted;
ALTER TABLE macwatch DROP COLUMN login;

-- Create basic token storage for api tokens

CREATE TABLE apitoken (
  id SERIAL PRIMARY KEY,
  token VARCHAR not null,
  expires TIMESTAMP not null,
  client INT REFERENCES profiles.account(id),
  scope INT DEFAULT 0
);

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

-- Add fields to apitoken
ALTER TABLE apitoken ADD COLUMN created TIMESTAMP DEFAULT now();
ALTER TABLE apitoken ADD COLUMN last_used TIMESTAMP;
ALTER TABLE apitoken ADD COLUMN comment TEXT;
ALTER TABLE apitoken ADD COLUMN revoked BOOLEAN default FALSE;
ALTER TABLE apitoken ADD COLUMN endpoints hstore;

UPDATE apitoken SET created = NULL;
