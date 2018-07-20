--
-- Url to info has changed to search. Replace privileges for that
--

UPDATE accountgroupprivilege SET target = '^/search/osm_map_redirect/?' WHERE target = '^/info/osm_map_redirect/?';
