-- Resolve alert states for deleted netboxes
UPDATE alerthist
SET end_time=NOW()
WHERE netboxid IS NULL AND end_time = 'infinity';

-- Rule to automatically resolve netbox related alert states when netboxes are
-- deleted.
CREATE OR REPLACE RULE close_alerthist_netboxes AS ON DELETE TO netbox
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE netboxid=OLD.netboxid
       AND end_time='infinity';
