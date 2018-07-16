-- Create table for netbios names

CREATE TABLE manage.netbios (
  netbiosid SERIAL PRIMARY KEY,
  ip INET NOT NULL,
  mac MACADDR NOT NULL,
  name VARCHAR NOT NULL,
  server VARCHAR NOT NULL,
  username VARCHAR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity'
);
