-- Create table for storing navlet information for a user

CREATE TABLE IF NOT EXISTS profiles.account_navlet (
  id SERIAL PRIMARY KEY,
  navlet VARCHAR NOT NULL,
  account INT REFERENCES profiles.account(id),
  col INT,
  displayorder INT NOT NULL,
  preferences VARCHAR
);
