-- Add rule to resolve open alerts for bgp sessions that are deleted
CREATE OR REPLACE RULE close_alerthist_peersession AS ON DELETE TO peersession
  DO UPDATE alerthist SET end_time=NOW()
     WHERE eventtypeid = 'bgpState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.peersessionid::text;
