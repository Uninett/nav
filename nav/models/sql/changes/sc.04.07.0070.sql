-- Add new fields to sensor table
ALTER TABLE sensor ADD COLUMN display_minimum_user FLOAT DEFAULT null;
ALTER TABLE sensor ADD COLUMN display_maximum_user FLOAT DEFAULT null;
ALTER TABLE sensor ADD COLUMN display_minimum_sys FLOAT DEFAULT null;
ALTER TABLE sensor ADD COLUMN display_maximum_sys FLOAT DEFAULT null;
