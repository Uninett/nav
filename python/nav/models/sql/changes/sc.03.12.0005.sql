-- netmap_view_defaultview
CREATE TABLE profiles.netmap_view_defaultview (
  id SERIAL,
  viewid INT4 NOT NULL REFERENCES netmap_view ON UPDATE CASCADE ON DELETE CASCADE,
  ownerid INT4 NOT NULL REFERENCES account ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY (viewid, ownerid)
);
COMMENT ON TABLE netmap_view_defaultview IS 'Stores default views for users in Netmap';