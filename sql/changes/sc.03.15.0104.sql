-- Modify netboxmac view to exclude invalid MAC addresses
CREATE OR REPLACE VIEW manage.netboxmac AS

SELECT DISTINCT ON (mac) netboxid, mac FROM (
(

 -- Attempt to get MAC for netbox' monitored IP
 SELECT DISTINCT netbox.netboxid, arp.mac
 FROM netbox
 JOIN arp ON (arp.ip = netbox.ip AND arp.end_time = 'infinity')

) UNION (

 -- Attempt to get MAC for router's interface addresses and virtual addresses
 SELECT interface.netboxid, arp.mac
 FROM arp
 JOIN gwportprefix gwp ON arp.ip = gwp.gwip
 LEFT JOIN (SELECT prefixid, COUNT(*) > 0 AS has_virtual
            FROM gwportprefix
            WHERE virtual=true
            GROUP BY prefixid) AS prefix_virtual_ports ON (gwp.prefixid = prefix_virtual_ports.prefixid)
 JOIN interface USING (interfaceid)
 WHERE arp.end_time = 'infinity'
   AND (gwp.virtual = true OR has_virtual IS NULL)

) UNION (

 -- Get MAC directly from interface physical addresses
 SELECT DISTINCT ON (interface.ifphysaddress) interface.netboxid, interface.ifphysaddress AS mac
   FROM interface
   -- physical ethernet interfaces are assumed to be iftype=6
  WHERE interface.iftype = 6 AND interface.ifphysaddress IS NOT NULL

)

) AS foo
WHERE mac <> '00:00:00:00:00:00' -- exclude invalid MACs
ORDER BY mac, netboxid;
