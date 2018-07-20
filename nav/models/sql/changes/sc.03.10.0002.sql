CREATE TABLE manage.powersupply_or_fan (
    powersupplyid SERIAL PRIMARY KEY,
    netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
    deviceid INT REFERENCES device(deviceid) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR NOT NULL,
    model VARCHAR,
    descr VARCHAR,
    physical_class VARCHAR not null,
    downsince TIMESTAMP default null,
    sensor_oid VARCHAR,
    up CHAR(1) NOT NULL DEFAULT 'u' CHECK (up='y' OR up='n' or up='u' or up='w')
);
