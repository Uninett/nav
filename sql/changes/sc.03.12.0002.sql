TRUNCATE TABLE netmap_view CASCADE;
ALTER TABLE netmap_view ADD COLUMN topology INT4 NOT NULL;
ALTER TABLE netmap_view DROP COLUMN link_types;