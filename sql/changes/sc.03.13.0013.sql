-- Delete all tuples related to collect_active_ip
DELETE FROM rrd_file WHERE category='activeip' AND key='prefix';
