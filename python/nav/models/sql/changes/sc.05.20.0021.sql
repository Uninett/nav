-- Snapshot of the client authentication sessions (802.1X, MAB, web auth)
-- currently active on each interface, as reported by the switch.
CREATE TABLE manage.interface_access_session (
  interface_access_sessionid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  -- keyed hash of the switch's own session identifier, never the raw value
  session_key VARCHAR NOT NULL,
  -- a VLAN tag claim only; NULL means the session has no assigned VLAN
  vlan_tag INT4 CHECK (vlan_tag BETWEEN 1 AND 4094),
  method VARCHAR NOT NULL DEFAULT 'unknown'
    CHECK (method IN ('dot1x', 'mab', 'webauth', 'unknown')),
  domain VARCHAR NOT NULL DEFAULT 'unknown'
    CHECK (domain IN ('data', 'voice', 'unknown')),
  status VARCHAR NOT NULL DEFAULT 'unknown'
    CHECK (status IN ('pending', 'authenticated', 'authorized',
                      'authentication_failed', 'authorization_failed',
                      'unknown')),
  first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
  -- identifying data, only collected when the operator has opted in
  client_mac MACADDR,
  username VARCHAR,
  UNIQUE (interfaceid, session_key)
);
