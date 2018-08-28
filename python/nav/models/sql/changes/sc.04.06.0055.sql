---
-- Give authenticated users access to dashboard urls
---
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 3, 2, '^/index/dashboard/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid = 3 AND privilegeid = 2 AND target = '^/index/dashboard/?'
  );
