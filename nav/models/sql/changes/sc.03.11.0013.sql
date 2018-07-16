-- force re-collection of cdp/lldp data to fix data mangled by LP#1037059
-- but only on installs that may be affected by the bug

DELETE FROM netboxinfo
WHERE key='poll_times' AND var IN ('cdp', 'lldp') AND
      EXISTS (SELECT * FROM gwportprefix WHERE gwip='0.0.0.0');

DELETE FROM adjacency_candidate
WHERE source IN  ('cdp', 'lldp') AND
      EXISTS (SELECT * FROM gwportprefix WHERE gwip='0.0.0.0');
