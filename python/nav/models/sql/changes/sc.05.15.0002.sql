-- Drop the trigger
DROP TRIGGER IF EXISTS add_default_dashboard_on_account_create ON profiles.account;

-- Drop the function
DROP FUNCTION IF EXISTS create_new_dashboard() CASCADE;
