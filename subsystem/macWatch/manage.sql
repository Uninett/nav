CREATE TABLE macwatch (
id SERIAL PRIMARY KEY,
camid int REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
mac macaddr NOT NULL,
posted timestamp,
userid int REFERENCES account(id) ON DELETE SET NULL ON UPDATE CASCADE,
login varchar,
description varchar,
created timestamp default now()
);

INSERT INTO subsystem (name) VALUES ('macwatch');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) 
VALUES ('info','macWarning','Mac appeared on port');

