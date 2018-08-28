CREATE TABLE manage.sensor (
  sensorid SERIAL PRIMARY KEY,
  netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
  oid VARCHAR,
  unit_of_measurement VARCHAR,
  precision integer default 0,
  data_scale VARCHAR,
  human_readable VARCHAR,
  name VARCHAR,
  internal_name VARCHAR,
  mib VARCHAR
);
