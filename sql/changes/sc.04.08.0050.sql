CREATE TABLE IF NOT EXISTS profiles.report_subscription (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES account ON DELETE CASCADE ON UPDATE CASCADE,
    address_id INT REFERENCES alertaddress ON DELETE CASCADE ON UPDATE CASCADE,
    period VARCHAR NOT NULL,
    report_type VARCHAR NOT NULL
);
