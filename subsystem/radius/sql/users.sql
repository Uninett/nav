-- User for Freeradius and/or log parsing script, that needs SELECT, INSERT 
-- and UPDATE privilege.
GRANT SELECT, INSERT, UPDATE ON radiusacct TO <navuser>;
GRANT SELECT, INSERT, UPDATE ON radiuslog TO <navuser>;

