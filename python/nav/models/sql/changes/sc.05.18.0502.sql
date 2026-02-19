-- Grant web access to /account/ for authenticated users
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 3, 2, '^/account/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid = 3 AND privilegeid = 2 AND target = '^/account/?'
  );
