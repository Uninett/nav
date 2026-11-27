-- Add covering indexes that speed up Machine Tracker IP and MAC address
-- searches (nav.web.machinetracker), which filter arp/cam by ip- or
-- mac-range together with end_time and order by the same leading column.
--
-- The stock arp_ip_btree/arp_mac_btree/cam_mac_btree indexes only cover the
-- leading column, so end_time is applied as a post-scan Filter and the
-- remaining columns require heap fetches. Folding end_time into the index key
-- and INCLUDE-ing the fetched columns turns these into tight (near) index-only
-- scans and provides the ORDER BY prefix for free.

-- Machine Tracker IP search: WHERE ip BETWEEN .. AND end_time > .. ORDER BY ip
CREATE INDEX arp_ip_end_time_btree ON arp USING btree (ip, end_time)
    INCLUDE (mac, start_time);

-- Machine Tracker MAC search (arp side): WHERE mac BETWEEN .. AND end_time > ..
CREATE INDEX arp_mac_end_time_btree ON arp USING btree (mac, end_time);

-- Machine Tracker MAC search (cam side): WHERE mac BETWEEN .. AND end_time > ..
--   ORDER BY mac, sysname, module, port
CREATE INDEX cam_mac_end_time_btree ON cam USING btree (mac, end_time)
    INCLUDE (netboxid, port, sysname);
