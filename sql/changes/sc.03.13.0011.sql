-- remove useless cam constraints/indexes to prevent index bloat
-- On some installs, the index may already have been manually removed. "DROP
-- CONSTRAINT IF EXISTS" wasn't introduced until PostgreSQL 9,
-- so we make a conditional drop function to accomplish this without errors
-- here:

CREATE OR REPLACE FUNCTION manage.drop_constraint(tbl_schema VARCHAR, tbl_name VARCHAR, const_name VARCHAR) RETURNS void AS $$
DECLARE
    exec_string TEXT;
BEGIN
    exec_string := 'ALTER TABLE ';
    IF tbl_schema != NULL THEN
        exec_string := exec_string || quote_ident(tbl_schema) || '.';
    END IF;
    exec_string := exec_string || quote_ident(tb_name)
        || ' DROP CONSTRAINT '
        || quote_ident(const_name);
    EXECUTE exec_string;
EXCEPTION
    WHEN OTHERS THEN
        NULL;
END;
$$ LANGUAGE plpgsql;

SELECT drop_constraint('manage', 'cam', 'cam_netboxid_key');
DROP INDEX IF EXISTS cam_start_time_btree;
