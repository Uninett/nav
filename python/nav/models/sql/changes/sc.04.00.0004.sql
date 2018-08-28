-- period should be a number of seconds instead, to avoid ambiguities in
-- parsing
ALTER TABLE thresholdrule DROP COLUMN period;
ALTER TABLE thresholdrule ADD COLUMN period INTEGER DEFAULT NULL;
