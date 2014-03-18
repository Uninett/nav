-- Fix maintenance tasks that are open "until the end of time" (LP#1273706)
UPDATE maint_task
SET maint_end = 'infinity'
WHERE extract(year from maint_end) = 9999;
