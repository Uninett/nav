CREATE TABLE manage.peersession (
  peersessionid SERIAL NOT NULL,
  netboxid INTEGER NOT NULL,
  protocol INTEGER NOT NULL,
  peer INET NOT NULL,
  state VARCHAR,
  adminstatus VARCHAR,
  local_as INTEGER,
  remote_as INTEGER,
  last_state_change TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT peersession_pkey PRIMARY KEY (peersessionid),
  CONSTRAINT peersession_netboxid_fkey
             FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT peersession_uniq
             UNIQUE (netboxid, protocol, peer)

);

COMMENT ON TABLE peersession IS 'Stores the state of gateway protocol peering sessions';

CREATE OR REPLACE FUNCTION peersession_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.state <> NEW.state THEN
        NEW.last_state_change = now();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER peersession_state_change
  BEFORE UPDATE ON peersession
  FOR EACH ROW EXECUTE PROCEDURE peersession_update_timestamp();
