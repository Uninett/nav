/*
 * This script defines auxiliary indexes for NAV tables.
 */


--------------------------------------------
-- Create lookup indexes on manage tables --
--------------------------------------------
SET search_path TO manage;

CREATE INDEX vlan_vlan_btree ON vlan USING btree (vlan);

CREATE INDEX prefix_vlanid_btree ON prefix USING btree (vlanid);

CREATE INDEX interface_to_interfaceid_btree ON interface USING btree (to_interfaceid);

CREATE INDEX gwportprefix_interfaceid_btree ON gwportprefix USING btree (interfaceid);
CREATE INDEX gwportprefix_prefixid_btree ON gwportprefix USING btree (prefixid);

CREATE INDEX swportvlan_interfaceid_btree ON swportvlan USING btree (interfaceid);
CREATE INDEX swportvlan_vlanid_btree ON swportvlan USING btree (vlanid);

CREATE INDEX arp_netboxid_btree ON arp USING btree (netboxid);
CREATE INDEX arp_mac_btree ON arp USING btree (mac);
CREATE INDEX arp_ip_btree ON arp USING btree (ip);
CREATE INDEX arp_start_time_btree ON arp USING btree (start_time);
CREATE INDEX arp_end_time_btree ON arp USING btree (end_time);
CREATE INDEX arp_prefixid_btree ON arp USING btree (prefixid);

CREATE INDEX cam_mac_btree ON cam USING btree (mac);
CREATE INDEX cam_end_time_btree ON cam USING btree (end_time);
CREATE INDEX cam_misscnt_btree ON cam USING btree (misscnt);
CREATE INDEX cam_netboxid_ifindex_end_time_btree ON cam USING btree (netboxid, ifindex, end_time);
-- Index to speed up ipdevinfo queries for the first cam entry from a box
CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);

CREATE INDEX eventq_target_btree ON eventq USING btree (target);

CREATE INDEX eventqvar_eventqid_btree ON eventqvar USING btree (eventqid);

CREATE INDEX alertqmsg_alertqid_btree ON alertqmsg USING btree (alertqid);

CREATE INDEX alertqvar_alertqid_btree ON alertqvar USING btree (alertqid);

CREATE INDEX alerthist_start_time_btree ON alerthist USING btree (start_time);
CREATE INDEX alerthist_end_time_btree ON alerthist USING btree (end_time);

CREATE INDEX alerthistmsg_alerthistid_btree ON alerthistmsg USING btree (alerthistid);

CREATE INDEX alerthistvar_alerthistid_btree ON alerthistvar USING btree (alerthistid);

CREATE INDEX alerthist_open_states_by_eventtype ON alerthist USING btree (netboxid, eventtypeid) WHERE end_time >= 'infinity';

CREATE INDEX cam_open_records_by_netbox ON cam USING btree (netboxid) WHERE end_time >= 'infinity' OR misscnt >= 0;

CREATE INDEX ipdevpoll_job_log_netboxjob_btree ON ipdevpoll_job_log (netboxid, job_name);

CREATE INDEX interface_stack_higher ON interface_stack (higher);
CREATE INDEX interface_stack_lower ON interface_stack (lower);
-- Create index for ip column on manage.netbios to make lookups faster

CREATE INDEX netbios_ip ON manage.netbios (ip);

CREATE INDEX interface_aggregate_aggregator ON interface_aggregate (aggregator);
CREATE INDEX interface_aggregate_interface ON interface_aggregate (interface);


----------------------------------------------
-- Create lookup indexes on profiles tables --
----------------------------------------------
SET search_path TO profiles;

CREATE INDEX account_idx ON Account(login);


--------------------------------------------
-- Create lookup indexes on logger tables --
--------------------------------------------
SET search_path TO logger;

CREATE INDEX log_message_type_btree ON log_message USING btree (type);
CREATE INDEX log_message_origin_btree ON log_message USING btree (origin);
CREATE INDEX log_message_time_btree ON log_message USING btree (time);

-- combined index for quick lookups when expiring old records.
CREATE INDEX log_message_expiration_btree ON log_message USING btree(newpriority, time);
--------------------------------------------
-- Create lookup indexes on radius tables --
--------------------------------------------
SET search_path TO radius;

-- For use by onoff-, update-, stop- and simul_* queries
CREATE INDEX radiusacct_active_user_idx ON radiusacct (UserName) WHERE AcctStopTime IS NULL;
-- and for common statistic queries:
CREATE INDEX radiusacct_start_user_index ON radiusacct (AcctStartTime, lower(UserName));
CREATE INDEX radiusacct_stop_user_index ON radiusacct (AcctStopTime, lower(UserName));

CREATE INDEX radiuslog_time_index ON radiuslog(time);
CREATE INDEX radiuslog_username_index ON radiuslog(lower(UserName));

-- Reset the search path
RESET search_path;
