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
 DELETE OLD TABLES
------------------------------------------------------
*/

-- 1 ACCOUNT
DROP SEQUENCE account_id_seq;
DROP TABLE Account CASCADE;

-- 2 ACCOUNTGROUP
DROP SEQUENCE accountgroup_id_seq;
DROP TABLE AccountGroup CASCADE;

-- 3 ACCOUNTINGROUP
DROP TABLE AccountInGroup CASCADE;

-- 4 ACCOUNTPROPERTY
DROP TABLE AccountProperty CASCADE;

-- 5 ALARMADRESSE
DROP SEQUENCE alarmadresse_id_seq;
DROP TABLE Alarmadresse CASCADE;

-- 6 BRUKERPROFIL
DROP SEQUENCE brukerprofil_id_seq;
DROP TABLE Brukerprofil CASCADE;

-- 7 PREFERENCE
DROP TABLE Preference CASCADE;

-- 8 TIDSPERIODE
DROP SEQUENCE tidsperiode_id_seq;
DROP TABLE Tidsperiode CASCADE;

-- 9 UTSTYRGRUPPE
DROP SEQUENCE utstyrgruppe_id_seq;
DROP TABLE Utstyrgruppe CASCADE;

-- 10 VARSLE
DROP TABLE Varsle CASCADE;

-- 11 RETTIGHET
DROP TABLE Rettighet CASCADE;

-- 12 BRUKERRETTIGHET
DROP TABLE BrukerRettighet CASCADE;

-- 13 DEFAULTUTSTYR
DROP TABLE DefaultUtstyr CASCADE;

-- 23 DEFAULTFILTER
DROP TABLE DefaultFilter CASCADE;


-- 14 UTSTYRFILTER
DROP SEQUENCE utstyrfilter_id_seq;
DROP TABLE Utstyrfilter CASCADE;

-- 15 GRUPPETILFILTER
DROP TABLE GruppeTilFilter CASCADE;

-- 16 MATCHFIELD
DROP SEQUENCE matchfield_id_seq;
DROP TABLE MatchField CASCADE;

-- 17 FILTERMATCH
DROP SEQUENCE filtermatch_id_seq;
DROP TABLE FilterMatch CASCADE;

-- 18 OPERATOR
DROP SEQUENCE operator_id_seq;
DROP TABLE Operator;

-- 19 LOGG
DROP SEQUENCE logg_id_seq;
DROP TABLE Logg CASCADE;

--DROP SEQUENCE smsq_id_seq;
DROP TABLE smsq CASCADE;

--DROP SEQUENCE queue_id_seq;
DROP TABLE queue CASCADE;

-- 22 NAVBARLINK
DROP SEQUENCE navbarlink_id_seq;
DROP TABLE NavbarLink CASCADE;

-- 23 ACCOUNTNAVBAR
DROP TABLE AccountNavbar;


-- AccountOrg
DROP TABLE AccountOrg;


-- Privileges

-- PrivilegeByGroup
DROP VIEW PrivilegeByGroup;

-- AccountGroupPrivilege
DROP TABLE AccountGroupPrivilege CASCADE;

DROP SEQUENCE privilege_id_seq;
DROP TABLE Privilege CASCADE;




/*
------------------------------------------------------
 TABLE DEFINITIONS
------------------------------------------------------
*/

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
    login varchar CONSTRAINT brukernavn_uniq UNIQUE NOT NULL,
    name varchar DEFAULT 'Noname',
    password varchar,
    ext_sync varchar,

    CONSTRAINT account_pk PRIMARY KEY (id)
);
CREATE INDEX account_idx ON Account(login);


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

       CONSTRAINT accountgroup_pk PRIMARY KEY (id)
);


/*
-- 3 ACCOUNTINGROUP

Relation between user and usergroup. A user can be member of arbitrary many usergroups. 

*/
CREATE TABLE AccountInGroup (
       accountid integer NOT NULL,
       groupid integer NOT NULL,
       
       CONSTRAINT accountingroup_pk PRIMARY KEY(accountid, groupid),
       CONSTRAINT account_exist 
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE, 
       CONSTRAINT group_exist 
		  FOREIGN KEY(groupid) REFERENCES Accountgroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

/*
-- 4 ACCOUNTPROPERTY

A general table related to a single user. An user can have many account properties.
This is a general way that allows applications to add key-value pairs to a user.

In example NAVprofile web frontend use key 'language' to save language preferences for an user.
*/
CREATE TABLE AccountProperty (
    accountid integer,
    property varchar,
    value varchar,
    
    CONSTRAINT account_exist 
        FOREIGN KEY(accountid) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE  
);

/*
-- 5 ALARMADRESSE

Addresses related to a user. A user can have arbitrary many addresses.

type		Specifies what kind of address this is.
                Predefined values:
                    1 e-mail user@domain.com
                    2 sms 99887766
                    3 irc nick!userid@irc.server.com
                    4 icq 123456789
adrese		The address
*/
CREATE SEQUENCE alarmadresse_id_seq START 1000;
CREATE TABLE Alarmadresse (
       id integer NOT NULL DEFAULT nextval('alarmadresse_id_seq'),
       accountid integer NOT NULL,
       type integer NOT NULL,
       adresse varchar,

       CONSTRAINT alarmadresse_pk PRIMARY KEY(id),
       CONSTRAINT account_exist 
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


/*
-- 6 BRUKERPROFIL

A table for alertprofile. Only one profile can be active simultanously. It is possible that zero profiles are active. One user may have arbitrary many profiles. A profile is a composistion of a set of timeperiods which define a timetable.

navn		The name of the profile
tid		Related to queueing. When daily queueing is selected, this attrubute specify when on a day
            enqueued alerts will be sent.
ukedag		Related to queueing. When weekly queueing is selected, this attribute specify which 
            weekday enqueued alerts will be sent on. 0 is monday, 6 is sunday.
uketid		Related to queueing. When weekly queueing is selected, this attribute specify which time
            on the day enqueued alerts will be sent.

*/
CREATE SEQUENCE brukerprofil_id_seq START 1000;
CREATE TABLE Brukerprofil (
       id integer NOT NULL DEFAULT nextval('brukerprofil_id_seq'),
       accountid integer NOT NULL,
       navn varchar,
       tid time NOT NULL DEFAULT '08:00:00',
       ukedag integer NOT NULL DEFAULT 0,
       uketid time NOT NULL DEFAULT '08:30:00',

       CONSTRAINT brukerprofil_pk PRIMARY KEY(id),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


/*
-- 7 PREFERENCE

queuelength	Related to queuing. When user select queueing this attributes speficies the highest number of
            days the user is allowed to queue an alert. Alerts that are older will be deleted by the 
            alertengine.
            
admin		an integer specifying wether the user is administrator or not.
            Defined values are (0 disabled, 1 normal user, 100 administrator)
            
activeprofile	Defines the active profile at the moment. null means no profiles is active.

sms		Is the user allowed to get alerts on sms.
*/
CREATE TABLE Preference (
    accountid integer NOT NULL,
    queuelength interval,
/*    admin integer NOT NULL DEFAULT 1,       */
    activeprofile integer,
/*    sms boolean NOT NULL DEFAULT true, */
    
    lastsentday timestamp,
    lastsentweek timestamp,

   CONSTRAINT preference_pk PRIMARY KEY(accountid),

    CONSTRAINT account_Exist
        FOREIGN KEY(accountid) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
                  
    CONSTRAINT brukerprofil_eksisterer
        FOREIGN KEY(activeprofile) REFERENCES Brukerprofil(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Trigger function to copy the preference row of the default user
-- whenever a new account is inserted.  I would like to insert a
-- composite row variable, but couldn't find any way to do so, so this
-- function needs to be updated whenever the schema of the preference
-- table is updated!  We don't attach the trigger until after we
-- insert some default accounts and privileges (further down in this
-- script)
CREATE OR REPLACE FUNCTION copy_default_preferences () RETURNS TRIGGER AS '
  DECLARE
    pref preference%ROWTYPE;
  BEGIN
    SELECT INTO pref * FROM preference WHERE accountid = 0;
    pref.accountid := NEW.id;
    INSERT INTO preference (accountid, queuelength, activeprofile, lastsentday, lastsentweek)
      VALUES (pref.accountid, pref.queuelength, pref.activeprofile, pref.lastsentday, pref.lastsentweek);
    RETURN NEW;
  END' LANGUAGE 'plpgsql';

/*
-- 8 TIDSPERIODE

A table specifying a time period. This could be though of as an element in a timetable. A time period is related to a set of relation between equipmentgroups and alertaddresses.

starttid	this attribute speficies the start time of this time period. The time period end time is 
            implicit given by the start time by the next time period.
            1 all week
            2 weekdays Monday-Friday
            3 weekend Saturday-Sunday
            
helg		Speficies wether this time period is for weekdays or weekend or both.
*/
CREATE SEQUENCE tidsperiode_id_seq START 1000;
CREATE TABLE Tidsperiode (
       id integer NOT NULL DEFAULT nextval('tidsperiode_id_seq'),
       brukerprofilid integer NOT NULL,
       starttid time NOT NULL,
       helg integer NOT NULL,

       CONSTRAINT tidsperiode_pk PRIMARY KEY(id),
       CONSTRAINT brukerprofil_eksisterer
		  FOREIGN KEY(brukerprofilid) REFERENCES Brukerprofil(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

/*
-- 9 UTSTYRGRUPPE

Equipment group. An equipment is a composite of equipment filters. Equipment group is specified by a 
ennumerated (by priority) list of equipment filters. An equipment group could either be owned by an user, or shared among administrators.

navn	The name of the equipment group
descr	Longer description

*/
CREATE SEQUENCE utstyrgruppe_id_seq START 1000;
CREATE TABLE Utstyrgruppe (
    id integer NOT NULL DEFAULT nextval('utstyrgruppe_id_seq'),
    accountid integer,
    navn varchar,
    descr varchar,

    CONSTRAINT utstyrgruppe_pk PRIMARY KEY(id),
       
    CONSTRAINT account_Exist
        FOREIGN KEY(accountid) REFERENCES Account(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE  
);

/*
-- 10 VARSLE

Varsle is the relation between alert address, time period and equipment group.

vent		an integer specifying the queueing settings on this alert.
                    0 No queue, imediate delivery of alert
                    1 Enqueued (daily), daily delivery of alert digest
                    2 Enqueued (weekly), weekly delivery of alert digest
                    3 Enqueued (profile switch), alert is enqueued, and every time alertengine detects that
                a new time period is entered, this queue will be checked and delivered to the user or another
                queue if it match the new time periods alert settings.
*/
CREATE TABLE Varsle (
	alarmadresseid integer NOT NULL,
	tidsperiodeid integer NOT NULL,
	utstyrgruppeid integer NOT NULL,
	vent integer,

	CONSTRAINT varsleadresse_pk PRIMARY KEY(alarmadresseid, tidsperiodeid, utstyrgruppeid),
	CONSTRAINT alarmadresse_eksisterer
		FOREIGN KEY (alarmadresseid) REFERENCES Alarmadresse(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,

	CONSTRAINT tidsperiode_eksisterer
		FOREIGN KEY(tidsperiodeid) REFERENCES Tidsperiode(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,
	CONSTRAINT utstyrgruppe_eksisterer
		FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE  
);

/*
-- 11 RETTIGHET

Permissions.

This table contatins a relation from a user group to an equipment group. It gives all members of the 
actual user group permission to set up notofication for alerts matching this filter. The relation 
usergroup <-> equipment group is many to many.
*/
CREATE TABLE Rettighet (
       accountgroupid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,
       CONSTRAINT rettighet_pk PRIMARY KEY(accountgroupid, utstyrgruppeid),
       CONSTRAINT accountgroup_exist
		  FOREIGN KEY(accountgroupid) REFERENCES accountgroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

/*
-- 12 BRUKERRETTIGHET

This is a permission relation table reserved for future use.

This adds permission from a user to quipmentgroups. In webfrontend, adding permission is still only available per user group. This is a suggested feature to be added later.. [10. juni 2003]

*/
CREATE TABLE BrukerRettighet (
       accountid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,
       
       CONSTRAINT brukerrettighet_pk PRIMARY KEY(accountid, utstyrgruppeid),
       CONSTRAINT account_exist
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

/*
-- 13 DEFAULTUTSTYR

Default equipment is a table adding default quipmentgroups to user groups. Default equipment groups will be avaibale for the user through the webinterface to use for notifications/alerts.

The relation can be only to equipment groups shared by administrators, not to equipment groups owned by someone.
*/
CREATE TABLE DefaultUtstyr (
       accountgroupid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,

       CONSTRAINT defaultutstyr_pk PRIMARY KEY (accountgroupid, utstyrgruppeid),
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT accountgroup_exist
		  FOREIGN KEY(accountgroupid) REFERENCES AccountGroup(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);




/*
-- 14 UTSTYRFILTER

Equipment filter, is a list of matches. An equipment filter will for a given alarm evaluate to either true
or false. For a filter to evaluate as true, all related filter matches has to evaluate to true.

The equipment filter could either be owned by an user, or shared among administrators. When accountid is null, the filter is shared among adminstrators.

navn		The name of the equipmentfilter
*/
CREATE SEQUENCE utstyrfilter_id_seq START 1000;
CREATE TABLE Utstyrfilter (
       id integer NOT NULL DEFAULT nextval('utstyrfilter_id_seq'),
       accountid integer,
       navn varchar,

       CONSTRAINT utstyrfilter_pk PRIMARY KEY(id),
       CONSTRAINT user_Exist
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE SET NULL 
		  ON UPDATE CASCADE
);

/*
-- 15 GRUPPETILFILTER

This table is an realtion from equipment group to eqipment filter. It is an enumerated relation, which
means that each row has a priority.

inkluder	include. If true the related filter is included in the group.
positiv		positive. If this is false, the filter is inverted, which implies that true is false, and
            false is true.
prioritet	priority. The list will be traversed in ascending priority order. Which means that the higher 
            number, the higher priority.
*/
CREATE TABLE GruppeTilFilter (
       inkluder boolean NOT NULL DEFAULT true,
       positiv boolean NOT NULL DEFAULT true,
       prioritet integer NOT NULL,
       utstyrfilterid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,

       CONSTRAINT gruppetilfilter_pk PRIMARY KEY(utstyrfilterid, utstyrgruppeid),
       CONSTRAINT utstyrgruppeid_eksisterer 
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrfilter_eksisterer 
		  FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

/*
-- 16 MATCHFIELD

Matchfield, is a relation to the Manage database. Each filtermatch could be related to a single matchfield.

name		The name of the filter
descr		Longer description
valuehelp	Help text in html about how to choose values.
valueid		Realtion to manage: table.field that defines the id
valuename	Realtion to manage: table.field describing the attribute name
valuecategory	Realtion to manage: table.field that categorize values
valuesort	Realtion to manage: table.field by which the values will be sorted in the option list.
listlimit	Max number of values shown in the drop down list.
datatype	Defining the datatype, this is a helper attribute for the alertengine.
showlist	boolean, true: show list of values from manage. false: show html input field.
*/
CREATE SEQUENCE matchfield_id_seq START 1000;
CREATE TABLE MatchField (
    matchfieldid integer NOT NULL DEFAULT nextval('matchfield_id_seq'),
    name varchar,
    descr varchar,
    valuehelp varchar,
    valueid varchar,
    valuename varchar,
    valuecategory varchar,
    valuesort varchar,
    listlimit integer DEFAULT 300,
    datatype integer NOT NULL DEFAULT 0,
    showlist boolean,
    
    CONSTRAINT matchfield_pk PRIMARY KEY(matchfieldid)
);

/*
-- 17 FILTERMATCH

Filtermatch is a single condition. It consist of a matchfield, a operator and a value.

matchfelt	This is a relation to matchfield
matchtype	This specifies the operator used. This a static list.
                Temporarily this list is used in the webinterface:
                    $type[0] = gettext('er lik');
                    $type[1] = gettext('er større enn');
                    $type[2] = gettext('er større eller lik');
                    $type[3] = gettext('er mindre enn');
                    $type[4] = gettext('er mindre eller lik');
                    $type[5] = gettext('er ulik');
                    $type[6] = gettext('starter med');
                    $type[7] = gettext('slutter med');
                    $type[8] = gettext('inneholder');
                    $type[9] = gettext('regexp');
                    $type[10] = gettext('wildcard (? og *)');
verdi		The value
*/
CREATE SEQUENCE filtermatch_id_seq START 1000;
CREATE TABLE FilterMatch (
       id integer NOT NULL DEFAULT nextval('filtermatch_id_seq'),
       utstyrfilterid integer NOT NULL,
       matchfelt integer NOT NULL,
       matchtype integer,
       verdi varchar,
       
    CONSTRAINT filtermatch_pk PRIMARY KEY(id),
    CONSTRAINT matchfield_Exist 
        FOREIGN KEY(matchfelt) REFERENCES matchfield(matchfieldid)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT utstyrfilter_eksisterer
        FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


/*
-- 18 OPERATOR

Operator, this is a list related to each matchfield, specifying which operator should be availbale to
choose from, form the given matchfield.

*/
CREATE SEQUENCE operator_id_seq START 1000;
CREATE TABLE Operator (
    operatorid integer NOT NULL DEFAULT nextval('operator_id_seq'),
    matchfieldid integer NOT NULL,
    
    CONSTRAINT operator_pk PRIMARY KEY (operatorid, matchfieldid),
    CONSTRAINT matchfield_eksisterer 
	FOREIGN KEY(matchfieldid) REFERENCES MatchField(matchfieldid)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);


/*
-- 19 LOGG

Logg is a table where log events are collected.

type	type of log event.
        Static list:
            1 User logs in
            2 User logs out
            3 New
            4 Delete
            5 Edit
            6 New
            7 Delete
            8 Edit
            9 Profile switch via wap
tid	the time when event took place
descr	a general textstring, could be used to describe the event

*/
CREATE SEQUENCE logg_id_seq START 1000;
CREATE TABLE Logg (
    id integer NOT NULL DEFAULT nextval('logg_id_seq'),
       accountid integer NOT NULL,
       type integer,
       tid timestamptz,       
       descr varchar,
       
       CONSTRAINT loggid_pk PRIMARY KEY(id),     
       
       CONSTRAINT user_exist
		  FOREIGN KEY(accountid) REFERENCES Account(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


/*
-- 20 SMSQ

SMSQ Description

*/
CREATE TABLE smsq (
    id serial primary key, 
    accountid int references
        account(id) on update cascade on delete cascade, 
        
    time timestamp not null,
    phone varchar(15) not null,
    msg varchar(145) not null, 
    sent char(1) not null default 'N' 
        check (sent='Y' or sent='N' or sent='I'), 
    smsid int, 
    timesent timestamp, 
    severity int
);


/*
-- 21 Queue

QUEUE Description

*/
CREATE TABLE queue (
    id serial primary key, 
    accountid int references
        account(id) on update cascade on delete cascade, 
        
    addrid int references
        alarmadresse(id) on update cascade on delete cascade, 
        
    alertid int,
    time timestamp not null    
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

    CONSTRAINT navbarlink_pk PRIMARY KEY (id),
    CONSTRAINT account_exists
               FOREIGN KEY (accountid) REFERENCES Account(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE
);

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

    CONSTRAINT accountnavbar_pk PRIMARY KEY (accountid, navbarlinkid),
    CONSTRAINT account_exists
               FOREIGN KEY (accountid) REFERENCES Account(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
    CONSTRAINT navbarlink_exists
               FOREIGN KEY (navbarlinkid) REFERENCES NavbarLink(id)
               ON DELETE CASCADE
               ON UPDATE CASCADE
);


/*
-- 23 DEFAULTFILTER

Default filter is a table adding default filters to the user groups. Default filters will be avaibale for the user through the webinterface to use for notifications/alerts.

The relation can be only to filters shared by administrators, not to filters owned by someone.
*/
CREATE TABLE DefaultFilter (
       accountgroupid integer NOT NULL,
       utstyrfilterid integer NOT NULL,

       CONSTRAINT defaultfilter_pk PRIMARY KEY (accountgroupid, utstyrfilterid),
       CONSTRAINT utstyrfilter_eksisterer
		  FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT accountgroup_exist
		  FOREIGN KEY(accountgroupid) REFERENCES AccountGroup(id)
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
CREATE TABLE AccountOrg (
       accountid integer NOT NULL,
       orgid varchar(10) NOT NULL,

       CONSTRAINT accountorg_pk
                  PRIMARY KEY (accountid, orgid),
       CONSTRAINT account_exists
                  FOREIGN KEY(accountid) REFERENCES Account(id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE
);

/*
-- Privilege

This table contains valid privilege names and their id numbers for
reference from the AccountGroupPrivilege table

*/
CREATE SEQUENCE privilege_id_seq START 10000;
CREATE TABLE Privilege (
       privilegeid integer NOT NULL DEFAULT nextval('privilege_id_seq'),
       privilegename varchar(30) NOT NULL CONSTRAINT privilegename_uniq UNIQUE,

       CONSTRAINT privilege_pk PRIMARY KEY (privilegeid)
);

/*
-- AccountGroupPrivilege

This table defines privileges granted to AccountGroups.

*/
CREATE TABLE AccountGroupPrivilege (
       accountgroupid integer NOT NULL,
       privilegeid integer NOT NULL,
       target varchar NOT NULL,

       CONSTRAINT agprivilege_pk PRIMARY KEY (accountgroupid, privilegeid, target),
       CONSTRAINT accountgroup_exists
                  FOREIGN KEY(accountgroupid) REFERENCES AccountGroup(id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE,
       CONSTRAINT privilege_exists
                  FOREIGN KEY(privilegeid) REFERENCES Privilege
                  ON DELETE CASCADE
                  ON UPDATE CASCADE
);

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
INSERT INTO AccountGroup (id, name, descr) VALUES (2, 'Anonymous users', 'Unauthenticated users (not logged in)');

-- Some default example groups
INSERT INTO AccountGroup (name, descr) VALUES ('ReadAll', 'Read access to most things');
INSERT INTO AccountGroup (name, descr) VALUES ('SMS', 'Allowed to receive SMS alerts');

-- Default system accounts
INSERT INTO Account (id, login, name, password) VALUES (0, 'default', 'Default User', '');
INSERT INTO Account (id, login, name, password) VALUES (1, 'admin', 'NAV Administrator', 'admin');

INSERT INTO AccountInGroup (accountid, groupid) VALUES (1, 1);

INSERT INTO Preference (accountid, queuelength) VALUES (1, '14 days');
INSERT INTO Preference (accountid, queuelength) VALUES (0, '14 days');

-- Default preference rows are now inserted, so we create the trigger
-- on the account table
CREATE TRIGGER insert_account AFTER INSERT ON account FOR EACH ROW EXECUTE PROCEDURE copy_default_preferences();

-- NAVBAR PREFERENCES

INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (1, 0, 'Preferences', '/preferences');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (2, 0, 'Toolbox', '/toolbox');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (3, 0, 'Useradmin', '/useradmin/index');
INSERT INTO NavbarLink (id, accountid, name, uri) VALUES (4, 0, 'Userinfo', '/index/userinfo');

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
-- Anonymous users need access to a few things, like the login page and images and soforth
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/images/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/alertprofiles/wap/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/$');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/toolbox\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/index(.py)?/(index|login|logout|userinfo|passwd)\\b');

-- Give read access to most informational tools for ReadAll group
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) 
       VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 2, '^/(report|status|emotd|alertprofiles|machinetracker|browse|preferences|cricket)/?');

-- Give alert_by privilege to SMS group
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) 
       VALUES ((SELECT id FROM AccountGroup WHERE name='SMS'), 3, 'sms');


-- Matchfields
/* 
Matchfield.Datatype
	string:  0
	integer: 1
	ip adr:  2
*/

INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(10, 0, 'Event type', 'eventtype.eventtypeid', 'eventtype.eventtypedesc|[ID]: [NAME]', null, 'eventtype.eventtypeid', true, 
'Event type: An event type describes a category of alarms. (Please note that alarm type is a more refined attribute. There are a set of alarm types within an event type.)');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 10);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 10);

INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(11, 0, 'Alert type', 'alerttype.alerttype', 'alerttype.alerttypedesc|[ID]: [NAME]', 'alerttype.eventtypeid', 'alerttype.alerttypeid', true, 
'Alert type: An alert type describes the various values an event type may take.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 11);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 11);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr,valuehelp) VALUES 
(12, 1, 'Severity', 'alertq.severity', null, null, null, false, 
'Severity: Limit your alarms based on severity.',
'Range: Severities are in the range 0-100, where 100 is most severe.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 12);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (1, 12);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (2, 12);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (3, 12);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (4, 12);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (5, 12);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(13, 0, 'Category', 'cat.catid', 'cat.descr|[ID]: [NAME]', null, 'cat.catid', true, 
'Category: All equipment is categorized in 7 main categories.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 13);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 13);

INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(14, 0, 'Sub category', 'subcat.subcatid', 'subcat.descr|[ID]: [NAME]', 'subcat.catid', 'subcat.descr', true, 
'Sub category: Within a catogory user-defined subcategories may exist.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 14);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 14);

INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr, valuehelp) VALUES 
(15, 0, 'Sysname', 'netbox.netboxid', null, null, null, false, 
'Sysname: Limit your alarms based on sysname.',
'Sysname examples:<blockquote>
<b>Starts with:</b> samson.<br>
<b>Ends with:</b> .stud.ntnu.no<br>
<b>Contains:</b> .studby.<br>
<b>Regexp:</b> [sbm][0-2][0-9]{2}[a-z]\\.studby\\.ntnu\\.no</blockquote>');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 15);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (5, 15);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (6, 15);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (7, 15);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (8, 15);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (9, 15);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr, valuehelp) VALUES 
(16, 2, 'IP address', 'netbox.ip', null, null, null, false,
'Limit your alarms based on an IP address/range (prefix)',
'examples:<blockquote>
129.241.190.190<br>
129.241.190.0/24</br>
129.241.0.0/16</blockquote>');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 16);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 16);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(17, 0, 'Room', 'room.roomid', 'room.descr|[ID]: [NAME]', 'room.locationid', 'room.roomid', true, 
'Room: Limit your alarms based on room.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 17);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 17);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(18, 0, 'Location', 'location.locationid', 'location.descr|[NAME] ([ID])', null, 'location.descr', true, 
'Location: Limit your alarms based on location (a location contains a set of rooms) ');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 18);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 18);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(19, 0, 'Organization', 'org.orgid', 'org.descr|[NAME] ([ID])', null, 'org.descr', true, 
'Organization: Limit your alarms based on the organization ownership of the alarm in question.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 19);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 19);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(20, 0, 'Usage', 'usage.usageid', 'usage.descr', null, 'usage.descr', true, 
'Usage: Different network prefixes are mapped to usage areas.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 20);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 20);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(21, 0, 'Type', 'type.typename', 'type.descr', 'type.vendorid', 'type.descr', true, 
'Type: Limit your alarms equipment type');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 21);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 21);


INSERT INTO MatchField (matchfieldid, datatype, name, valueid, valuename, valuecategory, valuesort, showlist, descr) VALUES 
(22, 0, 'Equipment vendor', 'vendor.vendorid', 'vendor.vendorid', null, 'vendor.vendorid', true,
'Equipment vendor: Limit alert by the vendor of the netbox.');
INSERT INTO Operator (operatorid, matchfieldid) VALUES (0, 22);
INSERT INTO Operator (operatorid, matchfieldid) VALUES (11, 22);









-- INSERT DEFAULT FILTERS AND FILTER GROUPS

-- Table:Utstyrgruppe

INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (62, NULL, 'Category_10: All routers', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (63, NULL, 'Category_20: All switches', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (64, NULL, 'Category_30: All core switches', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (65, NULL, 'Category_40: All edge switches', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (68, NULL, 'Category_50: All wireless equipment', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (69, NULL, 'Category_60: All servers', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (70, NULL, 'Category_70: All other equipment', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (71, NULL, 'All alarms', 'This filter group matches every alert. The group can i.e. be used to give a group permission to receive all alerts.');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (72, NULL, 'Event_10: Box: All boxState alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (73, NULL, 'Event_11: Box: up/down alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (74, NULL, 'Event_13: Box: shadow/sunny alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (75, NULL, 'Event_15: Box: early warning alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (76, NULL, 'Event_20: Module alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (77, NULL, 'Event_30: Services alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (78, NULL, 'Event_50: Threshold alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (79, NULL, 'Event_60: Device change alerts', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (80, NULL, 'Severity_20: All severities (incl info)', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (81, NULL, 'Severity_40: Warnings and above', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (82, NULL, 'Severity_60: Errors and above', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (83, NULL, 'Severity_80: Critical and emergency', '');
INSERT INTO utstyrgruppe (id, accountid, navn, descr) VALUES (84, NULL, 'Severity_99: Emergency only', '');

-- Table:Utstyrfilter

INSERT INTO utstyrfilter (id, accountid, navn) VALUES (13, NULL, 'All alarms');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (14, NULL, 'Event_11: Box: up/down alerts');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (15, NULL, 'Event_13: Box: sunny/shadow alerts');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (16, NULL, 'Event_20: Module outage');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (19, NULL, 'Severity_20: All severities (incl info)');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (20, NULL, 'Severity_40: Warning and above');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (21, NULL, 'Severity_60: Errors and above');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (23, NULL, 'Severity_80: Critical and emergency');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (24, NULL, 'Severity_99: Emergency only');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (25, NULL, 'Event_15: Box: early warnings');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (26, NULL, 'Event_30: Services up/down');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (27, NULL, 'Event_50: Threshold alerts');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (28, NULL, 'Event_60: Device changes');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (29, NULL, 'Cat_10: All routers');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (30, NULL, 'Cat_20: All switches');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (31, NULL, 'Cat_30: Core switches');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (32, NULL, 'Cat_40: Edge switches');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (33, NULL, 'Cat_50: Wireless');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (34, NULL, 'Cat_60: Servers');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (35, NULL, 'Cat_70: Other equipment');
INSERT INTO utstyrfilter (id, accountid, navn) VALUES (36, NULL, 'Event_10: Box: all alerts');



-- Table: gruppetilfilter

INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 29, 62);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 30, 63);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 2, 31, 64);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 32, 65);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 33, 68);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 34, 69);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 13, 71);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 35, 70);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 36, 72);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 14, 73);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 15, 74);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 25, 75);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 16, 76);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 26, 77);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 27, 78);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 28, 79);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 19, 80);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 20, 81);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 21, 82);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 23, 83);
INSERT INTO gruppetilfilter (inkluder, positiv, prioritet, utstyrfilterid, utstyrgruppeid) VALUES (true, true, 1, 24, 84);

-- Table: filtermatch

INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (26, 29, 13, 11, 'GSW|GW');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (27, 13, 12, 4, '100');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (25, 30, 13, 11, 'EDGE|GSW|SW');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (28, 31, 13, 11, 'GSW|SW');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (29, 14, 11, 11, 'boxDown|boxUp');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (30, 15, 11, 11, 'boxShadow|boxSunny');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (31, 25, 11, 11, 'boxDownWarning|boxShadowWarning');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (32, 16, 10, 0, 'moduleState');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (43, 32, 13, 0, 'EDGE');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (44, 33, 13, 0, 'WLAN');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (45, 34, 13, 0, 'SRV');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (46, 35, 13, 0, 'OTHER');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (47, 36, 10, 0, 'boxState');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (52, 26, 10, 0, 'serviceState');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (53, 27, 10, 0, 'thresholdState');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (55, 20, 12, 2, '20');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (56, 19, 12, 2, '0');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (57, 21, 12, 2, '40');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (58, 28, 10, 0, 'deviceChanged');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (59, 23, 12, 2, '60');
INSERT INTO filtermatch (id, utstyrfilterid, matchfelt, matchtype, verdi) VALUES (61, 24, 12, 2, '80');


-- Table: Rettighet

INSERT INTO rettighet (accountgroupid, utstyrgruppeid) VALUES (1, 71);
INSERT INTO rettighet (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 71);


-- Table: defaultutstyr

INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES (1, 71);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 71);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 62);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 63);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 64);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 65);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 68);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 69);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 70);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 72);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 73);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 74);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 75);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 76);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 77);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 78);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 79);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 80);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 81);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 82);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 83);
INSERT INTO defaultutstyr (accountgroupid, utstyrgruppeid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 84);


-- Table: defaultfilter

INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES (1, 13);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 13);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 29);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 30);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 31);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 32);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 33);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 34);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 35);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 36);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 14);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 15);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 25);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 16);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 26);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 27);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 28);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 19);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 20);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 21);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 23);
INSERT INTO defaultfilter (accountgroupid, utstyrfilterid) VALUES ((SELECT id FROM AccountGroup WHERE name='ReadAll'), 24);









/*
------------------------------------------------------
 GRANT PERMISSIONS
------------------------------------------------------
*/

CREATE OR REPLACE FUNCTION nav_grant(TEXT, BOOL) RETURNS INTEGER AS '
  DECLARE
    tables_rec   RECORD;
    counter      INTEGER;
    user_name    ALIAS FOR $1;
    write_access ALIAS FOR $2;
    use_priv     TEXT := ''SELECT'';
  BEGIN
    counter := 0;
    IF write_access THEN
      use_priv := ''ALL'';
    END IF;

    FOR tables_rec IN SELECT * FROM pg_tables WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.tablename)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    FOR tables_rec IN SELECT * FROM pg_views WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.viewname)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    FOR tables_rec IN SELECT * FROM pg_statio_all_sequences WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.relname)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    RETURN counter;
  END;
' LANGUAGE 'plpgsql';


SELECT nav_grant('navread', false);
SELECT nav_grant('navwrite', true);

/*
------------------------------------------------------
 EOF
------------------------------------------------------
*/
