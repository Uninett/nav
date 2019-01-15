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
ALTER SEQUENCE alertsender_id_seq OWNED BY alertsender.id;

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
    preferences manage.hstore DEFAULT manage.hstore(''),

    CONSTRAINT account_pkey PRIMARY KEY(id),
    CONSTRAINT account_login_key UNIQUE(login)
);
ALTER SEQUENCE account_id_seq OWNED BY account.id;

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
ALTER SEQUENCE accountgroup_id_seq OWNED BY accountgroup.id;


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
ALTER SEQUENCE accountgroup_accounts_id_seq OWNED BY accountgroup_accounts.id;

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
ALTER SEQUENCE accountproperty_id_seq OWNED BY accountproperty.id;

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
ALTER SEQUENCE alertaddress_id_seq OWNED BY alertaddress.id;


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
ALTER SEQUENCE alertprofile_id_seq OWNED BY alertprofile.id;


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
ALTER SEQUENCE timeperiod_id_seq OWNED BY timeperiod.id;

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
ALTER SEQUENCE filtergroup_id_seq OWNED BY filtergroup.id;

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
	ignore_resolved_alerts boolean,

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
	CONSTRAINT alertsubscription_filter_group_id_fkey
		FOREIGN KEY(filter_group_id) REFERENCES filtergroup(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE
);
ALTER SEQUENCE alertsubscription_id_seq OWNED BY alertsubscription.id;

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
ALTER SEQUENCE filtergroup_group_permission_id_seq OWNED BY filtergroup_group_permission.id;

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
ALTER SEQUENCE filter_id_seq OWNED BY filter.id;

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
ALTER SEQUENCE filtergroupcontent_id_seq OWNED BY filtergroupcontent.id;

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
    list_limit integer DEFAULT 1000,
    data_type integer NOT NULL DEFAULT 0,
    show_list boolean,

    CONSTRAINT matchfield_pkey PRIMARY KEY(id)
);
ALTER SEQUENCE matchfield_id_seq OWNED BY matchfield.id;

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
ALTER SEQUENCE expression_id_seq OWNED BY expression.id;


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
ALTER SEQUENCE operator_id_seq OWNED BY operator.id;
ALTER SEQUENCE operator_operator_id_seq OWNED BY operator.operator_id;

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

    CONSTRAINT accountalertqueue_alert_id_fkey
        FOREIGN KEY(alert_id) REFERENCES manage.alertq(alertqid)
	ON DELETE CASCADE
	ON UPDATE CASCADE,
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
ALTER SEQUENCE navbarlink_id_seq OWNED BY navbarlink.id;

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
ALTER SEQUENCE accountorg_id_seq OWNED BY accountorg.id;

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
ALTER SEQUENCE privilege_id_seq OWNED BY privilege.privilegeid;

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
ALTER SEQUENCE accountgroupprivilege_id_seq OWNED BY accountgroupprivilege.id;

/*
-- PrivilegeByGroup

This is a view that is similar to AccountGroupPrivilege, except that privilege names have been resolved from the privilege id
*/
CREATE VIEW PrivilegeByGroup AS (
       SELECT a.accountgroupid, b.privilegename AS action, a.target
       FROM AccountgroupPrivilege AS a NATURAL JOIN Privilege AS b
);


/*
-- statuspref

Stores preferences for the status tool.
*/
CREATE SEQUENCE statuspreference_id_seq START 1000;
CREATE TABLE statuspreference (
	id integer NOT NULL DEFAULT nextval('statuspreference_id_seq'),
	name varchar NOT NULL,
	position integer NOT NULL,
	type varchar NOT NULL,
	accountid integer NOT NULL,

	services varchar NOT NULL DEFAULT '',
	states varchar NOT NULL DEFAULT 'n,s',

	CONSTRAINT statuspreference_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_accountid_fkey
		FOREIGN KEY (accountid) REFERENCES Account(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
ALTER SEQUENCE statuspreference_id_seq OWNED BY statuspreference.id;

CREATE SEQUENCE statuspreference_organization_id_seq;
CREATE TABLE statuspreference_organization (
	id integer NOT NULL DEFAULT nextval('statuspreference_organization_id_seq'),
	statuspreference_id integer NOT NULL,
	organization_id varchar NOT NULL,

	CONSTRAINT statuspreference_organization_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_organization_statuspreference_id_key
		UNIQUE(statuspreference_id, organization_id),
	CONSTRAINT statuspreference_organization_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_organization_organization_id_fkey
		FOREIGN KEY (organization_id) REFERENCES manage.org(orgid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
ALTER SEQUENCE statuspreference_organization_id_seq OWNED BY statuspreference_organization.id;

CREATE SEQUENCE statuspreference_category_id_seq;
CREATE TABLE statuspreference_category (
	id integer NOT NULL DEFAULT nextval('statuspreference_category_id_seq'),
	statuspreference_id integer NOT NULL,
	category_id varchar NOT NULL,

	CONSTRAINT statuspreference_category_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_category_statuspreference_id_key
		UNIQUE(statuspreference_id, category_id),
	CONSTRAINT statuspreference_category_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_category_category_id_fkey
		FOREIGN KEY (category_id) REFERENCES manage.cat(catid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
ALTER SEQUENCE statuspreference_category_id_seq OWNED BY statuspreference_category.id;














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
-- Grant web access to unauthorized ajax requests
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/ajax/open/?');
-- Grant web access to osm map redirects
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/search/osm_map_redirect/?');
-- Give everyone access to navlets
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/navlets/.*');


-- Define minimum privileges for authenticated users
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (3, 2, '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap|info|netmap|graphite|search|index/dashboard)/?');


-- Give alert_by privilege to SMS group
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
       VALUES ((SELECT id FROM AccountGroup WHERE name='SMS'), 3, 'sms');

-- Alert senders
INSERT INTO alertsender VALUES (1, 'Email', 'email');
INSERT INTO alertsender VALUES (2, 'SMS', 'sms');
INSERT INTO alertsender VALUES (3, 'Jabber', 'jabber');
INSERT INTO alertsender VALUES (4, 'Slack', 'slack');


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
(11, 0, 'Alert type', 'alerttype.alerttype', 'alerttype.alerttypedesc', 'alerttype.alerttype', true,
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
(14, 0, 'Group', 'netboxgroup.netboxgroupid', 'netboxgroup.descr', 'netboxgroup.descr', true,
'Group: netboxes may belong to a group that is independent of type and category');
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


-- StatusPreferences for Default user

INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (1, 'IP devices down', 1, 'netbox', 0, 'n');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (2, 'IP devices in shadow', 2, 'netbox', 0, 's');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (3, 'IP devices on maintenance', 3, 'netbox_maintenance', 0, 'y,n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (4, 'Modules down/in shadow', 4, 'module', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (5, 'Services down', 5, 'service', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (6, 'Thresholds exceeded', 6, 'threshold', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (7, 'SNMP agents down', 7, 'snmpagent', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (8, 'Links down', 8, 'linkstate', 0);


-- netmap_view
CREATE TABLE profiles.netmap_view (
  viewid SERIAL,
  owner INT4 NOT NULL REFERENCES account ON UPDATE CASCADE ON DELETE CASCADE,
  title VARCHAR NOT NULL,
  zoom VARCHAR NOT NULL,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  last_modified TIMESTAMP NOT NULL DEFAULT NOW(),
  topology INT4 NOT NULL,
  display_elinks BOOLEAN NOT NULL DEFAULT false,
  display_orphans BOOLEAN NOT NULL DEFAULT false,
  description TEXT DEFAULT null,
  location_room_filter varchar NOT NULL DEFAULT '',

  PRIMARY KEY (viewid)
);
COMMENT ON TABLE netmap_view IS 'Stored views with settings for NetMap';

CREATE TABLE profiles.netmap_view_categories (
  id SERIAL,
  viewid INT4 CONSTRAINT netmapview_fkey REFERENCES netmap_view ON UPDATE CASCADE ON DELETE CASCADE,
  catid VARCHAR(8) CONSTRAINT netmapview_category_fkey REFERENCES manage.cat ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY (viewid, catid)
);

CREATE TABLE profiles.netmap_view_nodeposition (
  id SERIAL,
  viewid INT4 NOT NULL REFERENCES netmap_view ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES manage.netbox ON UPDATE CASCADE ON DELETE CASCADE,
  x INT4 NOT NULL,
  y INT4 NOT NULL,
  PRIMARY KEY (viewid, netboxid)
);

-- netmap_view_defaultview
CREATE TABLE profiles.netmap_view_defaultview (
  id SERIAL,
  viewid INT4 NOT NULL REFERENCES netmap_view ON UPDATE CASCADE ON DELETE CASCADE,
  ownerid INT4 NOT NULL REFERENCES account ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY (viewid, ownerid)
);
COMMENT ON TABLE netmap_view_defaultview IS 'Stores default views for users in Netmap';

CREATE TABLE profiles.accounttool(
  account_tool_id SERIAL PRIMARY KEY,
  toolname VARCHAR,
  accountid INTEGER NOT NULL,
  display BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 0,

  FOREIGN KEY (accountid) REFERENCES account(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Django database-backed sessions are now being used by NAV.
CREATE TABLE profiles.django_session (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" timestamp with time zone NOT NULL
);

--- Create table for storing multiple dashboards
CREATE TABLE profiles.account_dashboard (
  id SERIAL PRIMARY KEY,
  name VARCHAR DEFAULT 'My dashboard',
  is_default BOOLEAN DEFAULT FALSE,
  num_columns INT,
  account_id INT REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Create table for storing navlet information for a user

CREATE TABLE IF NOT EXISTS profiles.account_navlet (
  id SERIAL PRIMARY KEY,
  dashboard_id INT REFERENCES account_dashboard(id) ON UPDATE CASCADE ON DELETE CASCADE,
  navlet VARCHAR NOT NULL,
  account INT,
  col INT,
  displayorder INT NOT NULL,
  preferences VARCHAR,

  CONSTRAINT account_navlet_account_fkey
    FOREIGN KEY (account) REFERENCES account(id)
    ON DELETE CASCADE ON UPDATE CASCADE
);


---
-- Insert default widgets for every existing user
---
CREATE OR REPLACE FUNCTION insert_default_navlets_for_existing_users() RETURNS void AS $$
DECLARE
  account RECORD;
BEGIN
  FOR account IN SELECT * FROM account LOOP
    RAISE NOTICE 'Adding default navlets for %s', quote_ident(account.login);
    INSERT INTO account_navlet (navlet, account, displayorder, col, preferences) VALUES
      ('nav.web.navlets.gettingstarted.GettingStartedWidget', account.id, 0, 1, NULL),
      ('nav.web.navlets.status2.Status2Widget', account.id, 1, 1, '{"status_filter": "event_type=boxState&stateless_threshold=24", "refresh_interval": 60000}'),
      ('nav.web.navlets.messages.MessagesNavlet', account.id, 2, 1, NULL),
      ('nav.web.navlets.navblog.NavBlogNavlet', account.id, 0, 2, NULL),
      ('nav.web.navlets.linklist.LinkListNavlet', account.id, 1, 2, NULL);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

SELECT insert_default_navlets_for_existing_users();

---
-- Remove GettingStartedWidget for default user.
---
DELETE FROM account_navlet WHERE account=0 AND navlet='nav.web.navlets.gettingstarted.GettingStartedWidget';


--- Create a dashboard for each user and move all widgets there
DO $$DECLARE thisaccount RECORD;
BEGIN
  FOR thisaccount IN SELECT * FROM account LOOP
    RAISE NOTICE 'Creating dashboard for %s', quote_ident(thisaccount.login);
    WITH inserted AS (
      INSERT INTO account_dashboard (account_id, is_default, num_columns)
      VALUES (thisaccount.id, TRUE, 3) RETURNING id
    )
    UPDATE account_navlet
      SET dashboard_id=inserted.id
      FROM inserted
      WHERE account=thisaccount.id;
  END LOOP;
END$$;

--
-- Function and trigger to ensure the default account's dashboard setup is
-- copied to every new account that is created
--

-- Create a new dashboard and copy all the widgets from the default user to
-- the dashboard
CREATE OR REPLACE FUNCTION create_new_dashboard() RETURNS trigger AS $$
  BEGIN
    WITH inserted AS (
      INSERT INTO account_dashboard (account_id, is_default, num_columns)
      VALUES (NEW.id, TRUE, 3) RETURNING id
    )
    INSERT INTO account_navlet (account, navlet, displayorder, col, preferences, dashboard_id)
      SELECT NEW.id, navlet, displayorder, col, preferences, (SELECT id from inserted)
        FROM account_navlet WHERE account=0;

    RETURN NULL;
  END
$$ LANGUAGE plpgsql;


-- Creates a dashboard with default widgets for a new user
CREATE TRIGGER add_default_dashboard_on_account_create AFTER INSERT ON account
  FOR EACH ROW
  EXECUTE PROCEDURE create_new_dashboard();


/*
------------------------------------------------------
 EOF
------------------------------------------------------
*/
