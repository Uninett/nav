-- Make sure allauths many login urls are open for all.
--
-- Do this by adding web_access for the urls to the group
-- "Everyone"

INSERT INTO accountgroupprivilege
    (accountgroupid, privilegeid, target)
SELECT 2, 2, '^/accounts/\\w+(/\\w+)?/login'
WHERE
    NOT EXISTS (
        SELECT * FROM accountgroupprivilege WHERE target='^/accounts/\\w+(/\\w+)?/login'
    );
