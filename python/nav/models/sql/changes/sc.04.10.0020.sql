CREATE OR REPLACE VIEW manage.netboxmac as
 SELECT DISTINCT ON (foo.mac) foo.netboxid,
    foo.mac
   FROM ( SELECT DISTINCT netbox.netboxid,
            arp.mac
           FROM netbox
             JOIN arp ON arp.ip = netbox.ip AND arp.end_time = 'infinity'::timestamp without time zone
        UNION
         SELECT interface.netboxid,
            arp.mac
           FROM arp
             JOIN gwportprefix gwp ON arp.ip = gwp.gwip
             LEFT JOIN ( SELECT gwportprefix.prefixid,
                    count(*) > 0 AS has_virtual
                   FROM gwportprefix
                  WHERE gwportprefix.virtual = true
                  GROUP BY gwportprefix.prefixid) prefix_virtual_ports ON gwp.prefixid = prefix_virtual_ports.prefixid
             JOIN interface USING (interfaceid)
          WHERE arp.end_time = 'infinity'::timestamp without time zone AND (gwp.virtual = true OR prefix_virtual_ports.has_virtual IS NULL)
        UNION
         SELECT DISTINCT ON (interface.ifphysaddress) interface.netboxid,
            interface.ifphysaddress AS mac
           FROM interface
           WHERE interface.iftype = 6 AND interface.ifphysaddress IS NOT NULL
        UNION
         SELECT DISTINCT ON (netboxinfo.val) netboxinfo.netboxid, netboxinfo.val::macaddr
           FROM netboxinfo
           WHERE (netboxinfo.key = 'bridge_info' AND netboxinfo.var = 'base_address') or
                 (netboxinfo.key = 'lldp' AND netboxinfo.var = 'chassis_mac')) foo
  WHERE foo.mac <> '00:00:00:00:00:00'::macaddr
  ORDER BY foo.mac, foo.netboxid;
