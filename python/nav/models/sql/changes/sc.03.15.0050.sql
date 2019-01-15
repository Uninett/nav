-- Map topology id to match OSI layer number
UPDATE profiles.netmap_view SET topology = 3 where topology = 2;
UPDATE profiles.netmap_view SET topology = 2 where topology = 1;