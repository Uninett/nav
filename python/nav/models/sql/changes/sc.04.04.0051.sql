-- Create hstore field on account table
ALTER TABLE account ADD COLUMN preferences hstore DEFAULT hstore('');

