-- Grant web access to unauthorized ajax requests
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/ajax/open/?');
