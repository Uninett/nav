-- reset any invalid netbox.up values (those that don't correspond with any
-- unresolved alerthist states - ref: LP#1103929)

UPDATE netbox
SET up='y'
WHERE
  netboxid NOT IN (SELECT netboxid
                   FROM alerthist
                   WHERE
                     eventtypeid = 'boxState'
                     AND end_time >= 'infinity')
  AND up <> 'y';
