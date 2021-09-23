-- Update obsolete Alert Profile filter groups and filters related to severity values
-- These definitions are supplied with NAV. They may have been changed locally, but we don't care ;-)

-- refs:
-- match_field_id for the severity field is 12.
-- operator 2 means ">=", operator 4 means "<="

-- Update the value help text of the matchable severity field
UPDATE MatchField
   SET value_help = 'Range: Severities are in the range 1-5, where 1 is most severe.'
 WHERE id=12;

-- Update F17/G17: All alerts with severity >= Warning
UPDATE filtergroup SET description = 'G17: All alerts with severity <= 4' WHERE id=81;
UPDATE filter SET name = 'F17: All alerts with severity <= 4 ' WHERE id=20;
UPDATE expression SET operator=4, value='4' WHERE id=55;

-- Update F18/G18: All alerts with severity >= Errors
UPDATE filtergroup SET description = 'G18: All alerts with severity <= 3' WHERE id=82;
UPDATE filter SET name = 'F18: All alerts with severity <= 3' WHERE id=21;
UPDATE expression SET operator=4, value='3' WHERE id=57;

-- Update F19/G19: All alerts with severity >= Critical
UPDATE filtergroup SET description = 'G19: All alerts with severity <= 2' WHERE id=83;
UPDATE filter SET name = 'F19: All alerts with severity <= 2' WHERE id=23;
UPDATE expression SET operator=4, value='2' WHERE id=59;

-- Update F20/G20: All alerts with severity = Emergency
UPDATE filtergroup SET description = 'G20: All alerts with severity = 1' WHERE id=84;
UPDATE filter SET name = 'F20: All alerts with severity = 1' WHERE id=24;
UPDATE expression SET operator=4, value='1' WHERE id=61;
