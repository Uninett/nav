-- Definition of a rack with environment sensors

CREATE TABLE IF NOT EXISTS manage.rack (
  rackid SERIAL PRIMARY KEY,
  roomid VARCHAR REFERENCES room ON DELETE CASCADE,
  rackname VARCHAR,
  ordering INTEGER,
  configuration JSONB DEFAULT NULL,
  item_counter INTEGER NOT NULL DEFAULT 0
);
