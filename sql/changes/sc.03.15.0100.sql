-- Create table for storing navlet information for a user

DROP TABLE profiles.account_navlet;
CREATE TABLE IF NOT EXISTS profiles.account_navlet (
  id SERIAL PRIMARY KEY,
  navlet VARCHAR NOT NULL,
  account INT REFERENCES profiles.account(id),
  displayorder INT NOT NULL,
  options VARCHAR
);
