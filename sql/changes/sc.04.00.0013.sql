--
-- Drop the accountnavbar table, we don't need it anymore
--
DROP TABLE accountnavbar;


--
-- Delete all link rows with initial links. They are no longer needed.
--
DELETE FROM navbarlink WHERE name='Preferences' AND uri='/preferences';
DELETE FROM navbarlink WHERE name='Toolbox' AND uri='/toolbox';
DELETE FROM navbarlink WHERE name='Useradmin' AND uri='/useradmin/';
DELETE FROM navbarlink WHERE name='Userinfo' AND uri='/userinfo/';
