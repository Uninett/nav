-- Drop fields that have been obsolete for many NAV versions.
ALTER TABLE manage.type
    DROP COLUMN cdp,
    DROP COLUMN tftp,
    DROP COLUMN cs_at_vlan,
    DROP COLUMN chassis;
