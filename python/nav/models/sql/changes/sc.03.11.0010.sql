-- Add index to speed up things when looking for open alert states for specific netboxes.
CREATE INDEX alerthist_open_states_by_eventtype ON alerthist USING btree (netboxid, eventtypeid) WHERE end_time >= 'infinity';
