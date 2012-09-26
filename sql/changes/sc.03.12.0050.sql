-- Grant web access to unauthorized ajax requests
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 2, 2, '^/ajax/open/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid=2 AND privilegeid=2 AND target='^/ajax/open/?'
  )
;
