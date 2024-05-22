-- Remove malfunctioning ARP record closing rule, see #2910
DROP RULE IF EXISTS netbox_close_arp ON netbox;
