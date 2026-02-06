CREATE TABLE profiles.account_default_dashboard (
    account_id INT PRIMARY KEY REFERENCES profiles.account(id) ON UPDATE CASCADE ON DELETE CASCADE,
    dashboard_id INT NOT NULL REFERENCES profiles.account_dashboard(id) ON UPDATE CASCADE ON DELETE CASCADE
);

INSERT INTO profiles.account_default_dashboard (account_id, dashboard_id)
SELECT d.account_id, d.id
FROM profiles.account_dashboard AS d
WHERE d.is_default = true
ON CONFLICT (account_id) DO UPDATE
SET dashboard_id = EXCLUDED.dashboard_id;
