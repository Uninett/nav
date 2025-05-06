-- Delete widget_columns key from account preferences
UPDATE account
SET preferences = delete(preferences, 'widget_columns')
WHERE preferences ? 'widget_columns';
