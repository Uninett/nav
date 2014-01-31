---
-- Give everyone access to navlets
---
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 2, 2, '^/navlets/.*' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid = 2 AND privilegeid = 2 AND target = '^/navlets/.*'
  );


---
-- Insert default navlets for every existing user
---
CREATE OR REPLACE FUNCTION insert_default_navlets_for_existing_users() RETURNS void AS $$
DECLARE
  account RECORD;
BEGIN
  FOR account IN SELECT * FROM account LOOP
    RAISE NOTICE 'Adding default navlets for %s', quote_ident(account.login);
    INSERT INTO account_navlet (navlet, account, displayorder, col) VALUES
      ('nav.web.navlets.welcome.WelcomeNavlet', account.id, 0, 1),
      ('nav.web.navlets.linklist.LinkListNavlet', account.id, 0, 2),
      ('nav.web.navlets.messages.MessagesNavlet', account.id, 1, 2);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

SELECT insert_default_navlets_for_existing_users();


---
-- Create trigger that inserts default navlets for new users
---
CREATE OR REPLACE FUNCTION insert_default_navlets_for_new_users() RETURNS trigger AS $$
    BEGIN
      INSERT INTO account_navlet (account, navlet, displayorder, col, preferences)
        SELECT NEW.id, navlet, displayorder, col, preferences FROM account_navlet WHERE account=0;
      RETURN NULL;
    END
$$ LANGUAGE plpgsql;

CREATE TRIGGER add_default_navlets_on_account_create AFTER INSERT ON account
  FOR EACH ROW
  EXECUTE PROCEDURE insert_default_navlets_for_new_users();
