-- Use the migrate_tools.py script to fill the tools table with tools from the tool files
CREATE TABLE profiles.tool(
  toolid SERIAL PRIMARY KEY,
  toolname VARCHAR NOT NULL UNIQUE,
  uri VARCHAR NOT NULL,
  icon VARCHAR,
  description VARCHAR,
  priority integer DEFAULT 0
);

CREATE TABLE profiles.accounttool(
  accounttoolid SERIAL PRIMARY KEY,
  toolid INTEGER NOT NULL REFERENCES tool ON UPDATE CASCADE ON DELETE CASCADE,
  accountid INTEGER NOT NULL REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE,
  display BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 0
);
