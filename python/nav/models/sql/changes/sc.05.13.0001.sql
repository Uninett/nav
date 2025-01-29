CREATE TABLE manage.JWTRefreshToken (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    expires TIMESTAMP NOT NULL,
    activates TIMESTAMP NOT NULL,
    hash VARCHAR NOT NULL
);
