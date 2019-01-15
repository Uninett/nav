DROP TABLE nav_schema_version;

CREATE TABLE manage.schema_change_log (
    id SERIAL PRIMARY KEY,
    major INTEGER NOT NULL,
    minor INTEGER NOT NULL,
    point INTEGER NOT NULL,
    script_name VARCHAR NOT NULL,
    date_applied TIMESTAMP NOT NULL DEFAULT NOW()
);
