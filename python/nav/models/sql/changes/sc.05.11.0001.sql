CREATE TABLE manage.oui (
    oui MACADDR PRIMARY KEY,
    vendor VARCHAR NOT NULL,
    CHECK (oui=trunc(oui))
);
