---
-- Delete all widgets from all users
---
DELETE FROM account_navlet;

---
-- Insert default widgets for every existing user
---
CREATE OR REPLACE FUNCTION insert_default_navlets_for_existing_users() RETURNS void AS $$
DECLARE
  account RECORD;
BEGIN
  FOR account IN SELECT * FROM account LOOP
    RAISE NOTICE 'Adding default navlets for %s', quote_ident(account.login);
    INSERT INTO account_navlet (navlet, account, displayorder, col) VALUES
      ('nav.web.navlets.gettingstarted.GettingStartedWidget', account.id, 0, 1),
      ('nav.web.navlets.status.StatusNavlet', account.id, 1, 1),
      ('nav.web.navlets.messages.MessagesNavlet', account.id, 2, 1),
      ('nav.web.navlets.navblog.NavBlogNavlet', account.id, 0, 2),
      ('nav.web.navlets.linklist.LinkListNavlet', account.id, 1, 2);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

SELECT insert_default_navlets_for_existing_users();

---
-- Remove GettingStartedWidget for default user.
---
DELETE FROM account_navlet WHERE account=0 AND navlet='nav.web.navlets.gettingstarted.GettingStartedWidget';

---
-- Create trigger that inserts default navlets for new users
---
CREATE OR REPLACE FUNCTION insert_default_navlets_for_new_users() RETURNS trigger AS $$
    BEGIN
      INSERT INTO account_navlet (account, navlet, displayorder, col, preferences)
        SELECT NEW.id, navlet, displayorder, col, preferences FROM account_navlet WHERE account=0;
      INSERT INTO account_navlet (account, navlet, displayorder, col) VALUES
        (NEW.id, 'nav.web.navlets.gettingstarted.GettingStartedWidget', -1, 1);
      RETURN NULL;
    END
$$ LANGUAGE plpgsql;
