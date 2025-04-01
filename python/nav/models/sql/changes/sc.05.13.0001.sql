CREATE TABLE manage.jwtrefreshtoken (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    expires TIMESTAMP NOT NULL,
    activates TIMESTAMP NOT NULL,
    last_used TIMESTAMP,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    hash VARCHAR NOT NULL
);
