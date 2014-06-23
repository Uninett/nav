-- For some reason, the subid 0 has been used for years when posting boxState
-- events. This makes no sense, and complicates matching of events to form
-- coherent states. Remove usages of this subid.
UPDATE eventq SET subid = NULL WHERE eventtypeid = 'boxState' AND subid = '0';
UPDATE alertq SET subid = NULL WHERE eventtypeid = 'boxState' AND subid = '0';
UPDATE alerthist SET subid = NULL WHERE eventtypeid = 'boxState' AND subid = '0';
