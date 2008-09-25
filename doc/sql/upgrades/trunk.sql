/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.3 to the current trunk revision.  Please update this with every
 * change you make to the database initialization scripts.  It will eventually
 * become the update script for the next release.
 *
 * Also, if you are keeping your installation in sync with trunk, you should
 * watch this file for changes and run them when updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql manage <username>
 *
*/

-- Clean install of 3.3.0 caused this rule never to be created.  Recreate it
-- here for those who started out with clean 3.3.0 installs.
-- NAV 3.3.1 also contained bug SF#1899431 in this rule, which has
-- been fixed here, and should be applied when upgrading.
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid AND end_time='infinity';

-- Replace the netboxid_null_upd_end_time trigger, which has been
-- faulty the last six years.
CREATE OR REPLACE FUNCTION netboxid_null_upd_end_time () RETURNS trigger AS
  'BEGIN
     IF old.netboxid IS NOT NULL AND new.netboxid IS NULL 
        AND new.end_time = ''infinity'' THEN
       new.end_time = current_timestamp;
     END IF;
     RETURN new;
   end' LANGUAGE plpgsql;

-- Django needs a single column it can treat as primary key :-(
ALTER TABLE netboxcategory ADD COLUMN id SERIAL;
ALTER TABLE netbox_vtpvlan ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE netboxsnmpoid ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE serviceproperty ADD COLUMN id SERIAL;
ALTER TABLE maint_component ADD COLUMN id SERIAL;
ALTER TABLE message_to_maint_task ADD COLUMN id SERIAL;
ALTER TABLE alertqmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alertqvar ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistvar ADD COLUMN id SERIAL PRIMARY KEY;

ALTER TABLE accountproperty ADD COLUMN id SERIAL;

ALTER TABLE brukerrettighet DROP CONSTRAINT brukerrettighet_pk;
ALTER TABLE brukerrettighet ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE brukerrettighet ADD UNIQUE(accountid, utstyrgruppeid);

ALTER TABLE defaultfilter DROP CONSTRAINT defaultfilter_pk;
ALTER TABLE defaultfilter ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE defaultfilter ADD UNIQUE(accountgroupid, utstyrfilterid);

ALTER TABLE defaultutstyr DROP CONSTRAINT defaultutstyr_pk;
ALTER TABLE defaultutstyr ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE defaultutstyr ADD UNIQUE(accountgroupid, utstyrgruppeid);

ALTER TABLE grouptilfilter DROP CONSTRAINT gruppetilfilter_pk;
ALTER TABLE grouptilfilter ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE grouptilfilter ADD UNIQUE(utstyrfilterid, utstyrgruppeid);

ALTER TABLE operator DROP CONSTRAINT operator_pk;
ALTER TABLE operator id SERIAL PRIMARY KEY;
ALTER TABLE operator ADD UNIQUE(operatorid, matchfieldid);

ALTER TABLE rettighet DROP CONSTRAINT rettighet_pk;
ALTER TABLE rettighet ADD COLUMN id PRIMARY KEY;
ALTER TABLE rettighet ADD UNIQUE(accountgroupid,, utstyrgruppeid)

ALTER TABLE brukerrettighet DROP CONSTRAINT brukerrettighet_pk;
ALTER TABLE brukerrettighet ADD COLUMN id PRIMARY KEY;
ALTER TABLE brukerrettighet ADD UNIQUE(accountid, utstyrgruppeid)

ALTER TABLE varsle DROP CONSTRAINT varsleadresse_pk;
ALTER TABLE varsle ADD COLUMN id PRIMARY KEY;
ALTER TABLE varsle ADD UNIQUE(alarmadresseid, tidsperiodeid, utstyrgruppeid);

-- We wan't english names for everything so here goes:
-- FIXME rename all pkeys etc.
ALTER TABLE rettighet RENAME TO filtergroup_group_permision;
ALTER TABLE filtergroup_group_permision RENAME utstyrgruppeid TO filtergroup_id;
ALTER TABLE filtergroup_group_permision RENAME accountgroupid TO accountgroup_id;

ALTER TABLE alarmadresse RENAME TO alertaddress;
ALTER TABLE alertaddress RENAME adresse TO address;

ALTER TABLE preference RENAME TO alertpreference;

ALTER TABLE brukerprofil RENAME TO alertprofile;
ALTER TABLE alertprofile RENAME navn TO name;
ALTER TABLE alertprofile RENAME tid TO daily_dispatch_time;
ALTER TABLE alertprofile RENAME ukedag TO weekly_dispatch_day;
ALTER TABLE alertprofile RENAME uketid TO weekly_dispatch_time;

ALTER TABLE tidsperiode RENAME TO timeperiod;
ALTER TABLE timeperiod RENAME brukerprofilid TO alert_profile_id;
ALTER TABLE timeperiod RENAME starttid TO start_time;
ALTER TABLE timeperiod RENAME helg TO valid_during;

ALTER TABLE varsle RENAME TO alertsubscription;
ALTER TABLE alertsubscription RENAME alarmadresseid TO alert_address_id;
ALTER TABLE alertsubscription RENAME tidsperiodeid TO time_period_id;
ALTER TABLE alertsubscription RENAME utstyrgruppeid TO filter_group_id;
ALTER TABLE alertsubscription RENAME vent TO subscription_type;

ALTER TABLE gruppetilfilter RENAME TO  filtergroupcontent;
ALTER TABLE filtergroupcontent RENAME inkluder TO include;
ALTER TABLE filtergroupcontent RENAME positiv TO positive;
ALTER TABLE filtergroupcontent RENAME prioritet TO priority;
ALTER TABLE filtergroupcontent RENAME utstyrfilterid TO filter_id;
ALTER TABLE filtergroupcontent RENAME utstyrgruppeid TO filter_group_id;

ALTER TABLE operator RENAME operatorid TO operator_id;
ALTER TABLE operator RENAME matchfieldid TO match_field_id;

ALTER TABLE filtermatch RENAME TO expresion;
ALTER TABLE expresion RENAME utstyrfilterid TO filter_id;
ALTER TABLE expresion RENAME matchfelt TO match_field_id;
ALTER TABLE expresion RENAME matchtype TO operator;
ALTER TABLE expresion RENAME verdi TO value;

ALTER TABLE utstyrfilter RENAME TO filter;
ALTER TABLE filter RENAME accountid TO owner_id;
ALTER TABLE filter RENAME navn TO name;

ALTER TABLE utstyrgruppe RENAME TO filtergroup;
ALTER TABLE filtergroup RENAME accountid TO owner_id;
ALTER TABLE filtergroup RENAME navn TO name;

ALTER TABLE matchfield RENAME matchfieldid TO id;
ALTER TABLE matchfield RENAME valueid TO value_id;
ALTER TABLE matchfield RENAME valuename TO value_name;
ALTER TABLE matchfield RENAME valuehelp TO value_help;
ALTER TABLE matchfield RENAME valuecategory TO value_category;
ALTER TABLE matchfield RENAME valuesort TO value_sort;
ALTER TABLE matchfield RENAME listlimit TO list_limit;
ALTER TABLE matchfield RENAME datatype TO data_type;
ALTER TABLE matchfield RENAME showlist TO show_list;

ALTER TABLE queue RENAME TO accountalertqueue;
ALTER TABLE accountalertqueue RENAME accountid TO account_id;
ALTER TABLE accountalertqueue RENAME alertid TO alert_id;
ALTER TABLE accountalertqueue RENAME time TO insertion_time;

ALTER TABLE filtergroup RENAME descr TO description;
ALTER TABLE matchfield RENAME descr TO description;

-- Add new fields
ALTER TABLE alertsubscription ADD ignore_closed_alerts BOOLEAN;
ALTER TABLE alertq ADD closed BOOLEAN;
-- FIXME add subscrition to accountalertqueue

-- Rename indexes so they match with the new english table names
ALTER INDEX alarmadresse_pk RENAME TO alertaddress_pkey;
ALTER INDEX preference_pk RENAME TO alertpreference_pkey;
ALTER INDEX brukerprofil_pk RENAME TO alertprofile_pkey;
ALTER INDEX tidsperiode_pk RENAME TO timeperiod_pkey;
ALTER INDEX varsle_pkey RENAME TO alertsubscription_pkey;
ALTER INDEX varsle_alarmadresseid_key RENAME TO alertsubscription_alert_address_id_key;
ALTER INDEX gruppetilfilter_pkey RENAME TO filtergroupcontent_pkey;
ALTER INDEX gruppetilfilter_utstyrfilterid_key RENAME TO filtergroupcontent_filter_id_key;
ALTER INDEX operator_operatorid_key RENAME TO operator_operator_id_key;
ALTER INDEX filtermatch_pk RENAME TO filtermatch_pkey;
ALTER INDEX utstyrfilter_pk RENAME TO filter_pkey;
ALTER INDEX utstyrgruppe_pk RENAME TO filtergroup_pkey;
ALTER INDEX matchfield_pk RENAME TO matchfield_pkey;
ALTER INDEX queue_pkey RENAME TO accountalertqueue_pkey;

-- Rename sequences so they match with the new english table names
-- NOTE Internally a sequence has a column named 'sequence_name' which keeps
-- the name of the sequence. This value will not be changed when renaming
-- sequences, and you can not use UPDATE to set it either.
ALTER TABLE alarmadresse_id_seq RENAME TO alertaddress_id_seq;
ALTER TABLE alertaddress ALTER COLUMN id SET DEFAULT nextval('alertaddress_id_seq');

ALTER TABLE brukerprofil_id_seq RENAME TO alertprofile_id_seq;
ALTER TABLE alertprofile ALTER COLUMN id SET DEFAULT nextval('alertprofile_id_seq');

ALTER TABLE tidsperiode_id_seq RENAME TO timeperiod_id_seq;
ALTER TABLE timeperiod ALTER COLUMN id SET DEFAULT nextval('timeperiod_id_seq');

ALTER TABLE varsle_id_seq RENAME TO alertsubscription_id_seq;
ALTER TABLE alertsubscription ALTER COLUMN id SET DEFAULT nextval('alertsubscription_id_seq');

ALTER TABLE gruppetilfilter_id_seq RENAME TO filtergroupcontent_id_seq;
ALTER TABLE filtergroupcontent ALTER COLUMN id SET DEFAULT nextval('filtergroupcontent_id_seq');

ALTER TABLE operator_id_seq RENAME TO operator_operator_id_seq;
ALTER TABLE operator ALTER COLUMN id SET DEFAULT nextval('operator_operator_id_seq');
ALTER TABLE operator_id_seq1 RENAME TO operator_id_seq;
ALTER TABLE operator ALTER COLUMN id SET DEFAULT nextval('operator_id_seq');

ALTER TABLE filtermatch_id_seq RENAME TO expresion_id_seq;
ALTER TABLE expresion ALTER COLUMN id SET DEFAULT nextval('expresion_id_seq');

ALTER TABLE utstyrfilter_id_seq RENAME TO filter_id_seq;
ALTER TABLE filter ALTER COLUMN id SET DEFAULT nextval('filter_id_seq');

ALTER TABLE utstyrgruppe_id_seq RENAME TO filtergroup_id_seq;
ALTER TABLE filtergroup ALTER COLUMN id SET DEFAULT nextval('filtergroup_id_seq');

ALTER SEQUENCE queue_id_seq RENAME TO accountalertqueue_id_seq;

-- Both old IP Device Center and new IP Device Info does lots of selects on cam
-- with netboxid and ifindex in the where clause
CREATE INDEX cam_netboxid_ifindex_btree ON cam USING btree (netboxid, ifindex);
