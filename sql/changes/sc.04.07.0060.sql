-- Definition of a rack and racksensor to display in the rack

CREATE TABLE IF NOT EXISTS rack (
  rackid SERIAL PRIMARY KEY,
  roomid VARCHAR REFERENCES room ON DELETE CASCADE,
  rackname VARCHAR
);

CREATE TABLE IF NOT EXISTS racksensor (
  racksensorid SERIAL PRIMARY KEY,
  rackid INTEGER REFERENCES rack ON DELETE CASCADE,
  sensorid INTEGER REFERENCES sensor ON DELETE CASCADE,
  col INTEGER NOT NULL,
  row INTEGER NOT NULL,
  sensortype VARCHAR
);
