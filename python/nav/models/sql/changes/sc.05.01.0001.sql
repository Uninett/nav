-- Make it so AS numbers can be really big,
ALTER TABLE peersession
  ALTER COLUMN local_as TYPE BIGINT,
  ALTER COLUMN remote_as TYPE BIGINT
;