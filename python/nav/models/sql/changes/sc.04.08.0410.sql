CREATE TABLE manage.poegroup (
       poegroupid SERIAL PRIMARY KEY,
       netboxid INTEGER NOT NULL REFERENCES netbox ON DELETE CASCADE,
       moduleid INTEGER REFERENCES module ON DELETE CASCADE,
       index INTEGER NOT NULL,
       status INTEGER NOT NULL,
       power INTEGER NOT NULL,
       UNIQUE (netboxid, index)
);

CREATE TABLE manage.poeport (
       poeportid SERIAL PRIMARY KEY,
       netboxid INTEGER NOT NULL REFERENCES netbox ON DELETE CASCADE,
       poegroupid INTEGER NOT NULL REFERENCES poegroup ON DELETE CASCADE,
       interfaceid INTEGER REFERENCES interface ON DELETE CASCADE,
       index INTEGER NOT NULL,
       admin_enable BOOLEAN NOT NULL,
       detection_status INTEGER NOT NULL,
       priority INTEGER NOT NULL,
       classification INTEGER NOT NULL,
       UNIQUE (poegroupid, index)
);
