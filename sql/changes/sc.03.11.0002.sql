-- Change swportblocked primary key to a simple integer, since Django requires it.
ALTER TABLE swportblocked
  DROP CONSTRAINT swportblocked_pkey;

ALTER TABLE swportblocked
  ADD CONSTRAINT swportblocked_uniq UNIQUE (interfaceid, vlan);

ALTER TABLE swportblocked
  ADD COLUMN swportblockedid SERIAL PRIMARY KEY;
