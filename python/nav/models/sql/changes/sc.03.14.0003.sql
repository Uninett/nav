-- create accounttool table for storing personal tool setup
DROP TABLE IF EXISTS accounttool;
DROP TABLE IF EXISTS tool;

CREATE TABLE profiles.accounttool(
  account_tool_id SERIAL PRIMARY KEY,
  toolname VARCHAR,
  accountid INTEGER NOT NULL REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE,
  display BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 0
);
