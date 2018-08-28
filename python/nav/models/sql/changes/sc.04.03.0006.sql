-- Modernize existing close_alerthist_modules rule

CREATE OR REPLACE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid = 'moduleState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.moduleid::text;

-- Make similar rule for chassis devices

CREATE OR REPLACE RULE close_alerthist_chassis AS ON DELETE TO netboxentity
  WHERE OLD.physical_class = 3  -- chassis class magic number
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid = 'chassisState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.netboxentityid::text;

-- Make similar rule for interface devices

CREATE OR REPLACE RULE close_alerthist_interface AS ON DELETE TO interface
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid = 'linkState'
       AND end_time >= 'infinity'
       AND netboxid = OLD.netboxid
       AND subid = OLD.interfaceid::text;
