-- swp_netbox replacement table
CREATE TABLE manage.adjacency_candidate (
  adjacency_candidateid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_interfaceid INT4 REFERENCES interface ON UPDATE CASCADE ON DELETE SET NULL,
  source VARCHAR NOT NULL,
  misscnt INT4 NOT NULL DEFAULT 0,
  UNIQUE(netboxid, interfaceid, to_netboxid, to_interfaceid, source)
);
