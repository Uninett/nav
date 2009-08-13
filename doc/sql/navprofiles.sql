/*
=============================================
        NAVprofiles
    SQL Initialization script

    Run the command:
    psql navprofiles -f navprofiles.sql


	!! WARNING !!
	This SQL script is encoded as unicode (UTF-8),
	before you do changes and commit, be 100% sure
	that your editor do not mess it up.

    Check 1 : These norwegian letters looks nice:
    ! æøåÆØÅ !
    Check 2 : This is the Euro currency sign:
    ! € !
=============================================
*/


/*
------------------------------------------------------
 TABLE DEFINITIONS
------------------------------------------------------
*/

-- FIXME
CREATE SEQUENCE alertsender_id_seq START 1000;
CREATE TABLE alertsender (
	id integer NOT NULL DEFAULT nextval('alertsender_id_seq'),
	name varchar(100) NOT NULL,
	handler varchar(100) NOT NULL,

	CONSTRAINT alertsender_unique_name UNIQUE(name),
	CONSTRAINT alertsender_unique_handler UNIQUE(handler),
	CONSTRAINT alertsender_pkey  PRIMARY KEY(id)
);

/*
-- 1 ACCOUNT

Table for users

login		usally 3-8 characters
name		Real name of user
password	password for local authentication
ext_sync	external syncronization, reserved for future use,
            null means local authentication
*/
CREATE SEQUENCE account_id_seq START 1000;
CREATE TABLE Account (
    id integer NOT NULL DEFAULT nextval('account_id_seq'),
    login varchar NOT NULL,
    name varchar DEFAULT 'Noname',
    password varchar,
    ext_sync varchar,

    CONSTRAINT account_pkey PRIMARY KEY(id),
    CONSTRAINT account_login_key UNIQUE(login)
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE account_id_seq OWNED BY account.id;

-- Trigger that ensures that users are a part of the groups everyone and authenticated users
CREATE OR REPLACE FUNCTION group_membership() RETURNS trigger AS $group_membership$
        BEGIN
                IF NEW.id >= 1000 THEN
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (2, NEW.id);
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (3, NEW.id);
                END IF; RETURN NULL;
        END;
$group_membership$ LANGUAGE plpgsql;

CREATE TRIGGER group_membership AFTER INSERT ON account
        FOR EACH ROW EXECUTE PROCEDURE group_membership();


/*
-- 2 ACCOUNTGROUP

Table for usergroup

name		Name of usergroup
descr		Longer description
*/
CREATE SEQUENCE accountgroup_id_seq START 1000;
CREATE TABLE AccountGroup (
    id integer NOT NULL DEFAULT nextval('accountgroup_id_seq'),
    name varchar DEFAULT 'Noname',
    descr varchar,

    CONSTRAINT accountgroup_pkey PRIMARY KEY(id)
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE accountgroup_id_seq OWNED BY accountgroup.id;


-- 3 ACCOUNTGROUP_ACCOUNTS
CREATE SEQUENCE accountgroup_accounts_id_seq;
CREATE TABLE accountgroup_accounts (
    id integer NOT NULL DEFAULT nextval('accountgroup_accounts_id_seq'),
    account_id integer NOT NULL,
    accountgroup_id integer NOT NULL,

    CONSTRAINT accountgroup_accounts_pkey PRIMARY KEY(id),
    CONSTRAINT accountgroup_accounts_account_id_key UNIQUE(account_id, accountgroup_id),
    CONSTRAINT accountgroup_accounts_account_id_fkey
        FOREIGN KEY(account_id) REFERENCES account(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT accountgroup_accounts_accountgroup_id_fkey
        FOREIGN KEY(accountgroup_id) REFERENCES accountgroup(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE accountgroup_accounts_id_seq OWNED BY accountgroup_accounts.id;

-- ACCOUNTINGROUP
-- View for compability with older code that thinks accountgroup_accounts is
-- still called accountingroup.
CREATE VIEW accountingroup AS (
    SELECT
        accountgroup_accounts.account_id AS accountid,
        accountgroup_accounts.accountgroup_id AS groupid
    FROM
        accountgroup_accounts
);


/*
-- 4 ACCOUNTPROPERTY

A general table related to a single user. An user can have many account properties.
This is a general way that allows applications to add key-value pairs to a user.

In example NAVprofile web frontend use key 'language' to save language preferences for an user.
*/
CREATE SEQUENCE accountproperty_id_seq;
CREATE TABLE AccountProperty (
    id integer NOT NULL DEFAULT nextval('accountproperty_id_seq'),
    accountid integer,
    property varchar,
    value varchar,

    CONSTRAINT accountproperty_pkey PRIMARY KEY(id),
    CONSTRAINT accountproperty_accountid_fkey
        FOREIGN KEY(accountid) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE accountproperty_id_seq OWNED BY accountproperty.id;

/*
-- 5 ALERTADDRESS

Addresses related to a user. A user can have arbitrary many addresses.

type		Specifies what kind of address this is.
                Predefined values:
                    1 e-mail user@domain.com
                    2 sms 99887766
                    3 irc nick!userid@irc.server.com
                    4 icq 123456789
address		The address
*/
CREATE SEQUENCE alertaddress_id_seq START 1000;
CREATE TABLE alertaddress (
       id integer NOT NULL DEFAULT nextval('alertaddress_id_seq'),
       accountid integer NOT NULL,
       type integer NOT NULL,
       address varchar,

       CONSTRAINT alertaddress_pkey PRIMARY KEY(id),
       CONSTRAINT alertaddress_accountid_fkey
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT alertaddress_type_fkey 
                  FOREIGN KEY(type) REFERENCES alertsender(id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE
         
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE alertaddress_id_seq OWNED BY alertaddress.id;


/*
-- 6 ALERTPROFILE

A table for alertprofile. Only one profile can be active simultanously. It is possible that zero profiles are active. One user may have arbitrary many profiles. A profile is a composistion of a set of timeperiods which define a timetable.

name		The name of the profile
daily_dispatch_time		Related to queueing. When daily queueing is selected, this attrubute specify when on a day
            enqueued alerts will be sent.
weekly_dispatch_day		Related to queueing. When weekly queueing is selected, this attribute specify which 
            weekday enqueued alerts will be sent on. 0 is monday, 6 is sunday.
weekly_dispatch_time		Related to queueing. When weekly queueing is selected, this attribute specify which time
            on the day enqueued alerts will be sent.

*/
CREATE SEQUENCE alertprofile_id_seq START 1000;
CREATE TABLE alertprofile (
       id integer NOT NULL DEFAULT nextval('alertprofile_id_seq'),
       accountid integer NOT NULL,
       name varchar,
       daily_dispatch_time time NOT NULL DEFAULT '08:00:00',
       weekly_dispatch_day integer NOT NULL DEFAULT 0,
       weekly_dispatch_time time NOT NULL DEFAULT '08:30:00',

       CONSTRAINT alertprofile_pkey PRIMARY KEY(id),
       CONSTRAINT alertprofile_accountid_fkey
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE alertprofile_id_seq OWNED BY alertprofile.id;


/*
-- 7 ALERTPREFERENCE

admin		an integer specifying wether the user is administrator or not.
            Defined values are (0 disabled, 1 normal user, 100 administrator)

activeprofile	Defines the active profile at the moment. null means no profiles is active.
*/
CREATE TABLE alertpreference (
    accountid integer NOT NULL,
    activeprofile integer,
    lastsentday timestamp,
    lastsentweek timestamp,

    CONSTRAINT alertpreference_pkey PRIMARY KEY(accountid),

    CONSTRAINT alertpreference_accountid_fkey
        FOREIGN KEY(accountid) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT alertpreference_activeprofile_fkey
        FOREIGN KEY(activeprofile) REFERENCES alertprofile(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

/*
-- 8 TIMEPERIOD

A table specifying a time period. This could be though of as an element in a timetable. A time period is related to a set of relation between equipmentgroups and alertaddresses.

start_time	this attribute speficies the start time of this time period. The time period end time is 
            implicit given by the start time by the next time period.

valid_during		Speficies wether this time period is for weekdays or weekend or both.
				1 all week
				2 weekdays Monday-Friday
				3 weekend Saturday-Sunday
*/
CREATE SEQUENCE timeperiod_id_seq START 1000;
CREATE TABLE timeperiod (
       id integer NOT NULL DEFAULT nextval('timeperiod_id_seq'),
       alert_profile_id integer NOT NULL,
       start_time time NOT NULL,
       valid_during integer NOT NULL,

       CONSTRAINT timeperiod_pkey PRIMARY KEY(id),
       CONSTRAINT timeperiod_alert_profile_id_fkey
		  FOREIGN KEY(alert_profile_id) REFERENCES alertprofile(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE timeperiod_id_seq OWNED BY timeperiod.id;

/*
-- 9 FILTERGROUP

Equipment group. An equipment is a composite of equipment filters. Equipment group is specified by a 
ennumerated (by priority) list of equipment filters. An equipment group could either be owned by an user, or shared among administrators.

name	The name of the equipment group
description	Longer description

*/
CREATE SEQUENCE filtergroup_id_seq START 1000;
CREATE TABLE filtergroup (
    id integer NOT NULL DEFAULT nextval('filtergroup_id_seq'),
    owner_id integer,
    name varchar,
    description varchar,

    CONSTRAINT filtergroup_pkey PRIMARY KEY(id),
    CONSTRAINT filtergroup_owner_id_fkey
        FOREIGN KEY(owner_id) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE filtergroup_id_seq OWNED BY filtergroup.id;

/*
-- 10 ALERTSUBSCRIPTION

AlertSubscription is the relation between alert address, time period and equipment group.

subscription_type		an integer specifying the queueing settings on this alert.
                    0 No queue, imediate delivery of alert
                    1 Enqueued (daily), daily delivery of alert digest
                    2 Enqueued (weekly), weekly delivery of alert digest
                    3 Enqueued (profile switch), alert is enqueued, and every time alertengine detects that
                a new time period is entered, this queue will be checked and delivered to the user or another
                queue if it match the new time periods alert settings.
*/
CREATE SEQUENCE alertsubscription_id_seq;
CREATE TABLE alertsubscription (
	id integer NOT NULL DEFAULT nextval('alertsubscription_id_seq'),
	alert_address_id integer NOT NULL,
	time_period_id integer NOT NULL,
	filter_group_id integer NOT NULL,
	subscription_type integer,
	ignore_closed_alerts boolean,

	CONSTRAINT alertsubscription_pkey PRIMARY KEY(id),
	CONSTRAINT alertsubscription_alert_address_id_key
		UNIQUE(alert_address_id, time_period_id, filter_group_id),

	CONSTRAINT alertsubscription_alert_address_id_fkey
		FOREIGN KEY (alert_address_id) REFERENCES alertaddress(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,
	CONSTRAINT alertsubscription_time_period_id_fkey
		FOREIGN KEY(time_period_id) REFERENCES timeperiod(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,
	CONSTRAINT alertsubscriptino_filter_group_id_fkey
		FOREIGN KEY(filter_group_id) REFERENCES filtergroup(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE alertsubscription_id_seq OWNED BY alertsubscription.id;

/*
-- 11 FILTERGROUP_GROUP_PERMISSION

Permissions.

This table contatins a relation from a user group to an equipment group. It gives all members of the 
actual user group permission to set up notofication for alerts matching this filter. The relation 
usergroup <-> equipment group is many to many.
*/
CREATE SEQUENCE filtergroup_group_permission_id_seq;
CREATE TABLE filtergroup_group_permission (
       id integer NOT NULL DEFAULT nextval('filtergroup_group_permission_id_seq'),
       accountgroup_id integer NOT NULL,
       filtergroup_id integer NOT NULL,

       CONSTRAINT filtergroup_group_permission_pkey PRIMARY KEY(id),
       CONSTRAINT filtergroup_group_permission_accountgroup_id_key
       		UNIQUE(accountgroup_id, filtergroup_id),
       CONSTRAINT filtergroup_group_permission_accountgroup_id_fkey
		  FOREIGN KEY(accountgroup_id) REFERENCES accountgroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT filtergroup_group_permission_filtergroup_id_fkey
		  FOREIGN KEY(filtergroup_id) REFERENCES filtergroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE filtergroup_group_permission_id_seq OWNED BY filtergroup_group_permission.id;

/*
-- 14 FILTER

Equipment filter, is a list of matches. An equipment filter will for a given alarm evaluate to either true
or false. For a filter to evaluate as true, all related filter matches has to evaluate to true.

The equipment filter could either be owned by an user, or shared among administrators. When accountid is null, the filter is shared among adminstrators.

name		The name of the equipmentfilter
*/
CREATE SEQUENCE filter_id_seq START 1000;
CREATE TABLE filter (
       id integer NOT NULL DEFAULT nextval('filter_id_seq'),
       owner_id integer,
       name varchar,

       CONSTRAINT filter_pkey PRIMARY KEY(id),
       CONSTRAINT filter_owner_id_fkey
		  FOREIGN KEY(owner_id) REFERENCES Account(id)
		  ON DELETE SET NULL
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE filter_id_seq OWNED BY filter.id;

/*
-- 15 FILTERGROUPCONTENT

This table is an realtion from equipment group to eqipment filter. It is an enumerated relation, which
means that each row has a priority.

include.    If true the related filter is included in the group.
positive.   If this is false, the filter is inverted, which implies that true is false, and
            false is true.
priority.   The list will be traversed in ascending priority order. Which means that the higher 
            number, the higher priority.
*/
CREATE SEQUENCE filtergroupcontent_id_seq;
CREATE TABLE filtergroupcontent (
       id integer NOT NULL DEFAULT nextval('filtergroupcontent_id_seq'),
       include boolean NOT NULL DEFAULT true,
       positive boolean NOT NULL DEFAULT true,
       priority integer NOT NULL,
       filter_id integer NOT NULL,
       filter_group_id integer NOT NULL,

       CONSTRAINT filtergroupcontent_pkey PRIMARY KEY(id),
       CONSTRAINT filtergroupcontent_filter_id_key UNIQUE(filter_id, filter_group_id),
       CONSTRAINT filtergroupcontent_filter_group_id_fkey
		  FOREIGN KEY(filter_group_id) REFERENCES filtergroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT filtergroupcontent_filter_id_fkey
		  FOREIGN KEY(filter_id) REFERENCES filter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE filtergroupcontent_id_seq OWNED BY filtergroupcontent.id;

/*
-- 16 MATCHFIELD

Matchfield, is a relation to the Manage database. Each filtermatch could be related to a single matchfield.

name		The name of the filter
descr		Longer description
value_help	Help text in html about how to choose values.
value_id		Realtion to manage: table.field that defines the id
value_name	Realtion to manage: table.field describing the attribute name
value_sort	Realtion to manage: table.field by which the values will be sorted in the option list.
list_limit	Max number of values shown in the drop down list.
data_type	Defining the datatype, this is a helper attribute for the alertengine.
show_list	boolean, true: show list of values from manage. false: show html input field.
*/
CREATE SEQUENCE matchfield_id_seq START 1000;
CREATE TABLE MatchField (
    id integer NOT NULL DEFAULT nextval('matchfield_id_seq'),
    name varchar,
    description varchar,
    value_help varchar,
    value_id varchar,
    value_name varchar,
    value_sort varchar,
    list_limit integer DEFAULT 300,
    data_type integer NOT NULL DEFAULT 0,
    show_list boolean,

    CONSTRAINT matchfield_pkey PRIMARY KEY(id)
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE matchfield_id_seq OWNED BY matchfield.id;

/*
-- 17 EXPRESSION

Expression is a single condition. It consist of a matchfield, a operator and a value.

match_field_id	This is a relation to matchfield
operator	This specifies the operator used. This a static list.
value		The value
*/
CREATE SEQUENCE expression_id_seq START 1000;
CREATE TABLE expression (
       id integer NOT NULL DEFAULT nextval('expression_id_seq'),
       filter_id integer NOT NULL,
       match_field_id integer NOT NULL,
       operator integer,
       value varchar,

    CONSTRAINT expression_pkey PRIMARY KEY(id),
    CONSTRAINT expression_match_field_id_fkey
        FOREIGN KEY(match_field_id) REFERENCES matchfield(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT expression_filter_id_fkey
        FOREIGN KEY(filter_id) REFERENCES filter(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE expression_id_seq OWNED BY expression.id;


/*
-- 18 OPERATOR

Operator, this is a list related to each matchfield, specifying which operator should be availbale to
choose from, form the given matchfield.

*/
CREATE SEQUENCE operator_id_seq;
CREATE SEQUENCE operator_operator_id_seq;
CREATE TABLE Operator (
    id integer NOT NULL DEFAULT nextval('operator_id_seq'),
    operator_id integer NOT NULL DEFAULT nextval('operator_operator_id_seq'),
    match_field_id integer NOT NULL,

    CONSTRAINT operator_pkey PRIMARY KEY(id),
    CONSTRAINT operator_operator_id_key UNIQUE(operator_id, match_field_id),
    CONSTRAINT operator_match_field_id_fkey
	FOREIGN KEY(match_field_id) REFERENCES matchfield(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE operator_id_seq OWNED BY operator.id;
-- ALTER SEQUENCE operator_operator_id_seq OWNED BY operator.operator_id;

/*
-- 20 SMSQ

SMSQ Description

*/
CREATE TABLE smsq (
    id serial,
    accountid integer,
    time timestamp NOT NULL,
    phone varchar(15) NOT NULL,
    msg varchar(145) NOT NULL,
    sent char(1) NOT NULL DEFAULT 'N'
        CHECK (sent='Y' or sent='N' or sent='I'),
    smsid integer,
    timesent timestamp,
    severity integer,

    CONSTRAINT smsq_pkey PRIMARY KEY(id),
    CONSTRAINT smsq_accountid_fkey
    	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE
);


/*
-- 21 ACCOUNTALERTQUEUE

QUEUE Description

*/
CREATE TABLE accountalertqueue (
    id serial,
    account_id integer,
    alert_id integer,
    subscription_id integer,
    insertion_time timestamp NOT NULL,

    CONSTRAINT accountalertqueue_pkey PRIMARY KEY(id),
    CONSTRAINT accountalertqueue_account_id_fkey
    	FOREIGN KEY(account_id) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE,
    CONSTRAINT accountalertqueue_subscription_id_fkey
	FOREIGN KEY (subscription_id) REFERENCES alertsubscription(id)
	-- ON UPDATE CASCADE -- FIXME is CASCADE right here?
	-- ON DELETE CASCADE -- FIXME
);

/*
-- 20 NAVBARLINK

Table for links in the navigation bar and dropdown menus. Links with
accountid 0 is shared by all.

accountid          owner of the link, id 0 means link is shared by all
name               one or two words describing the link, eg. Network
Explorer
uri                address of the link, eg. /vlanplot/index.html

*/
CREATE SEQUENCE navbarlink_id_seq START 1000;
CREATE TABLE NavbarLink (
    id integer NOT NULL DEFAULT nextval('navbarlink_id_seq'),
    accountid integer NOT NULL DEFAULT 0,
    name varchar,
    uri varchar,

    CONSTRAINT navbarlink_pkey PRIMARY KEY(id),
    CONSTRAINT navbarlink_accountid_fkey
               FOREIGN KEY (accountid) REFERENCES Account(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE navbarlink_id_seq OWNED BY navbarlink.id;

/*
-- 21 ACCOUNTNAVBAR

Relation between account and navbarlinks, describing where the user wants
the link to be.

positions      'navbar', 'qlink1', 'qlink2' or a combination of these.

*/
CREATE TABLE AccountNavbar (
    accountid integer NOT NULL,
    navbarlinkid integer NOT NULL,
    positions varchar,

    CONSTRAINT accountnavbar_pkey PRIMARY KEY (accountid, navbarlinkid),
    CONSTRAINT accountnavbar_accountid_fkey
               FOREIGN KEY (accountid) REFERENCES Account(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
    CONSTRAINT accountnavbar_navbarlinkid_fkey
               FOREIGN KEY (navbarlinkid) REFERENCES NavbarLink(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE
);

/*
-- AccountOrg

This table associates accounts with organizations.  Unfortunately, the
entity describing organizations is contained in the manage database,
so referential integrity must be enforced outside of the database
server.

*/
CREATE SEQUENCE accountorg_id_seq;
CREATE TABLE AccountOrg (
       id integer NOT NULL DEFAULT nextval('accountorg_id_seq'),
       account_id integer NOT NULL,
       organization_id varchar(30) NOT NULL,

       CONSTRAINT accountorg_pkey PRIMARY KEY(id),
       CONSTRAINT accountorg_accountid_key UNIQUE(account_id, organization_id),
       CONSTRAINT accountorg_account_id_fkey
                  FOREIGN KEY(account_id) REFERENCES Account(id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE,
       CONSTRAINT accountorg_organization_id_fkey
                  FOREIGN KEY (organization_id) REFERENCES manage.org(orgid)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE accountorg_id_seq OWNED BY accountorg.id;

/*
-- Privilege

This table contains valid privilege names and their id numbers for
reference from the AccountGroupPrivilege table

*/
CREATE SEQUENCE privilege_id_seq START 10000;
CREATE TABLE Privilege (
       privilegeid integer NOT NULL DEFAULT nextval('privilege_id_seq'),
       privilegename varchar(30) NOT NULL,

       CONSTRAINT privilege_pkey PRIMARY KEY (privilegeid),
       CONSTRAINT privilege_privilegename_key UNIQUE(privilegename)
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE privilege_id_seq OWNED BY privilege.privilegeid;

/*
-- AccountGroupPrivilege

This table defines privileges granted to AccountGroups.

*/
CREATE SEQUENCE accountgroupprivilege_id_seq;
CREATE TABLE AccountGroupPrivilege (
       id integer NOT NULL DEFAULT nextval('accountgroupprivilege_id_seq'),
       accountgroupid integer NOT NULL,
       privilegeid integer NOT NULL,
       target varchar NOT NULL,

       CONSTRAINT accountgroupprivilege_pkey PRIMARY KEY(id),
       CONSTRAINT accountgroupprivilege_accountgroupid_key UNIQUE(accountgroupid, privilegeid, target),
       CONSTRAINT accountgroupprivilege_accountgroupid_fkey
                  FOREIGN KEY(accountgroupid) REFERENCES AccountGroup(id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE,
       CONSTRAINT accountgroupprivilege_privilegeid_fkey
                  FOREIGN KEY(privilegeid) REFERENCES Privilege
                  ON DELETE CASCADE
                  ON UPDATE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE accountgroupprivilege_id_seq OWNED BY accountgroupprivilege.id;

/*
-- PrivilegeByGroup

This is a view that is similar to AccountGroupPrivilege, except that privilege names have been resolved from the privilege id
*/
CREATE VIEW PrivilegeByGroup AS (
       SELECT a.accountgroupid, b.privilegename AS action, a.target
       FROM AccountgroupPrivilege AS a NATURAL JOIN Privilege AS b
);
















/*
------------------------------------------------------
 INSERT INITIAL DATA
------------------------------------------------------
*/


-- Accounts and Accountgroups

INSERT INTO AccountGroup (id, name, descr) VALUES (1, 'NAV Administrators', 'Full access to everything');
INSERT INTO AccountGroup (id, name, descr) VALUES (2, 'Everyone', 'Unauthenticated and authenticated users');
INSERT INTO AccountGroup (id, name, descr) VALUES (3, 'Authenticated users', 'Any authenticated user (logged in)');

-- Some default example groups
INSERT INTO AccountGroup (name, descr) VALUES ('SMS', 'Allowed to receive SMS alerts');

-- Default system accounts
INSERT INTO Account (id, login, name, password) VALUES (0, 'default', 'Default User', '');
INSERT INTO Account (id, login, name, password) VALUES (1, 'admin', 'NAV Administrator', '{sha1}s3F6XX/D$L3vU8Rs2bTJ4zArBLVIPbh7cN9Q=');

INSERT INTO accountgroup_accounts (account_id, accountgroup_id) VALUES (0,2); -- add default to Everyone
INSERT INTO accountgroup_accounts (account_id, accountgroup_id) VALUES (1,1); -- add admin to Administrators
INSERT INTO accountgroup_accounts (account_id, accountgroup_id) VALUES (1,2); -- add admin to Everyone
INSERT INTO accountgroup_accounts (account_id, accountgroup_id) VALUES (1,3); -- add admin to Authenticated users

-- NAVBAR PREFERENCES

INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (1, 0, 'Preferences', '/preferences');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (2, 0, 'Toolbox', '/toolbox');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (3, 0, 'Useradmin', '/useradmin/');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (4, 0, 'Userinfo', '/userinfo/');

INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (1, 1, 'navbar');
INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (1, 2, 'navbar');
INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (1, 3, 'navbar');
INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (1, 4, 'navbar');

INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (0, 1, 'navbar');
INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (0, 2, 'navbar');
INSERT INTO AccountNavbar (accountid, navbarlinkid, positions) VALUES (0, 4, 'navbar');


-- Privileges

-- INSERT INTO Privilege VALUES (1, 'empty_privilege');
INSERT INTO Privilege VALUES (2, 'web_access');
INSERT INTO Privilege VALUES (3, 'alert_by');

/*
  Set some default web_access privileges
*/
-- Anonymous users need access to a few things, like the login page and images
-- and soforth
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/about/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/images/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/js/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/style/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/alertprofiles/wap/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/$');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/toolbox\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/index(.py)?/(index|login|logout|passwd)\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/userinfo/?');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/messages/(active|historic|planned|view|rss)\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/maintenance/(calendar|active|historic|planned|view)\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/geomap$');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, E'^/geomap/open');

-- Define minimum privileges for authenticated users
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (3, 2, '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap)/?');

-- Give alert_by privilege to SMS group
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) 
       VALUES ((SELECT id FROM AccountGroup WHERE name='SMS'), 3, 'sms');

-- Alert senders
INSERT INTO alertsender VALUES (1, 'Email', 'email');
INSERT INTO alertsender VALUES (2, 'SMS', 'sms');
INSERT INTO alertsender VALUES (3, 'Jabber', 'jabber'); 


-- Matchfields
/* 
Matchfield.Datatype
	string:  0
	integer: 1
	ip adr:  2
*/

INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(10, 0, 'Event type', 'eventtype.eventtypeid', 'eventtype.eventtypedesc', 'eventtype.eventtypeid', true, 
'Event type: An event type describes a category of alarms. (Please note that alarm type is a more refined attribute. There are a set of alarm types within an event type.)');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 10);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 10);

INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(11, 0, 'Alert type', 'alerttype.alerttype', 'alerttype.alerttypedesc', 'alerttype.alerttypeid', true, 
'Alert type: An alert type describes the various values an event type may take.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 11);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 11);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description, value_help) VALUES 
(12, 1, 'Severity', 'alertq.severity', null, null, false,
'Severity: Limit your alarms based on severity.',
'Range: Severities are in the range 0-100, where 100 is most severe.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 12);
INSERT INTO Operator (operator_id, match_field_id) VALUES (1, 12);
INSERT INTO Operator (operator_id, match_field_id) VALUES (2, 12);
INSERT INTO Operator (operator_id, match_field_id) VALUES (3, 12);
INSERT INTO Operator (operator_id, match_field_id) VALUES (4, 12);
INSERT INTO Operator (operator_id, match_field_id) VALUES (5, 12);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(13, 0, 'Category', 'cat.catid', 'cat.descr', 'cat.catid', true,
'Category: All equipment is categorized in 7 main categories.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 13);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 13);

INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(14, 0, 'Sub category', 'subcat.subcatid', 'subcat.descr', 'subcat.descr', true,
'Sub category: Within a catogory user-defined subcategories may exist.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 14);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 14);

INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description, value_help) VALUES 
(15, 0, 'Sysname', 'netbox.sysname', null, null, false,
'Sysname: Limit your alarms based on sysname.',
E'Sysname examples:<blockquote>
<b>Starts with:</b> samson.<br>
<b>Ends with:</b> .stud.ntnu.no<br>
<b>Contains:</b> .studby.<br>
<b>Regexp:</b> [sbm][0-2][0-9]{2}[a-z]\\.studby\\.ntnu\\.no</blockquote>');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 15);
INSERT INTO Operator (operator_id, match_field_id) VALUES (5, 15);
INSERT INTO Operator (operator_id, match_field_id) VALUES (6, 15);
INSERT INTO Operator (operator_id, match_field_id) VALUES (7, 15);
INSERT INTO Operator (operator_id, match_field_id) VALUES (8, 15);
INSERT INTO Operator (operator_id, match_field_id) VALUES (9, 15);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description, value_help) VALUES 
(16, 2, 'IP address', 'netbox.ip', null, null, false,
'Limit your alarms based on an IP address/range (prefix)',
'examples:<blockquote>
129.241.190.190<br>
129.241.190.0/24</br>
129.241.0.0/16</blockquote>');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 16);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 16);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(17, 0, 'Room', 'room.roomid', 'room.descr', 'room.roomid', true,
'Room: Limit your alarms based on room.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 17);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 17);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(18, 0, 'Location', 'location.locationid', 'location.descr', 'location.descr', true, 
'Location: Limit your alarms based on location (a location contains a set of rooms) ');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 18);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 18);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(19, 0, 'Organization', 'org.orgid', 'org.descr', 'org.descr', true,
'Organization: Limit your alarms based on the organization ownership of the alarm in question.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 19);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 19);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(20, 0, 'Usage', 'usage.usageid', 'usage.descr', 'usage.descr', true,
'Usage: Different network prefixes are mapped to usage areas.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 20);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 20);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(21, 0, 'Type', 'type.typename', 'type.descr', 'type.descr', true,
'Type: Limit your alarms equipment type');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 21);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 21);


INSERT INTO MatchField (id, data_type, name, value_id, value_name, value_sort, show_list, description) VALUES 
(22, 0, 'Equipment vendor', 'vendor.vendorid', 'vendor.vendorid', 'vendor.vendorid', true,
'Equipment vendor: Limit alert by the vendor of the netbox.');
INSERT INTO Operator (operator_id, match_field_id) VALUES (0, 22);
INSERT INTO Operator (operator_id, match_field_id) VALUES (11, 22);









-- INSERT DEFAULT FILTERS AND FILTER GROUPS

-- Table:filtergroup

INSERT INTO filtergroup (id, owner_id, name, description) VALUES (71, NULL, 'G01: All alerts', 'This filter group matches every alert. The group can i.e. be used to give a group permission to receive all alerts.');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (62, NULL, 'G02: All router alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (63, NULL, 'G03: All switch (core and edge) alerts', '');

INSERT INTO filtergroup (id, owner_id, name, description) VALUES (64, NULL, 'G04: All core switch alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (65, NULL, 'G05: All edge switch alert', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (68, NULL, 'G06: All alerts from wireless boxes', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (69, NULL, 'G07: All alerts from servers', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (70, NULL, 'G08: All alerts from OTHER equipment', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (72, NULL, 'G09: All boxState alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (73, NULL, 'G10: All box up/down alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (74, NULL, 'G11: All box sunny/shadow alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (75, NULL, 'G12: All boxState early warnings', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (76, NULL, 'G13: All module outage alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (77, NULL, 'G14: All services alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (78, NULL, 'G15: All threshold alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (79, NULL, 'G16: All device change alerts', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (81, NULL, 'G17: All alerts with severity >= Warning', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (82, NULL, 'G18: All alerts with severity >= Errors', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (83, NULL, 'G19: All alerts with severity >= Critical', '');
INSERT INTO filtergroup (id, owner_id, name, description) VALUES (84, NULL, 'G20: All alerts with severity = Emergency', '');

-- Table:filter

INSERT INTO filter (id, owner_id, name) VALUES (13, NULL, 'F01: All alerts');
INSERT INTO filter (id, owner_id, name) VALUES (29, NULL, 'F02: All router alerts');
INSERT INTO filter (id, owner_id, name) VALUES (30, NULL, 'F03: All switch (core and edge) alerts');
INSERT INTO filter (id, owner_id, name) VALUES (31, NULL, 'F04: All core switch alerts');
INSERT INTO filter (id, owner_id, name) VALUES (32, NULL, 'F05: All edge switch alerts');
INSERT INTO filter (id, owner_id, name) VALUES (33, NULL, 'F06: All alerts from wireless boxes');
INSERT INTO filter (id, owner_id, name) VALUES (34, NULL, 'F07: All alerts from servers');
INSERT INTO filter (id, owner_id, name) VALUES (35, NULL, 'F08: All alerts from OTHER equipment');
INSERT INTO filter (id, owner_id, name) VALUES (36, NULL, 'F09: All boxState alerts');
INSERT INTO filter (id, owner_id, name) VALUES (14, NULL, 'F10: All box up/down alerts');
INSERT INTO filter (id, owner_id, name) VALUES (15, NULL, 'F11: All box sunny/shadow alerts');
INSERT INTO filter (id, owner_id, name) VALUES (25, NULL, 'F12: All boxState early warnings');
INSERT INTO filter (id, owner_id, name) VALUES (16, NULL, 'F13: All module outage alerts');
INSERT INTO filter (id, owner_id, name) VALUES (26, NULL, 'F14: All services alerts');
INSERT INTO filter (id, owner_id, name) VALUES (27, NULL, 'F15: All threshold alerts');
INSERT INTO filter (id, owner_id, name) VALUES (28, NULL, 'F16: All device change alerts');
INSERT INTO filter (id, owner_id, name) VALUES (20, NULL, 'F17: All alerts with severity >= Warning');
INSERT INTO filter (id, owner_id, name) VALUES (21, NULL, 'F18: All alerts with severity >= Errors');
INSERT INTO filter (id, owner_id, name) VALUES (23, NULL, 'F19: All alerts with severity >= Critical');
INSERT INTO filter (id, owner_id, name) VALUES (24, NULL, 'F20: All alerts with severity = Emergency');




-- Table: filtergroupcontent

INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 29, 62);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 30, 63);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 2, 31, 64);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 32, 65);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 33, 68);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 34, 69);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 13, 71);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 35, 70);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 36, 72);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 14, 73);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 15, 74);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 25, 75);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 16, 76);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 26, 77);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 27, 78);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 28, 79);
--INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 19, 80);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 20, 81);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 21, 82);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 23, 83);
INSERT INTO filtergroupcontent (include, positive, priority, filter_id, filter_group_id) VALUES (true, true, 1, 24, 84);

-- Table: expression

INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (26, 29, 13, 11, 'GSW|GW');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (27, 13, 12, 4, '100');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (25, 30, 13, 11, 'EDGE|GSW|SW');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (28, 31, 13, 11, 'GSW|SW');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (29, 14, 11, 11, 'boxDown|boxUp');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (30, 15, 11, 11, 'boxShadow|boxSunny');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (31, 25, 11, 11, 'boxDownWarning|boxShadowWarning');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (32, 16, 10, 0, 'moduleState');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (43, 32, 13, 0, 'EDGE');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (44, 33, 13, 0, 'WLAN');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (45, 34, 13, 0, 'SRV');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (46, 35, 13, 0, 'OTHER');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (47, 36, 10, 0, 'boxState');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (52, 26, 10, 0, 'serviceState');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (53, 27, 10, 0, 'thresholdState');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (55, 20, 12, 2, '20');
--INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (56, 19, 12, 2, '0');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (57, 21, 12, 2, '40');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (58, 28, 10, 0, 'deviceChanged');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (59, 23, 12, 2, '60');
INSERT INTO expression (id, filter_id, match_field_id, operator, value) VALUES (61, 24, 12, 2, '80');


-- Table: filtergroup_group_permission

INSERT INTO filtergroup_group_permission (accountgroup_id, filtergroup_id) VALUES (1, 71);


/*
------------------------------------------------------
 EOF
------------------------------------------------------
*/
