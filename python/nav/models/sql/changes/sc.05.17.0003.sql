-- Create a new dashboard, copy all the widgets from the default user to
-- the dashboard, and set the new dashboard as the default dashboard
-- for the newly created account.
CREATE OR REPLACE FUNCTION create_new_dashboard() RETURNS trigger AS $$
  DECLARE
    new_dashboard_id INTEGER;
  BEGIN
    -- Insert dashboard
    INSERT INTO profiles.account_dashboard (account_id, is_default, num_columns)
      VALUES (NEW.id, TRUE, 3)
      RETURNING id INTO new_dashboard_id;

    -- Copy navlets from default user
    INSERT INTO profiles.account_navlet (account, navlet, displayorder, col, preferences, dashboard_id)
      SELECT NEW.id, navlet, displayorder, col, preferences, new_dashboard_id
        FROM profiles.account_navlet WHERE account=0;

    -- Insert into account_default_dashboard
    INSERT INTO profiles.account_default_dashboard (account_id, dashboard_id)
      VALUES (NEW.id, new_dashboard_id);

    RETURN NULL;
  END
$$ LANGUAGE plpgsql;

-- Drop the trigger to allow re-creation with updated create_new_dashboard function
DROP TRIGGER IF EXISTS add_default_dashboard_on_account_create ON profiles.account;

-- Create the trigger
CREATE TRIGGER add_default_dashboard_on_account_create
  AFTER INSERT ON profiles.account
  FOR EACH ROW
  EXECUTE PROCEDURE create_new_dashboard();
