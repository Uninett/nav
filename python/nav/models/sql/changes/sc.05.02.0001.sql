-- Rewrite severity values of existing NAV alert history

-- This function will map any severity value in the interval 0-100 to the new 5-1 interval. The current schema
-- allows any integer value in the field, so we map any existing values outside the 0-100 interval to either end of the
-- interval before conversion.
CREATE FUNCTION pg_temp.severitymap(numeric) RETURNS numeric AS
$$ SELECT ROUND(((1.0-(GREATEST(0, LEAST($1, 100.0)) / 100.0)) * 4) + 1)  $$
LANGUAGE sql;

UPDATE eventq SET severity = pg_temp.severitymap(severity);
UPDATE alertq SET severity = pg_temp.severitymap(severity);
UPDATE alerthist SET severity = pg_temp.severitymap(severity);

CREATE DOMAIN severity_value AS INTEGER CHECK(VALUE BETWEEN 1 AND 5) DEFAULT 3;

ALTER TABLE eventq ALTER COLUMN severity TYPE severity_value;
ALTER TABLE alertq ALTER COLUMN severity TYPE severity_value;
ALTER TABLE alerthist ALTER COLUMN severity TYPE severity_value;
