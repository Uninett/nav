-- Delete all tuples related to collect_active_ip because trigger did not exist in early beta
-- The data will be restored on next run of collect_active_ip
DELETE FROM rrd_file
  WHERE category = 'activeip' AND key = 'prefix';

-- Create trigger to delete rrd_file tuples regarding deleted prefix
CREATE OR REPLACE RULE prefix_on_delete_do_clean_rrd_file AS ON DELETE TO prefix
  DO DELETE FROM rrd_file
      WHERE category = 'activeip'
          AND key = 'prefix' AND CAST(value AS int) = OLD.prefixid;
