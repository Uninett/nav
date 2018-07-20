-- Some objects may have been installed in the wrong schema over time, due to
-- changes in how navsyncdb handles changes to the PostgreSQL search path.
--
-- We attempt to move potentially affected objects to the correct schema here.
-- However, it is a PostgreSQL error move an object to a schema it is already
-- in, so we move objects back and forth to ensure this changescript works no
-- matter whether the object had been installed originally in the correct
-- schema.

ALTER VIEW enterprise_number SET SCHEMA arnold;
ALTER VIEW arnold.enterprise_number SET SCHEMA manage;

ALTER VIEW netboxmac SET SCHEMA arnold;
ALTER VIEW arnold.netboxmac SET SCHEMA manage;

ALTER TABLE poeport SET SCHEMA arnold;
ALTER TABLE arnold.poeport SET SCHEMA manage;

ALTER TABLE poegroup SET SCHEMA arnold;
ALTER TABLE arnold.poegroup SET SCHEMA manage;

ALTER TABLE report_subscription SET SCHEMA arnold;
ALTER TABLE arnold.report_subscription SET SCHEMA profiles;

ALTER FUNCTION close_snmpagentstates_on_community_clear() SET SCHEMA arnold;
ALTER FUNCTION arnold.close_snmpagentstates_on_community_clear() SET SCHEMA manage;

ALTER FUNCTION close_thresholdstate_on_thresholdrule_delete() SET SCHEMA arnold;
ALTER FUNCTION arnold.close_thresholdstate_on_thresholdrule_delete() SET SCHEMA manage;

ALTER FUNCTION never_use_null_subid() SET SCHEMA arnold;
ALTER FUNCTION arnold.never_use_null_subid() SET SCHEMA manage;

ALTER FUNCTION peersession_update_timestamp() SET SCHEMA arnold;
ALTER FUNCTION arnold.peersession_update_timestamp() SET SCHEMA manage;
