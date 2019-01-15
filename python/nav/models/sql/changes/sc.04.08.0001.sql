-- delete obsolete function used as trigger on removed rrd tables
DROP FUNCTION IF EXISTS close_thresholdstate_on_threshold_delete();


-- Ensure functions are in correct schema, in a roundabout way:
-- Since bootstrapping from a new baseline already puts it in the correct
-- schema, and moving it to the schema it already is in raises an error, we
-- move it around a bit first :-D
ALTER FUNCTION create_new_dashboard() SET SCHEMA arnold;
ALTER FUNCTION arnold.create_new_dashboard() SET SCHEMA profiles;

ALTER FUNCTION insert_default_navlets_for_existing_users() SET SCHEMA arnold;
ALTER FUNCTION arnold.insert_default_navlets_for_existing_users() SET SCHEMA profiles;

