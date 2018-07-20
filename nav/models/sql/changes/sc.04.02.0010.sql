-- Add field location_room_filter to netmap_view
ALTER TABLE netmap_view ADD COLUMN location_room_filter varchar NOT NULL DEFAULT '';