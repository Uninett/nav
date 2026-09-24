UPDATE account_dashboard
SET name = 'New dashboard'
WHERE trim(name) = '';

ALTER TABLE account_dashboard
ADD CONSTRAINT ACCOUNT_DASHBOARD_NAME_NOT_EMPTY_STRING CHECK (trim(name) <> '');
