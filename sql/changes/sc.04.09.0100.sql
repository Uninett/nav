-- Make sure refresh session is open for all.
--
-- Do this by adding web_access for the refresh_session url to the group
-- "Everyone"

INSERT INTO accountgroupprivilege
    (accountgroupid, privilegeid, target)
SELECT 2, 2, '^/refresh_session'
WHERE
    NOT EXISTS (
        SELECT * FROM accountgroupprivilege WHERE target='^/refresh_session'
    );
