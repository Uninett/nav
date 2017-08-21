CREATE TABLE "manage"."connectionprofile" (
  connectionprofileid SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL UNIQUE,
  description VARCHAR,
  protocol INTEGER NOT NULL,
  port INTEGER,
  snmp_community VARCHAR,
  ca_certificate VARCHAR,
  client_cert VARCHAR,
  username VARCHAR,
  password VARCHAR
);

INSERT INTO connectionprofile (connectionprofileid, protocol, name) VALUES (0, 0, 'No data connection');

ALTER TABLE netbox ADD COLUMN readonly_connection_profile_id INTEGER REFERENCES connectionprofile NOT NULL DEFAULT 0;
ALTER TABLE netbox ADD COLUMN readwrite_connection_profile_id INTEGER REFERENCES connectionprofile NOT NULL DEFAULT 0;

INSERT INTO connectionprofile (protocol, name, snmp_community)
       SELECT 1, 'SNMP v1 profile ' || row, snmp_community FROM
              (SELECT row_number() OVER (ORDER BY snmp_community) as row, snmp_community FROM (SELECT ro as snmp_community from netbox where snmp_version = 1 and ro is not NULL and ro != '' UNION
               SELECT rw as snmp_community from netbox where snmp_version = 1 and rw is not NULL and rw != '') AS snmp) AS snmp2;

INSERT INTO connectionprofile (protocol, name, snmp_community)
       SELECT 2, 'SNMP v2c profile ' || row, snmp_community FROM
              (SELECT row_number() OVER (ORDER BY snmp_community) as row, snmp_community FROM (SELECT ro as snmp_community from netbox where snmp_version = 2 and ro is not NULL and ro != '' UNION
               SELECT rw as snmp_community from netbox where snmp_version = 2 and rw is not NULL and rw != '') AS snmp) AS snmp2;

UPDATE netbox SET readonly_connection_profile_id = (SELECT connectionprofileid FROM connectionprofile WHERE protocol = "snmp_version" AND snmp_community = "ro") WHERE ro is not null and ro != '';
UPDATE netbox SET readwrite_connection_profile_id = (SELECT connectionprofileid FROM connectionprofile WHERE protocol = "snmp_version" AND snmp_community = "rw") WHERE rw is not null and rw != '';

ALTER TABLE netbox DROP COLUMN ro;
ALTER TABLE netbox DROP COLUMN rw;
ALTER TABLE netbox DROP COLUMN snmp_version;
