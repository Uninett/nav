-- Reinstate rule that closes ARP records on netbox deletion, see #2910
CREATE OR REPLACE RULE netbox_close_arp AS ON DELETE TO netbox
  DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

-- Close all open ARP records that have no associated netbox (those that may have been kept open in error due to
-- deletions between 5.10.1 and 5.10.2)
UPDATE arp SET end_time=NOW()
  WHERE end_time>='infinity' AND netboxid IS NULL;

-- Remove actually malfunctioning ARP record closing rule, see #2910
DROP RULE IF EXISTS netbox_status_close_arp ON netbox;
