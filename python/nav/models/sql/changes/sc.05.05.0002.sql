--- Create table for storing JWT refresh tokens
CREATE TABLE JWTRefreshToken (
    id SERIAL PRIMARY KEY,
    token VARCHAR NOT NULL,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR
);
