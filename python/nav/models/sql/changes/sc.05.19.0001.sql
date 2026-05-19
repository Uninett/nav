ALTER TABLE profiles.account ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Set is_active for default user to false (in case someone managed to set a password)
UPDATE profiles.account
SET is_active = FALSE
WHERE id = 0;

UPDATE profiles.account
SET is_active = FALSE, password = SUBSTRING(password FROM 2)
WHERE password LIKE '!%';
