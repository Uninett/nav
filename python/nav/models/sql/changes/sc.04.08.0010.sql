ALTER TABLE adjacency_candidate DROP CONSTRAINT adjacency_candidate_uniq;
ALTER TABLE adjacency_candidate ADD CONSTRAINT adjacency_candidate_uniq UNIQUE(netboxid, interfaceid, to_netboxid, to_interfaceid, source);
