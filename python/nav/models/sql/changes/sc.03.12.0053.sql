-- Grant web access to osm map redirects
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 2, 2, '^/info/osm_map_redirect/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid=2 AND privilegeid=2 AND target = '^/info/osm_map_redirect/?'
  )
;
