-- Add parent field to location table
ALTER TABLE location ADD parent VARCHAR REFERENCES location(locationid) ON UPDATE CASCADE;
