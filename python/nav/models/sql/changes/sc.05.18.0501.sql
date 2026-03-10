BEGIN;
--
-- Add field aliases to room and location
--
ALTER TABLE "room" ADD COLUMN "aliases" jsonb DEFAULT '[]'::jsonb NOT NULL;
ALTER TABLE "location" ADD COLUMN "aliases" jsonb DEFAULT '[]'::jsonb NOT NULL;
COMMIT;
