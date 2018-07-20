-- fix wrong categories in rrd_file table
UPDATE rrd_file SET category='port-counters'
  WHERE category IN ('router-interfaces-counters', 'switch-port-counters');
