CREATE TABLE manage.powersupply (
    powersupplyid SERIAL PRIMARY KEY,
    netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
    deviceid INT REFERENCES device(deviceid) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR NOT NULL,
    model VARCHAR,
    descr VARCHAR,
    downsince TIMESTAMP default NOW(),
    up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n')
);
