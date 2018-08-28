-- fix view that gives wrong ip count in VRRP/HSRP environments
CREATE OR REPLACE VIEW manage.prefix_active_ip_cnt AS
(SELECT prefix.prefixid, COUNT(DISTINCT arp.ip) AS active_ip_cnt
 FROM prefix
 LEFT JOIN arp ON arp.ip << prefix.netaddr
 WHERE arp.end_time = 'infinity'
 GROUP BY prefix.prefixid);
