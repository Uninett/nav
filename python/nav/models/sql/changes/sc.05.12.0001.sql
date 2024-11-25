-- This migration is to ensure that for accounts that don't have a default
-- dashboard we set a default dashboard

-- This part finds the row with the lowest id for any account that does not
-- have a default dashboard
WITH CTE AS (
  SELECT MIN(id) as id
  FROM account_dashboard a
  WHERE NOT EXISTS (
    SELECT 1 
    FROM account_dashboard b 
    WHERE a.account_id = b.account_id 
    AND b.is_default = TRUE
  )
  GROUP BY account_id
)
-- And this part sets is_default for that row to true
UPDATE account_dashboard
SET is_default = TRUE
WHERE id IN (SELECT id FROM CTE);