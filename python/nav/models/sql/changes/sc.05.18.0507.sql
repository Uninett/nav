ALTER TABLE profiles.account ADD COLUMN is_active boolean NOT NULL DEFAULT true;

UPDATE profiles.account
SET is_active = false
WHERE password IS NULL OR password LIKE '!%';

UPDATE profiles.account
SET password = substring(password FROM 2)
WHERE password LIKE '!%';
