-- Insert an example SNMP v2c management profile if no profiles exist.
-- Typically helpful to get started more easily with a new NAV installation.
INSERT INTO management_profile
  (protocol, name, description, configuration)
SELECT
  1,
  'SNMP v2c read-only',
  'Example SNMP v2c read-only profile with the standard community',
  '{"version": "2c", "community": "public"}'::JSONB
WHERE NOT EXISTS (
  SELECT * FROM management_profile
);
