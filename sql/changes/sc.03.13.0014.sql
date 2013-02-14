-- close old, invalid moduleState alerts that may be lingering from NAV
-- versions prior to 3.6 (!)
UPDATE alerthist SET end_time=now()
WHERE
  eventtypeid='moduleState'
  AND end_time >= 'infinity'
  AND COALESCE(subid, '') = '';
