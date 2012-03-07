-- fix improper unique constraint on adjacency_candidate
DELETE FROM manage.adjacency_candidate;

ALTER TABLE manage.adjacency_candidate
  DROP CONSTRAINT adjacency_candidate_netboxid_key;

ALTER TABLE manage.adjacency_candidate
  ADD CONSTRAINT adjacency_candidate_uniq UNIQUE (netboxid, interfaceid, to_netboxid, source);
