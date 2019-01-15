---
-- Give authenticated users access to Graphite graphs and stuffz
---
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 3, 2, '^/graphite/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid = 3 AND privilegeid = 2 AND target = '^/graphite/?'
  );


---
-- Give authenticated users access to search
---
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 3, 2, '^/search/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid = 3 AND privilegeid = 2 AND target = '^/search/?'
  );
