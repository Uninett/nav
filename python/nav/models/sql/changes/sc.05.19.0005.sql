UPDATE account_dashboard
SET name = 'New dashboard'
WHERE name ~ '^\s*$';

ALTER TABLE account_dashboard
ADD CONSTRAINT account_dashboard_name_not_blank CHECK (name !~ '^\s*$');
