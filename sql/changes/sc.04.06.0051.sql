--- Create table for storing multiple dashboards
CREATE TABLE profiles.account_dashboard (
  id SERIAL PRIMARY KEY,
  name VARCHAR DEFAULT 'My dashboard',
  is_default BOOLEAN DEFAULT FALSE,
  num_columns INT,
  account_id INT REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE
);


--- Widgets should now be a part of a dashboard
ALTER TABLE account_navlet
  ADD dashboard_id INT
    REFERENCES account_dashboard(id)
    ON UPDATE CASCADE ON DELETE CASCADE;


--- Create a dashboard for each user and move all widgets there
DO $$DECLARE thisaccount RECORD;
BEGIN
  FOR thisaccount IN SELECT * FROM account LOOP
    RAISE NOTICE 'Creating dashboard for %s', quote_ident(thisaccount.login);
    WITH inserted AS (
      INSERT INTO account_dashboard (account_id, is_default, num_columns)
      VALUES (thisaccount.id, TRUE, 3) RETURNING id
    )
    UPDATE account_navlet
      SET dashboard_id=inserted.id
      FROM inserted
      WHERE account=thisaccount.id;
  END LOOP;
END$$;
