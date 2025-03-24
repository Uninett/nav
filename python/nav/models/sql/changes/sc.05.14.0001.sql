-- Add missing field required when switching to Django's AbstractBaseUser
ALTER TABLE account
ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
