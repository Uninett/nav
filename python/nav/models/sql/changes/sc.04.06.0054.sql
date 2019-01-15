-- Remove the function (and the trigger that uses it) that inserts default
-- navlets. This is now done in the function below - create_new_dashboard()
DROP FUNCTION insert_default_navlets_for_new_users() CASCADE;


-- Create a new dashboard and copy all the widgets from the default user to
-- the dashboard
CREATE OR REPLACE FUNCTION create_new_dashboard() RETURNS trigger AS $$
  BEGIN
    WITH inserted AS (
      INSERT INTO account_dashboard (account_id, is_default, num_columns)
      VALUES (NEW.id, TRUE, 3) RETURNING id
    )
    INSERT INTO account_navlet (account, navlet, displayorder, col, preferences, dashboard_id)
      SELECT NEW.id, navlet, displayorder, col, preferences, (SELECT id from inserted)
        FROM account_navlet WHERE account=0;

    RETURN NULL;
  END
$$ LANGUAGE plpgsql;


-- Creates a dashboard with default widgets for a new user
CREATE TRIGGER add_default_dashboard_on_account_create AFTER INSERT ON account
  FOR EACH ROW
  EXECUTE PROCEDURE create_new_dashboard();
