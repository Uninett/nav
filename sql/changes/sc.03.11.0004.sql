-- Fix improper unique constraint on adjacency_candidate. Unfortunately, the
-- constraint name is different on different versions of PostgreSQL, so we
-- might as well drop the table and re-create it.  Don't worry, its contents
-- will be re-populated as soon as NAV is restarted.
DROP TABLE adjacency_candidate;

CREATE TABLE manage.adjacency_candidate (
  adjacency_candidateid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_interfaceid INT4 REFERENCES interface ON UPDATE CASCADE ON DELETE SET NULL,
  source VARCHAR NOT NULL,
  misscnt INT4 NOT NULL DEFAULT 0,
  CONSTRAINT adjacency_candidate_uniq UNIQUE(netboxid, interfaceid, to_netboxid, source)
);
