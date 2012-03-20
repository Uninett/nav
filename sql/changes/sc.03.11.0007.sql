-- new unrecognized neighbors table
CREATE TABLE manage.unrecognized_neighbor (
  id SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  remote_id VARCHAR NOT NULL,
  remote_name VARCHAR NOT NULL,
  source VARCHAR NOT NULL,
  since TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE unrecognized_neighbor IS 'Unrecognized neighboring devices reported by support discovery protocols';
