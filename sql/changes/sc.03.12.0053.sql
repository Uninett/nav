-- Grant web access to osm map redirects
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/info/osm_map_redirect/?');
