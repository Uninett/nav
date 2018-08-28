-- Due to changes in requirements, remove all feedreaders with nav blog as source
DELETE FROM account_navlet WHERE preferences LIKE '%http://blog.nav.uninett.no/rss%';

-- Add new blog navlet to all users. Exclude those that have already activated it.
DO $$DECLARE account_record RECORD;
BEGIN
  FOR account_record IN SELECT * FROM account WHERE id NOT IN (SELECT account FROM account_navlet WHERE navlet = 'nav.web.navlets.navblog.NavBlogNavlet') LOOP
    INSERT INTO account_navlet (navlet, account, col, displayorder, preferences) VALUES
    ('nav.web.navlets.navblog.NavBlogNavlet', account_record.id, 2, 0, '(dp0
S''refresh_interval''
p1
I600000
s.');
  END LOOP;
END$$;
