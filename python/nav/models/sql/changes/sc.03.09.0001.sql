-- Changes necessary to implement the macwatch system

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('info','macWarning','Mac appeared on port');

------------------------------------------------------------------------------
-- mac watch table for storing watched mac addresses
------------------------------------------------------------------------------
CREATE TABLE manage.macwatch (
  id SERIAL PRIMARY KEY,
  camid INT REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  mac MACADDR NOT NULL,
  posted TIMESTAMP,
  userid INT REFERENCES account(id) ON DELETE SET NULL ON UPDATE CASCADE,
  login VARCHAR,
  description VARCHAR,
  created TIMESTAMP DEFAULT NOW()
);
