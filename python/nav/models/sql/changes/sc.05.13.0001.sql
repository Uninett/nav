CREATE TABLE manage.JWTRefreshToken (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    expires TIMESTAMPTZ NOT NULL,
    activates TIMESTAMPTZ NOT NULL,
    hash VARCHAR NOT NULL
);
