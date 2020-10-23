-- fix majorly broken constraint in netboxinfo

-- first, delete duplicates, which might happen on old installations
DELETE FROM netboxinfo WHERE netboxinfoid IN (
    SELECT a.netboxinfoid FROM netboxinfo a JOIN netboxinfo b
    ON (a.netboxid  = b.netboxid AND COALESCE(a.key, '') = COALESCE(b.key, '') AND a.var = b.var AND b.netboxinfoid > a.netboxinfoid)
);

-- THEN, fix the broken constraints
ALTER TABLE netboxinfo DROP CONSTRAINT IF EXISTS netboxinfo_netboxid_key_var_val_key;
ALTER TABLE netboxinfo DROP CONSTRAINT IF EXISTS netboxinfo_uniq;
ALTER TABLE netboxinfo ADD CONSTRAINT netboxinfo_uniq UNIQUE (netboxid, key, var);
