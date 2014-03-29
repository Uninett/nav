-- Clean up scale/precision problems of already known APC sensors (LP#1270095)

UPDATE sensor
SET precision=1, data_scale=NULL
WHERE mib = 'PowerNet-MIB'
      AND data_scale = 'deci';

UPDATE sensor
SET precision=2, data_scale=NULL
WHERE mib = 'PowerNet-MIB'
      AND data_scale = 'centi';
