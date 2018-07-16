CREATE TABLE manage.thresholdrule (
  id SERIAL PRIMARY KEY,
  target VARCHAR NOT NULL,
  alert VARCHAR NOT NULL,
  clear VARCHAR,
  raw BOOLEAN NOT NULL DEFAULT FALSE,
  period VARCHAR,
  description VARCHAR,
  creator_id INTEGER DEFAULT NULL,
  created TIMESTAMP DEFAULT NOW(),

  CONSTRAINT thresholdrule_creator_fkey FOREIGN KEY (creator_id)
             REFERENCES profiles.account (id)
             ON UPDATE CASCADE ON DELETE SET NULL

);
