-- Add index to speed up lookups for open cam records for specific netboxes
CREATE INDEX cam_open_records_by_netbox ON cam USING btree (netboxid) WHERE end_time >= 'infinity' OR misscnt >= 0;
