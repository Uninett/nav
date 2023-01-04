--- Create table for storing JWT refresh tokens
CREATE TABLE api.JWTRefreshToken (
    id SERIAL PRIMARY KEY,
    token VARCHAR NOT NULL,
    name VARCHAR NOT NULL
);
