---
-- Sort Alert Types when modifying Alert Profiles
---
UPDATE MatchField SET value_sort='alerttype.alerttype' WHERE id=11 AND value_sort='alerttype.alerttypeid';
