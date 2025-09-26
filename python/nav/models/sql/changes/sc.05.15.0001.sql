ALTER TABLE account_dashboard
ADD COLUMN is_shared BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE profiles.account_dashboard_subscription (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE,
    dashboard_id INT REFERENCES account_dashboard(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT unique_account_dashboard_subscription UNIQUE(account_id, dashboard_id)
)
