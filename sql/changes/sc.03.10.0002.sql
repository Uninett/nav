CREATE TABLE manage.powersupply_state (
    stateid SERIAL PRIMARY KEY,
    netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR NOT NULL,
    descr VARCHAR,
    serialnum VARCHAR,
    modelname VARCHAR,
    down_since TIMESTAMP default NOW(),
    event_posted TIMESTAMP,
    state VARCHAR NOT NULL
);
