-- Add FeedReader widget with blog.nav.uninett.no/rss as feed to all users.

DO $$DECLARE account RECORD;
BEGIN
  FOR account IN SELECT * FROM account LOOP
    INSERT INTO account_navlet (navlet, account, col, displayorder, preferences) VALUES
    ('nav.web.navlets.feedreader.FeedReaderNavlet', account.id, 2, 0, '(dp0
S''blogurl''
p1
Vhttp://blog.nav.uninett.no/rss
p2
sS''maxposts''
p3
V5
p4
sS''refresh_interval''
p5
I600000
s.');
  END LOOP;
END$$;

