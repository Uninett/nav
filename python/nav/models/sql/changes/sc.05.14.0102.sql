-- Add email column to account table just to be more compatible with Django user models
ALTER TABLE account ADD COLUMN email VARCHAR(254) DEFAULT NULL;
