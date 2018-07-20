-- Make sure to close active ARP entries if the source netbox goes down
CREATE OR REPLACE RULE netbox_status_close_arp AS ON UPDATE TO netbox
   WHERE NEW.up='n'
   DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';
