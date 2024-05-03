CREATE TABLE manage.oui (
    id SERIAL PRIMARY KEY,
    vendor VARCHAR NOT NULL,
    oui MACADDR NOT NULL UNIQUE,
    CHECK (oui=trunc(oui))
);
