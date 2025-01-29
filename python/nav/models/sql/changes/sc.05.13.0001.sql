CREATE TABLE manage.JWTRefreshToken (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    hash VARCHAR NOT NULL
);
