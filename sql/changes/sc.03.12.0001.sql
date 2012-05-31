-- netmap_view
CREATE TABLE profiles.netmap_view (
  viewid VARCHAR PRIMARY KEY,
  owner INT4 NOT NULL REFERENCES account ON UPDATE CASCADE ON DELETE CASCADE,
  title VARCHAR NOT NULL,
  link_types VARCHAR NOT NULL,
  categories VARCHAR NOT NULL,
  zoom VARCHAR NOT NULL,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  last_modified TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE netmap_view IS 'Stored views with settings for NetMap';

CREATE TABLE profiles.netmap_view_nodeposition (
  viewid VARCHAR NOT NULL REFERENCES netmap_view ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  x INT4 NOT NULL,
  y INT4 NOT NULL
);
