CREATE TABLE manage.netboxentity (
  netboxentityid SERIAL NOT NULL,
  netboxid INTEGER NOT NULL,

  index VARCHAR NOT NULL,
  source VARCHAR NOT NULL,
  descr VARCHAR,
  vendor_type VARCHAR,
  contained_in_id INTEGER,
  physical_class INTEGER,
  parent_relpos INTEGER,
  name VARCHAR,
  hardware_revision VARCHAR,
  firmware_revision VARCHAR,
  software_revision VARCHAR,
  deviceid INTEGER,
  mfg_name VARCHAR,
  model_name VARCHAR,
  alias VARCHAR,
  asset_id VARCHAR,
  fru BOOLEAN,
  mfg_date TIMESTAMP WITH TIME ZONE,
  uris VARCHAR,
  data hstore NOT NULL DEFAULT hstore(''),

  CONSTRAINT netboxentity_pkey PRIMARY KEY (netboxentityid),
  CONSTRAINT netboxentity_netboxid_fkey
             FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_contained_in_id_fkey
             FOREIGN KEY (contained_in_id)
             REFERENCES netboxentity (netboxentityid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_deviceid_fkey
             FOREIGN KEY (deviceid)
             REFERENCES device (deviceid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT netboxentity_netboxid_source_index_unique
             UNIQUE (netboxid, source, index) INITIALLY DEFERRED

);
