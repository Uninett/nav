-- Include up boxes in the default netbox_maintenance settings
UPDATE statuspreference SET states = 'y,n,s' WHERE id = 3;
