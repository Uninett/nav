-- This migration is to ensure that for accounts that have more than one
-- default dashboard we set is_default to false for all except for one

UPDATE account_dashboard
SET is_default = FALSE
WHERE id NOT IN (
  -- This part finds the lowest id of the default dashboards for each
  -- account_id 
  SELECT MIN(id)
  FROM account_dashboard
  WHERE is_default = TRUE
  GROUP BY account_id
)
AND account_id IN (
  -- This part finds all account_ids that have more than one default dashboard
  SELECT account_id
  FROM account_dashboard
  WHERE is_default = TRUE
  GROUP BY account_id
  HAVING COUNT(account_id) > 1
)