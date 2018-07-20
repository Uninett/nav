
CREATE VIEW enterprise_number AS

WITH enterprise AS (
  SELECT vendorid,
         (string_to_array(sysobjectid, '.'))[7]::INTEGER AS enterprise
  FROM manage.type)
SELECT vendorid, enterprise, count(*)
FROM enterprise
GROUP BY vendorid, enterprise
ORDER BY enterprise, count DESC, vendorid;

COMMENT ON VIEW enterprise_number IS
'Shows the most common enterprise numbers associated with each vendorid, based on the type table';
