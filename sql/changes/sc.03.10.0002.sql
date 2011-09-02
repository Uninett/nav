CREATE TABLE manage.powersupply_state (
  stateid SERIAL PRIMARY KEY,
  netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
  power_name VARCHAR,
  discovered TIMESTAMP default NOW(),
  event_posted TIMESTAMP,
  state VARCHAR
);
