-- Added because macwatch may use mac-address prefixes
CREATE TABLE manage.macwatch_match(
  id SERIAL PRIMARY KEY,
  macwatch INT NOT NULL REFERENCES macwatch(id) ON DELETE CASCADE ON UPDATE CASCADE,
  cam INT NOT NULL REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  posted TIMESTAMP DEFAULT NOW()
);

INSERT INTO macwatch_match (macwatch, cam, posted)
  SELECT id, camid, posted
    FROM macwatch
  WHERE camid IS NOT NULL;

ALTER TABLE macwatch ADD COLUMN prefix_length INT DEFAULT NULL;
ALTER TABLE macwatch ADD CONSTRAINT macwatch_unique_mac UNIQUE (mac);
ALTER TABLE macwatch DROP COLUMN camid;
ALTER TABLE macwatch DROP COLUMN posted;
ALTER TABLE macwatch DROP COLUMN login;
