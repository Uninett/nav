ALTER TABLE profiles.account ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT FALSE;

-- Set is_active true for all accounts that have a password set and that does not start with !
UPDATE profiles.account
SET is_active = TRUE
WHERE password <> '' AND password NOT LIKE '!%';

-- Remove locked indicator (!) from passwords
UPDATE profiles.account
SET password = SUBSTRING(password FROM 2)
WHERE password LIKE '!%';

-- Set default for is_active to true
ALTER TABLE profiles.account ALTER COLUMN is_active SET DEFAULT TRUE;
