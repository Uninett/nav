-- Delete unresolved service alerts for services that have been removed
UPDATE alerthist SET end_time=NOW()
WHERE
  eventtypeid='serviceState'
  AND end_time='infinity'
  AND subid SIMILAR TO '[0-9]+'
  AND subid::integer NOT IN (SELECT serviceid FROM service);

-- Ensure any associated service alerts are closed when a service is deleted
CREATE RULE close_alerthist_services
  AS ON DELETE TO service DO
  UPDATE alerthist SET end_time=NOW()
  WHERE
    eventtypeid='serviceState'
    AND end_time='infinity'
    AND subid = old.serviceid::text;
