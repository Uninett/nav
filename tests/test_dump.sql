-- navpgdump invoked on ef8511c551f5 at 2015-05-06 11:44:51.845184
-- pgcmd: ['pg_dump', '--no-privileges', '--disable-triggers']
--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: arnold; Type: SCHEMA; Schema: -; Owner: nav
--

CREATE SCHEMA arnold;


ALTER SCHEMA arnold OWNER TO nav;

--
-- Name: logger; Type: SCHEMA; Schema: -; Owner: nav
--

CREATE SCHEMA logger;


ALTER SCHEMA logger OWNER TO nav;

--
-- Name: manage; Type: SCHEMA; Schema: -; Owner: nav
--

CREATE SCHEMA manage;


ALTER SCHEMA manage OWNER TO nav;

--
-- Name: profiles; Type: SCHEMA; Schema: -; Owner: nav
--

CREATE SCHEMA profiles;


ALTER SCHEMA profiles OWNER TO nav;

--
-- Name: radius; Type: SCHEMA; Schema: -; Owner: nav
--

CREATE SCHEMA radius;


ALTER SCHEMA radius OWNER TO nav;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: hstore; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS hstore WITH SCHEMA manage;


--
-- Name: EXTENSION hstore; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION hstore IS 'data type for storing sets of (key, value) pairs';


SET search_path = manage, pg_catalog;

--
-- Name: close_snmpagentstates_on_community_clear(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION close_snmpagentstates_on_community_clear() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF COALESCE(OLD.ro, '') IS DISTINCT FROM COALESCE(NEW.ro, '')
           AND COALESCE(NEW.ro, '') = '' THEN
            UPDATE alerthist
            SET end_time=NOW()
            WHERE netboxid=NEW.netboxid
              AND eventtypeid='snmpAgentState'
              AND end_time >= 'infinity';
        END IF;
        RETURN NULL;
    END;
    $$;


ALTER FUNCTION manage.close_snmpagentstates_on_community_clear() OWNER TO nav;

--
-- Name: close_thresholdstate_on_threshold_delete(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION close_thresholdstate_on_threshold_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
  BEGIN
    IF TG_OP = 'DELETE' THEN
      UPDATE alerthist
        SET end_time = NOW()
          WHERE subid = CAST(OLD.rrd_datasourceid AS text)
            AND eventtypeid = 'thresholdState'
              AND end_time >= 'infinity';
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF COALESCE(OLD.threshold, '') IS 
            DISTINCT FROM COALESCE(NEW.threshold, '')
                AND COALESCE(NEW.threshold, '') = '' THEN
            UPDATE alerthist
                SET end_time = NOW()
                    WHERE subid = CAST(NEW.rrd_datasourceid AS text)
                        AND eventtypeid = 'thresholdState'
                            AND end_time >= 'infinity';
        END IF;
    END IF;
    RETURN NULL;
  END;
  $$;


ALTER FUNCTION manage.close_thresholdstate_on_threshold_delete() OWNER TO nav;

--
-- Name: close_thresholdstate_on_thresholdrule_delete(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION close_thresholdstate_on_thresholdrule_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
  BEGIN
    IF TG_OP = 'DELETE'
      OR (TG_OP = 'UPDATE' AND
          (OLD.alert <> NEW.alert OR OLD.target <> NEW.target))
    THEN
      UPDATE alerthist
      SET end_time = NOW()
      WHERE subid LIKE (CAST(OLD.id AS text) || ':%')
            AND eventtypeid = 'thresholdState'
            AND end_time >= 'infinity';
    END IF;
    RETURN NULL;
  END;
$$;


ALTER FUNCTION manage.close_thresholdstate_on_thresholdrule_delete() OWNER TO nav;

--
-- Name: drop_constraint(character varying, character varying, character varying); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION drop_constraint(tbl_schema character varying, tbl_name character varying, const_name character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    exec_string TEXT;
BEGIN
    exec_string := 'ALTER TABLE ';
    IF tbl_schema != NULL THEN
        exec_string := exec_string || quote_ident(tbl_schema) || '.';
    END IF;
    exec_string := exec_string || quote_ident(tb_name)
        || ' DROP CONSTRAINT '
        || quote_ident(const_name);
    EXECUTE exec_string;
EXCEPTION
    WHEN OTHERS THEN
        NULL;
END;
$$;


ALTER FUNCTION manage.drop_constraint(tbl_schema character varying, tbl_name character varying, const_name character varying) OWNER TO nav;

--
-- Name: insert_default_navlets_for_existing_users(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION insert_default_navlets_for_existing_users() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  account RECORD;
BEGIN
  FOR account IN SELECT * FROM account LOOP
    RAISE NOTICE 'Adding default navlets for %s', quote_ident(account.login);
    INSERT INTO account_navlet (navlet, account, displayorder, col) VALUES
      ('nav.web.navlets.gettingstarted.GettingStartedWidget', account.id, 0, 1),
      ('nav.web.navlets.status.StatusNavlet', account.id, 1, 1),
      ('nav.web.navlets.messages.MessagesNavlet', account.id, 2, 1),
      ('nav.web.navlets.navblog.NavBlogNavlet', account.id, 0, 2),
      ('nav.web.navlets.linklist.LinkListNavlet', account.id, 1, 2);
  END LOOP;
END;
$$;


ALTER FUNCTION manage.insert_default_navlets_for_existing_users() OWNER TO nav;

--
-- Name: insert_default_navlets_for_new_users(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION insert_default_navlets_for_new_users() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
      INSERT INTO account_navlet (account, navlet, displayorder, col, preferences)
        SELECT NEW.id, navlet, displayorder, col, preferences FROM account_navlet WHERE account=0;
      INSERT INTO account_navlet (account, navlet, displayorder, col) VALUES
        (NEW.id, 'nav.web.navlets.gettingstarted.GettingStartedWidget', -1, 1);
      RETURN NULL;
    END
$$;


ALTER FUNCTION manage.insert_default_navlets_for_new_users() OWNER TO nav;

--
-- Name: message_replace(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION message_replace() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    DECLARE
        -- Old replaced_by value of the message beeing replaced
        old_replaced_by INTEGER;
    BEGIN
        -- Remove references that are no longer correct
        IF TG_OP = 'UPDATE' THEN
            IF OLD.replaces_message <> NEW.replaces_message OR
                (OLD.replaces_message IS NOT NULL AND NEW.replaces_message IS NULL) THEN
                EXECUTE 'UPDATE message SET replaced_by = NULL WHERE messageid = '
                || quote_literal(OLD.replaces_message);
            END IF;
        END IF;

        -- It does not replace any message, exit
        IF NEW.replaces_message IS NULL THEN
            RETURN NEW;
        END IF;

        -- Update the replaced_by field of the replaced message with a
        -- reference to the replacer
        SELECT INTO old_replaced_by replaced_by FROM message
            WHERE messageid = NEW.replaces_message;
        IF old_replaced_by <> NEW.messageid OR old_replaced_by IS NULL THEN
            EXECUTE 'UPDATE message SET replaced_by = '
            || quote_literal(NEW.messageid)
            || ' WHERE messageid = '
            || quote_literal(NEW.replaces_message);
        END IF;

        RETURN NEW;
        END;
    $$;


ALTER FUNCTION manage.message_replace() OWNER TO nav;

--
-- Name: never_use_null_subid(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION never_use_null_subid() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
  BEGIN
    NEW.subid = COALESCE(NEW.subid, '');
    RETURN NEW;
  END;
$$;


ALTER FUNCTION manage.never_use_null_subid() OWNER TO nav;

--
-- Name: remove_floating_devices(); Type: FUNCTION; Schema: manage; Owner: nav
--

CREATE FUNCTION remove_floating_devices() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        DELETE FROM device WHERE
            deviceid NOT IN (SELECT deviceid FROM netbox) AND
            deviceid NOT IN (SELECT deviceid FROM module) AND
            serial IS NULL;
        RETURN NULL;
        END;
    $$;


ALTER FUNCTION manage.remove_floating_devices() OWNER TO nav;

SET search_path = profiles, pg_catalog;

--
-- Name: group_membership(); Type: FUNCTION; Schema: profiles; Owner: nav
--

CREATE FUNCTION group_membership() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
                IF NEW.id >= 1000 THEN
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (2, NEW.id);
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (3, NEW.id);
                END IF; RETURN NULL;
        END;
$$;


ALTER FUNCTION profiles.group_membership() OWNER TO nav;

SET search_path = arnold, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: block; Type: TABLE; Schema: arnold; Owner: nav; Tablespace: 
--

CREATE TABLE block (
    blockid integer NOT NULL,
    blocktitle character varying NOT NULL,
    blockdesc character varying,
    mailfile character varying,
    reasonid integer,
    determined character(1),
    incremental character(1),
    blocktime integer NOT NULL,
    active character(1),
    lastedited timestamp without time zone NOT NULL,
    lastedituser character varying NOT NULL,
    inputfile character varying,
    activeonvlans character varying,
    detainmenttype character varying,
    quarantineid integer,
    CONSTRAINT block_active_check CHECK (((active = 'y'::bpchar) OR (active = 'n'::bpchar))),
    CONSTRAINT block_detainmenttype_check CHECK ((((detainmenttype)::text = 'disable'::text) OR ((detainmenttype)::text = 'quarantine'::text)))
);


ALTER TABLE arnold.block OWNER TO nav;

--
-- Name: block_blockid_seq; Type: SEQUENCE; Schema: arnold; Owner: nav
--

CREATE SEQUENCE block_blockid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arnold.block_blockid_seq OWNER TO nav;

--
-- Name: block_blockid_seq; Type: SEQUENCE OWNED BY; Schema: arnold; Owner: nav
--

ALTER SEQUENCE block_blockid_seq OWNED BY block.blockid;


--
-- Name: blocked_reason; Type: TABLE; Schema: arnold; Owner: nav; Tablespace: 
--

CREATE TABLE blocked_reason (
    blocked_reasonid integer NOT NULL,
    name character varying,
    comment character varying
);


ALTER TABLE arnold.blocked_reason OWNER TO nav;

--
-- Name: blocked_reason_blocked_reasonid_seq; Type: SEQUENCE; Schema: arnold; Owner: nav
--

CREATE SEQUENCE blocked_reason_blocked_reasonid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arnold.blocked_reason_blocked_reasonid_seq OWNER TO nav;

--
-- Name: blocked_reason_blocked_reasonid_seq; Type: SEQUENCE OWNED BY; Schema: arnold; Owner: nav
--

ALTER SEQUENCE blocked_reason_blocked_reasonid_seq OWNED BY blocked_reason.blocked_reasonid;


--
-- Name: event; Type: TABLE; Schema: arnold; Owner: nav; Tablespace: 
--

CREATE TABLE event (
    eventid integer NOT NULL,
    identityid integer,
    event_comment character varying,
    blocked_status character varying,
    blocked_reasonid integer,
    eventtime timestamp without time zone NOT NULL,
    autoenablestep integer,
    username character varying NOT NULL,
    CONSTRAINT event_blocked_status_check CHECK (((((blocked_status)::text = 'enabled'::text) OR ((blocked_status)::text = 'disabled'::text)) OR ((blocked_status)::text = 'quarantined'::text)))
);


ALTER TABLE arnold.event OWNER TO nav;

--
-- Name: event_eventid_seq; Type: SEQUENCE; Schema: arnold; Owner: nav
--

CREATE SEQUENCE event_eventid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arnold.event_eventid_seq OWNER TO nav;

--
-- Name: event_eventid_seq; Type: SEQUENCE OWNED BY; Schema: arnold; Owner: nav
--

ALTER SEQUENCE event_eventid_seq OWNED BY event.eventid;


--
-- Name: identity; Type: TABLE; Schema: arnold; Owner: nav; Tablespace: 
--

CREATE TABLE identity (
    identityid integer NOT NULL,
    mac macaddr NOT NULL,
    blocked_status character varying,
    blocked_reasonid integer,
    swportid integer NOT NULL,
    ip inet,
    dns character varying,
    netbios character varying,
    starttime timestamp without time zone NOT NULL,
    lastchanged timestamp without time zone NOT NULL,
    autoenable timestamp without time zone,
    autoenablestep integer,
    mail character varying,
    orgid character varying,
    determined character(1),
    fromvlan integer,
    tovlan integer,
    textual_interface character varying DEFAULT ''::character varying,
    CONSTRAINT identity_blocked_status_check CHECK (((((blocked_status)::text = 'enabled'::text) OR ((blocked_status)::text = 'disabled'::text)) OR ((blocked_status)::text = 'quarantined'::text)))
);


ALTER TABLE arnold.identity OWNER TO nav;

--
-- Name: identity_identityid_seq; Type: SEQUENCE; Schema: arnold; Owner: nav
--

CREATE SEQUENCE identity_identityid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arnold.identity_identityid_seq OWNER TO nav;

--
-- Name: identity_identityid_seq; Type: SEQUENCE OWNED BY; Schema: arnold; Owner: nav
--

ALTER SEQUENCE identity_identityid_seq OWNED BY identity.identityid;


--
-- Name: quarantine_vlans; Type: TABLE; Schema: arnold; Owner: nav; Tablespace: 
--

CREATE TABLE quarantine_vlans (
    quarantineid integer NOT NULL,
    vlan integer,
    description character varying
);


ALTER TABLE arnold.quarantine_vlans OWNER TO nav;

--
-- Name: quarantine_vlans_quarantineid_seq; Type: SEQUENCE; Schema: arnold; Owner: nav
--

CREATE SEQUENCE quarantine_vlans_quarantineid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arnold.quarantine_vlans_quarantineid_seq OWNER TO nav;

--
-- Name: quarantine_vlans_quarantineid_seq; Type: SEQUENCE OWNED BY; Schema: arnold; Owner: nav
--

ALTER SEQUENCE quarantine_vlans_quarantineid_seq OWNED BY quarantine_vlans.quarantineid;


SET search_path = logger, pg_catalog;

--
-- Name: category; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE category (
    category character varying NOT NULL
);


ALTER TABLE logger.category OWNER TO nav;

--
-- Name: errorerror; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE errorerror (
    id integer NOT NULL,
    message character varying
);


ALTER TABLE logger.errorerror OWNER TO nav;

--
-- Name: errorerror_id_seq; Type: SEQUENCE; Schema: logger; Owner: nav
--

CREATE SEQUENCE errorerror_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE logger.errorerror_id_seq OWNER TO nav;

--
-- Name: errorerror_id_seq; Type: SEQUENCE OWNED BY; Schema: logger; Owner: nav
--

ALTER SEQUENCE errorerror_id_seq OWNED BY errorerror.id;


--
-- Name: log_message; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE log_message (
    id integer NOT NULL,
    "time" timestamp without time zone NOT NULL,
    origin integer NOT NULL,
    newpriority integer,
    type integer NOT NULL,
    message character varying
);


ALTER TABLE logger.log_message OWNER TO nav;

--
-- Name: log_message_id_seq; Type: SEQUENCE; Schema: logger; Owner: nav
--

CREATE SEQUENCE log_message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE logger.log_message_id_seq OWNER TO nav;

--
-- Name: log_message_id_seq; Type: SEQUENCE OWNED BY; Schema: logger; Owner: nav
--

ALTER SEQUENCE log_message_id_seq OWNED BY log_message.id;


--
-- Name: log_message_type; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE log_message_type (
    type integer NOT NULL,
    priority integer,
    facility character varying NOT NULL,
    mnemonic character varying NOT NULL
);


ALTER TABLE logger.log_message_type OWNER TO nav;

--
-- Name: log_message_type_type_seq; Type: SEQUENCE; Schema: logger; Owner: nav
--

CREATE SEQUENCE log_message_type_type_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE logger.log_message_type_type_seq OWNER TO nav;

--
-- Name: log_message_type_type_seq; Type: SEQUENCE OWNED BY; Schema: logger; Owner: nav
--

ALTER SEQUENCE log_message_type_type_seq OWNED BY log_message_type.type;


--
-- Name: origin; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE origin (
    origin integer NOT NULL,
    name character varying NOT NULL,
    category character varying
);


ALTER TABLE logger.origin OWNER TO nav;

--
-- Name: message_view; Type: VIEW; Schema: logger; Owner: nav
--

CREATE VIEW message_view AS
    SELECT origin.origin, log_message.type, log_message.newpriority, origin.category, log_message."time" FROM (origin JOIN log_message USING (origin));


ALTER TABLE logger.message_view OWNER TO nav;

--
-- Name: origin_origin_seq; Type: SEQUENCE; Schema: logger; Owner: nav
--

CREATE SEQUENCE origin_origin_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE logger.origin_origin_seq OWNER TO nav;

--
-- Name: origin_origin_seq; Type: SEQUENCE OWNED BY; Schema: logger; Owner: nav
--

ALTER SEQUENCE origin_origin_seq OWNED BY origin.origin;


--
-- Name: priority; Type: TABLE; Schema: logger; Owner: nav; Tablespace: 
--

CREATE TABLE priority (
    priority integer NOT NULL,
    keyword character varying NOT NULL,
    description character varying
);


ALTER TABLE logger.priority OWNER TO nav;

SET search_path = manage, pg_catalog;

--
-- Name: adjacency_candidate; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE adjacency_candidate (
    adjacency_candidateid integer NOT NULL,
    netboxid integer NOT NULL,
    interfaceid integer NOT NULL,
    to_netboxid integer NOT NULL,
    to_interfaceid integer,
    source character varying NOT NULL,
    misscnt integer DEFAULT 0 NOT NULL
);


ALTER TABLE manage.adjacency_candidate OWNER TO nav;

--
-- Name: adjacency_candidate_adjacency_candidateid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE adjacency_candidate_adjacency_candidateid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.adjacency_candidate_adjacency_candidateid_seq OWNER TO nav;

--
-- Name: adjacency_candidate_adjacency_candidateid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE adjacency_candidate_adjacency_candidateid_seq OWNED BY adjacency_candidate.adjacency_candidateid;


--
-- Name: alerthist; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alerthist (
    alerthistid integer NOT NULL,
    source character varying(32) NOT NULL,
    deviceid integer,
    netboxid integer,
    subid character varying DEFAULT ''::character varying NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone DEFAULT 'infinity'::timestamp without time zone,
    eventtypeid character varying(32) NOT NULL,
    alerttypeid integer,
    value integer NOT NULL,
    severity integer NOT NULL
);


ALTER TABLE manage.alerthist OWNER TO nav;

--
-- Name: alerthist_ack; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alerthist_ack (
    alert_id integer NOT NULL,
    account_id integer NOT NULL,
    comment character varying,
    date timestamp with time zone DEFAULT now()
);


ALTER TABLE manage.alerthist_ack OWNER TO nav;

--
-- Name: alerthist_alerthistid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alerthist_alerthistid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alerthist_alerthistid_seq OWNER TO nav;

--
-- Name: alerthist_alerthistid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alerthist_alerthistid_seq OWNED BY alerthist.alerthistid;


--
-- Name: alerthistmsg; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alerthistmsg (
    id integer NOT NULL,
    alerthistid integer,
    state character(1) NOT NULL,
    msgtype character varying NOT NULL,
    language character varying NOT NULL,
    msg text NOT NULL
);


ALTER TABLE manage.alerthistmsg OWNER TO nav;

--
-- Name: alerthistmsg_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alerthistmsg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alerthistmsg_id_seq OWNER TO nav;

--
-- Name: alerthistmsg_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alerthistmsg_id_seq OWNED BY alerthistmsg.id;


--
-- Name: alerthistvar; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alerthistvar (
    id integer NOT NULL,
    alerthistid integer,
    state character(1) NOT NULL,
    var character varying NOT NULL,
    val text NOT NULL
);


ALTER TABLE manage.alerthistvar OWNER TO nav;

--
-- Name: alerthistvar_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alerthistvar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alerthistvar_id_seq OWNER TO nav;

--
-- Name: alerthistvar_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alerthistvar_id_seq OWNED BY alerthistvar.id;


--
-- Name: alertq; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alertq (
    alertqid integer NOT NULL,
    source character varying(32) NOT NULL,
    deviceid integer,
    netboxid integer,
    subid character varying DEFAULT ''::character varying NOT NULL,
    "time" timestamp without time zone NOT NULL,
    eventtypeid character varying(32),
    alerttypeid integer,
    state character(1) NOT NULL,
    value integer NOT NULL,
    severity integer NOT NULL,
    alerthistid integer
);


ALTER TABLE manage.alertq OWNER TO nav;

--
-- Name: alertq_alertqid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alertq_alertqid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alertq_alertqid_seq OWNER TO nav;

--
-- Name: alertq_alertqid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alertq_alertqid_seq OWNED BY alertq.alertqid;


--
-- Name: alertqmsg; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alertqmsg (
    id integer NOT NULL,
    alertqid integer,
    msgtype character varying NOT NULL,
    language character varying NOT NULL,
    msg text NOT NULL
);


ALTER TABLE manage.alertqmsg OWNER TO nav;

--
-- Name: alertqmsg_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alertqmsg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alertqmsg_id_seq OWNER TO nav;

--
-- Name: alertqmsg_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alertqmsg_id_seq OWNED BY alertqmsg.id;


--
-- Name: alertqvar; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alertqvar (
    id integer NOT NULL,
    alertqid integer,
    var character varying NOT NULL,
    val text NOT NULL
);


ALTER TABLE manage.alertqvar OWNER TO nav;

--
-- Name: alertqvar_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alertqvar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alertqvar_id_seq OWNER TO nav;

--
-- Name: alertqvar_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alertqvar_id_seq OWNED BY alertqvar.id;


--
-- Name: alerttype; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE alerttype (
    alerttypeid integer NOT NULL,
    eventtypeid character varying(32) NOT NULL,
    alerttype character varying,
    alerttypedesc character varying
);


ALTER TABLE manage.alerttype OWNER TO nav;

--
-- Name: alerttype_alerttypeid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE alerttype_alerttypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.alerttype_alerttypeid_seq OWNER TO nav;

--
-- Name: alerttype_alerttypeid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE alerttype_alerttypeid_seq OWNED BY alerttype.alerttypeid;


--
-- Name: swportallowedvlan; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE swportallowedvlan (
    interfaceid integer NOT NULL,
    hexstring character varying
);


ALTER TABLE manage.swportallowedvlan OWNER TO nav;

--
-- Name: allowedvlan; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW allowedvlan AS
    SELECT allowed_octets.interfaceid, vlan.vlan AS allowedvlan FROM ((SELECT swportallowedvlan.interfaceid, decode((swportallowedvlan.hexstring)::text, 'hex'::text) AS octetstring FROM swportallowedvlan) allowed_octets CROSS JOIN generate_series(0, 4095) vlan(vlan)) WHERE ((vlan.vlan < (length(allowed_octets.octetstring) * 8)) AND (CASE WHEN (length(allowed_octets.octetstring) >= 128) THEN get_bit(allowed_octets.octetstring, ((((vlan.vlan / 8) * 8) + 7) - (vlan.vlan % 8))) ELSE get_bit(allowed_octets.octetstring, (((((((length(allowed_octets.octetstring) * 8) - vlan.vlan) + 7) >> 3) << 3) - 8) + (vlan.vlan % 8))) END = 1));


ALTER TABLE manage.allowedvlan OWNER TO nav;

--
-- Name: interface; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE interface (
    interfaceid integer NOT NULL,
    netboxid integer NOT NULL,
    moduleid integer,
    ifindex integer,
    ifname character varying,
    ifdescr character varying,
    iftype integer,
    speed double precision,
    ifphysaddress macaddr,
    ifadminstatus integer,
    ifoperstatus integer,
    iflastchange integer,
    ifconnectorpresent boolean,
    ifpromiscuousmode boolean,
    ifalias character varying,
    baseport integer,
    media character varying,
    vlan integer,
    trunk boolean,
    duplex character(1),
    to_netboxid integer,
    to_interfaceid integer,
    gone_since timestamp without time zone,
    CONSTRAINT interface_duplex_check CHECK (((duplex = 'f'::bpchar) OR (duplex = 'h'::bpchar)))
);


ALTER TABLE manage.interface OWNER TO nav;

--
-- Name: allowedvlan_both; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW allowedvlan_both AS
    (SELECT allowedvlan.interfaceid, allowedvlan.interfaceid AS interfaceid2, allowedvlan.allowedvlan FROM allowedvlan ORDER BY allowedvlan.allowedvlan) UNION (SELECT interface.interfaceid, interface.to_interfaceid AS interfaceid2, allowedvlan.allowedvlan FROM (interface JOIN allowedvlan ON ((interface.to_interfaceid = allowedvlan.interfaceid))) ORDER BY allowedvlan.allowedvlan);


ALTER TABLE manage.allowedvlan_both OWNER TO nav;

--
-- Name: apitoken; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE apitoken (
    id integer NOT NULL,
    token character varying NOT NULL,
    expires timestamp without time zone NOT NULL,
    client integer,
    scope integer DEFAULT 0
);


ALTER TABLE manage.apitoken OWNER TO nav;

--
-- Name: apitoken_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE apitoken_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.apitoken_id_seq OWNER TO nav;

--
-- Name: apitoken_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE apitoken_id_seq OWNED BY apitoken.id;


--
-- Name: arp; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE arp (
    arpid integer NOT NULL,
    netboxid integer,
    prefixid integer,
    sysname character varying NOT NULL,
    ip inet NOT NULL,
    mac macaddr NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone DEFAULT 'infinity'::timestamp without time zone NOT NULL
);


ALTER TABLE manage.arp OWNER TO nav;

--
-- Name: arp_arpid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE arp_arpid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.arp_arpid_seq OWNER TO nav;

--
-- Name: arp_arpid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE arp_arpid_seq OWNED BY arp.arpid;


--
-- Name: cabling; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE cabling (
    cablingid integer NOT NULL,
    roomid character varying(30) NOT NULL,
    jack character varying NOT NULL,
    building character varying NOT NULL,
    targetroom character varying NOT NULL,
    descr character varying,
    category character varying NOT NULL
);


ALTER TABLE manage.cabling OWNER TO nav;

--
-- Name: cabling_cablingid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE cabling_cablingid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.cabling_cablingid_seq OWNER TO nav;

--
-- Name: cabling_cablingid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE cabling_cablingid_seq OWNED BY cabling.cablingid;


--
-- Name: cam; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE cam (
    camid integer NOT NULL,
    netboxid integer,
    sysname character varying NOT NULL,
    ifindex integer NOT NULL,
    module character varying(4),
    port character varying,
    mac macaddr NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone DEFAULT 'infinity'::timestamp without time zone NOT NULL,
    misscnt integer DEFAULT 0
);


ALTER TABLE manage.cam OWNER TO nav;

--
-- Name: cam_camid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE cam_camid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.cam_camid_seq OWNER TO nav;

--
-- Name: cam_camid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE cam_camid_seq OWNED BY cam.camid;


--
-- Name: cat; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE cat (
    catid character varying(8) NOT NULL,
    descr character varying,
    req_snmp boolean NOT NULL
);


ALTER TABLE manage.cat OWNER TO nav;

--
-- Name: device; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE device (
    deviceid integer NOT NULL,
    serial character varying,
    hw_ver character varying,
    fw_ver character varying,
    sw_ver character varying,
    discovered timestamp without time zone DEFAULT now()
);


ALTER TABLE manage.device OWNER TO nav;

--
-- Name: device_deviceid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE device_deviceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.device_deviceid_seq OWNER TO nav;

--
-- Name: device_deviceid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE device_deviceid_seq OWNED BY device.deviceid;


--
-- Name: eventq; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE eventq (
    eventqid integer NOT NULL,
    source character varying(32) NOT NULL,
    target character varying(32) NOT NULL,
    deviceid integer,
    netboxid integer,
    subid character varying DEFAULT ''::character varying NOT NULL,
    "time" timestamp without time zone DEFAULT now() NOT NULL,
    eventtypeid character varying(32) NOT NULL,
    state character(1) DEFAULT 'x'::bpchar NOT NULL,
    value integer DEFAULT 100 NOT NULL,
    severity integer DEFAULT 50 NOT NULL,
    CONSTRAINT eventq_state_check CHECK ((((state = 'x'::bpchar) OR (state = 's'::bpchar)) OR (state = 'e'::bpchar)))
);


ALTER TABLE manage.eventq OWNER TO nav;

--
-- Name: eventq_eventqid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE eventq_eventqid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.eventq_eventqid_seq OWNER TO nav;

--
-- Name: eventq_eventqid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE eventq_eventqid_seq OWNED BY eventq.eventqid;


--
-- Name: eventqvar; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE eventqvar (
    id integer NOT NULL,
    eventqid integer,
    var character varying NOT NULL,
    val text NOT NULL
);


ALTER TABLE manage.eventqvar OWNER TO nav;

--
-- Name: eventqvar_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE eventqvar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.eventqvar_id_seq OWNER TO nav;

--
-- Name: eventqvar_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE eventqvar_id_seq OWNED BY eventqvar.id;


--
-- Name: eventtype; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE eventtype (
    eventtypeid character varying(32) NOT NULL,
    eventtypedesc character varying,
    stateful character(1) NOT NULL,
    CONSTRAINT eventtype_stateful_check CHECK (((stateful = 'y'::bpchar) OR (stateful = 'n'::bpchar)))
);


ALTER TABLE manage.eventtype OWNER TO nav;

--
-- Name: gwportprefix; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE gwportprefix (
    interfaceid integer NOT NULL,
    prefixid integer NOT NULL,
    gwip inet NOT NULL,
    virtual boolean DEFAULT false NOT NULL
);


ALTER TABLE manage.gwportprefix OWNER TO nav;

--
-- Name: rproto_attr; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE rproto_attr (
    id integer NOT NULL,
    interfaceid integer NOT NULL,
    protoname character varying NOT NULL,
    metric integer
);


ALTER TABLE manage.rproto_attr OWNER TO nav;

--
-- Name: gwport; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW gwport AS
    SELECT i.interfaceid AS gwportid, i.moduleid, i.ifindex, CASE i.ifadminstatus WHEN 1 THEN CASE i.ifoperstatus WHEN 1 THEN 'y'::character(1) ELSE 'n'::character(1) END ELSE 'd'::character(1) END AS link, NULL::integer AS masterindex, i.ifdescr AS interface, i.speed, ra.metric, i.ifalias AS portname, i.to_netboxid, i.to_interfaceid AS to_swportid FROM ((interface i JOIN gwportprefix gwpfx ON ((i.interfaceid = gwpfx.interfaceid))) LEFT JOIN rproto_attr ra ON (((i.interfaceid = ra.interfaceid) AND ((ra.protoname)::text = 'ospf'::text))));


ALTER TABLE manage.gwport OWNER TO nav;

--
-- Name: iana_iftype; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE iana_iftype (
    iftype integer NOT NULL,
    name character varying NOT NULL,
    descr character varying
);


ALTER TABLE manage.iana_iftype OWNER TO nav;

--
-- Name: image; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE image (
    imageid integer NOT NULL,
    roomid character varying NOT NULL,
    title character varying NOT NULL,
    path character varying NOT NULL,
    name character varying NOT NULL,
    created timestamp without time zone NOT NULL,
    uploader integer,
    priority integer
);


ALTER TABLE manage.image OWNER TO nav;

--
-- Name: image_imageid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE image_imageid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.image_imageid_seq OWNER TO nav;

--
-- Name: image_imageid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE image_imageid_seq OWNED BY image.imageid;


--
-- Name: interface_gwport; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW interface_gwport AS
    SELECT interface.interfaceid, interface.netboxid, interface.moduleid, interface.ifindex, interface.ifname, interface.ifdescr, interface.iftype, interface.speed, interface.ifphysaddress, interface.ifadminstatus, interface.ifoperstatus, interface.iflastchange, interface.ifconnectorpresent, interface.ifpromiscuousmode, interface.ifalias, interface.baseport, interface.media, interface.vlan, interface.trunk, interface.duplex, interface.to_netboxid, interface.to_interfaceid, interface.gone_since, CASE interface.ifadminstatus WHEN 1 THEN CASE interface.ifoperstatus WHEN 1 THEN 'y'::character(1) ELSE 'n'::character(1) END ELSE 'd'::character(1) END AS link FROM (interface JOIN (SELECT gwportprefix.interfaceid FROM gwportprefix GROUP BY gwportprefix.interfaceid) routerports USING (interfaceid));


ALTER TABLE manage.interface_gwport OWNER TO nav;

--
-- Name: interface_interfaceid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE interface_interfaceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.interface_interfaceid_seq OWNER TO nav;

--
-- Name: interface_interfaceid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE interface_interfaceid_seq OWNED BY interface.interfaceid;


--
-- Name: interface_stack; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE interface_stack (
    id integer NOT NULL,
    higher integer,
    lower integer
);


ALTER TABLE manage.interface_stack OWNER TO nav;

--
-- Name: interface_stack_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE interface_stack_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.interface_stack_id_seq OWNER TO nav;

--
-- Name: interface_stack_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE interface_stack_id_seq OWNED BY interface_stack.id;


--
-- Name: interface_swport; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW interface_swport AS
    SELECT interface.interfaceid, interface.netboxid, interface.moduleid, interface.ifindex, interface.ifname, interface.ifdescr, interface.iftype, interface.speed, interface.ifphysaddress, interface.ifadminstatus, interface.ifoperstatus, interface.iflastchange, interface.ifconnectorpresent, interface.ifpromiscuousmode, interface.ifalias, interface.baseport, interface.media, interface.vlan, interface.trunk, interface.duplex, interface.to_netboxid, interface.to_interfaceid, interface.gone_since, CASE interface.ifadminstatus WHEN 1 THEN CASE interface.ifoperstatus WHEN 1 THEN 'y'::character(1) ELSE 'n'::character(1) END ELSE 'd'::character(1) END AS link FROM interface WHERE (interface.baseport IS NOT NULL);


ALTER TABLE manage.interface_swport OWNER TO nav;

--
-- Name: ipdevpoll_job_log; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE ipdevpoll_job_log (
    id bigint NOT NULL,
    netboxid integer NOT NULL,
    job_name character varying NOT NULL,
    end_time timestamp without time zone NOT NULL,
    duration double precision,
    success boolean,
    "interval" integer
);


ALTER TABLE manage.ipdevpoll_job_log OWNER TO nav;

--
-- Name: ipdevpoll_job_log_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE ipdevpoll_job_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.ipdevpoll_job_log_id_seq OWNER TO nav;

--
-- Name: ipdevpoll_job_log_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE ipdevpoll_job_log_id_seq OWNED BY ipdevpoll_job_log.id;


--
-- Name: live_clients; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW live_clients AS
    SELECT arp.ip, arp.mac FROM arp WHERE (arp.end_time = 'infinity'::timestamp without time zone);


ALTER TABLE manage.live_clients OWNER TO nav;

--
-- Name: location; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE location (
    locationid character varying(30) NOT NULL,
    descr character varying NOT NULL,
    data hstore DEFAULT ''::hstore NOT NULL
);


ALTER TABLE manage.location OWNER TO nav;

--
-- Name: macwatch; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE macwatch (
    id integer NOT NULL,
    mac macaddr NOT NULL,
    userid integer,
    description character varying,
    created timestamp without time zone DEFAULT now(),
    prefix_length integer
);


ALTER TABLE manage.macwatch OWNER TO nav;

--
-- Name: macwatch_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE macwatch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.macwatch_id_seq OWNER TO nav;

--
-- Name: macwatch_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE macwatch_id_seq OWNED BY macwatch.id;


--
-- Name: macwatch_match; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE macwatch_match (
    id integer NOT NULL,
    macwatch integer NOT NULL,
    cam integer NOT NULL,
    posted timestamp without time zone DEFAULT now()
);


ALTER TABLE manage.macwatch_match OWNER TO nav;

--
-- Name: macwatch_match_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE macwatch_match_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.macwatch_match_id_seq OWNER TO nav;

--
-- Name: macwatch_match_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE macwatch_match_id_seq OWNED BY macwatch_match.id;


--
-- Name: maint_component; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE maint_component (
    id integer NOT NULL,
    maint_taskid integer NOT NULL,
    key character varying NOT NULL,
    value character varying NOT NULL
);


ALTER TABLE manage.maint_component OWNER TO nav;

--
-- Name: maint_task; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE maint_task (
    maint_taskid integer NOT NULL,
    maint_start timestamp without time zone NOT NULL,
    maint_end timestamp without time zone NOT NULL,
    description text NOT NULL,
    author character varying NOT NULL,
    state character varying NOT NULL
);


ALTER TABLE manage.maint_task OWNER TO nav;

--
-- Name: maint; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW maint AS
    SELECT maint_task.maint_taskid, maint_task.maint_start, maint_task.maint_end, maint_task.description, maint_task.author, maint_task.state, maint_component.id, maint_component.key, maint_component.value FROM (maint_task NATURAL JOIN maint_component);


ALTER TABLE manage.maint OWNER TO nav;

--
-- Name: maint_component_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE maint_component_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.maint_component_id_seq OWNER TO nav;

--
-- Name: maint_component_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE maint_component_id_seq OWNED BY maint_component.id;


--
-- Name: maint_task_maint_taskid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE maint_task_maint_taskid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.maint_task_maint_taskid_seq OWNER TO nav;

--
-- Name: maint_task_maint_taskid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE maint_task_maint_taskid_seq OWNED BY maint_task.maint_taskid;


--
-- Name: mem; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE mem (
    memid integer NOT NULL,
    netboxid integer NOT NULL,
    memtype character varying NOT NULL,
    device character varying NOT NULL,
    size integer NOT NULL,
    used integer
);


ALTER TABLE manage.mem OWNER TO nav;

--
-- Name: mem_memid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE mem_memid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.mem_memid_seq OWNER TO nav;

--
-- Name: mem_memid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE mem_memid_seq OWNED BY mem.memid;


--
-- Name: message; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE message (
    messageid integer NOT NULL,
    title character varying NOT NULL,
    description text NOT NULL,
    tech_description text,
    publish_start timestamp without time zone,
    publish_end timestamp without time zone,
    author character varying NOT NULL,
    last_changed timestamp without time zone,
    replaces_message integer,
    replaced_by integer
);


ALTER TABLE manage.message OWNER TO nav;

--
-- Name: message_messageid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE message_messageid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.message_messageid_seq OWNER TO nav;

--
-- Name: message_messageid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE message_messageid_seq OWNED BY message.messageid;


--
-- Name: message_to_maint_task; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE message_to_maint_task (
    id integer NOT NULL,
    messageid integer NOT NULL,
    maint_taskid integer NOT NULL
);


ALTER TABLE manage.message_to_maint_task OWNER TO nav;

--
-- Name: message_to_maint_task_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE message_to_maint_task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.message_to_maint_task_id_seq OWNER TO nav;

--
-- Name: message_to_maint_task_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE message_to_maint_task_id_seq OWNED BY message_to_maint_task.id;


--
-- Name: message_with_replaced; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW message_with_replaced AS
    SELECT m.messageid, m.title, m.description, m.tech_description, m.publish_start, m.publish_end, m.author, m.last_changed, m.replaces_message, m.replaced_by, rm.title AS replaces_message_title, rm.description AS replaces_message_description, rm.tech_description AS replaces_message_tech_description, rm.publish_start AS replaces_message_publish_start, rm.publish_end AS replaces_message_publish_end, rm.author AS replaces_message_author, rm.last_changed AS replaces_message_last_changed, rb.title AS replaced_by_title, rb.description AS replaced_by_description, rb.tech_description AS replaced_by_tech_description, rb.publish_start AS replaced_by_publish_start, rb.publish_end AS replaced_by_publish_end, rb.author AS replaced_by_author, rb.last_changed AS replaced_by_last_changed FROM ((message m LEFT JOIN message rm ON ((m.replaces_message = rm.messageid))) LEFT JOIN message rb ON ((m.replaced_by = rb.messageid)));


ALTER TABLE manage.message_with_replaced OWNER TO nav;

--
-- Name: module; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE module (
    moduleid integer NOT NULL,
    deviceid integer NOT NULL,
    netboxid integer NOT NULL,
    module integer,
    name character varying NOT NULL,
    model character varying,
    descr character varying,
    up character(1) DEFAULT 'y'::bpchar NOT NULL,
    downsince timestamp without time zone,
    CONSTRAINT module_up_check CHECK (((up = 'y'::bpchar) OR (up = 'n'::bpchar)))
);


ALTER TABLE manage.module OWNER TO nav;

--
-- Name: module_moduleid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE module_moduleid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.module_moduleid_seq OWNER TO nav;

--
-- Name: module_moduleid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE module_moduleid_seq OWNED BY module.moduleid;


--
-- Name: netbios; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netbios (
    netbiosid integer NOT NULL,
    ip inet NOT NULL,
    mac macaddr,
    name character varying NOT NULL,
    server character varying NOT NULL,
    username character varying NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone DEFAULT 'infinity'::timestamp without time zone NOT NULL
);


ALTER TABLE manage.netbios OWNER TO nav;

--
-- Name: netbios_netbiosid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netbios_netbiosid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netbios_netbiosid_seq OWNER TO nav;

--
-- Name: netbios_netbiosid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netbios_netbiosid_seq OWNED BY netbios.netbiosid;


--
-- Name: netbox; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netbox (
    netboxid integer NOT NULL,
    ip inet NOT NULL,
    roomid character varying(30) NOT NULL,
    typeid integer,
    deviceid integer NOT NULL,
    sysname character varying NOT NULL,
    catid character varying(8) NOT NULL,
    orgid character varying(30) NOT NULL,
    ro character varying,
    rw character varying,
    up character(1) DEFAULT 'y'::bpchar NOT NULL,
    snmp_version integer DEFAULT 1 NOT NULL,
    upsince timestamp without time zone DEFAULT now() NOT NULL,
    uptodate boolean DEFAULT false NOT NULL,
    discovered timestamp without time zone DEFAULT now(),
    data hstore DEFAULT ''::hstore NOT NULL,
    CONSTRAINT netbox_up_check CHECK ((((up = 'y'::bpchar) OR (up = 'n'::bpchar)) OR (up = 's'::bpchar)))
);


ALTER TABLE manage.netbox OWNER TO nav;

--
-- Name: netbox_netboxid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netbox_netboxid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netbox_netboxid_seq OWNER TO nav;

--
-- Name: netbox_netboxid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netbox_netboxid_seq OWNED BY netbox.netboxid;


--
-- Name: netbox_vtpvlan; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netbox_vtpvlan (
    id integer NOT NULL,
    netboxid integer,
    vtpvlan integer
);


ALTER TABLE manage.netbox_vtpvlan OWNER TO nav;

--
-- Name: netbox_vtpvlan_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netbox_vtpvlan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netbox_vtpvlan_id_seq OWNER TO nav;

--
-- Name: netbox_vtpvlan_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netbox_vtpvlan_id_seq OWNED BY netbox_vtpvlan.id;


--
-- Name: netboxcategory; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netboxcategory (
    id integer NOT NULL,
    netboxid integer NOT NULL,
    category character varying NOT NULL
);


ALTER TABLE manage.netboxcategory OWNER TO nav;

--
-- Name: netboxcategory_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netboxcategory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netboxcategory_id_seq OWNER TO nav;

--
-- Name: netboxcategory_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netboxcategory_id_seq OWNED BY netboxcategory.id;


--
-- Name: netboxgroup; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netboxgroup (
    netboxgroupid character varying NOT NULL,
    descr character varying NOT NULL
);


ALTER TABLE manage.netboxgroup OWNER TO nav;

--
-- Name: netboxinfo; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netboxinfo (
    netboxinfoid integer NOT NULL,
    netboxid integer NOT NULL,
    key character varying,
    var character varying NOT NULL,
    val text NOT NULL
);


ALTER TABLE manage.netboxinfo OWNER TO nav;

--
-- Name: netboxinfo_netboxinfoid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netboxinfo_netboxinfoid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netboxinfo_netboxinfoid_seq OWNER TO nav;

--
-- Name: netboxinfo_netboxinfoid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netboxinfo_netboxinfoid_seq OWNED BY netboxinfo.netboxinfoid;


--
-- Name: netboxmac; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW netboxmac AS
    SELECT DISTINCT ON (foo.mac) foo.netboxid, foo.mac FROM ((SELECT DISTINCT netbox.netboxid, arp.mac FROM (netbox JOIN arp ON (((arp.ip = netbox.ip) AND (arp.end_time = 'infinity'::timestamp without time zone)))) UNION SELECT interface.netboxid, arp.mac FROM (((arp JOIN gwportprefix gwp ON ((arp.ip = gwp.gwip))) LEFT JOIN (SELECT gwportprefix.prefixid, (count(*) > 0) AS has_virtual FROM gwportprefix WHERE (gwportprefix.virtual = true) GROUP BY gwportprefix.prefixid) prefix_virtual_ports ON ((gwp.prefixid = prefix_virtual_ports.prefixid))) JOIN interface USING (interfaceid)) WHERE ((arp.end_time = 'infinity'::timestamp without time zone) AND ((gwp.virtual = true) OR (prefix_virtual_ports.has_virtual IS NULL)))) UNION SELECT DISTINCT ON (interface.ifphysaddress) interface.netboxid, interface.ifphysaddress AS mac FROM interface WHERE ((interface.iftype = 6) AND (interface.ifphysaddress IS NOT NULL))) foo WHERE (foo.mac <> '00:00:00:00:00:00'::macaddr) ORDER BY foo.mac, foo.netboxid;


ALTER TABLE manage.netboxmac OWNER TO nav;

--
-- Name: prefix; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE prefix (
    prefixid integer NOT NULL,
    netaddr cidr NOT NULL,
    vlanid integer
);


ALTER TABLE manage.prefix OWNER TO nav;

--
-- Name: netboxprefix; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW netboxprefix AS
    SELECT netbox.netboxid, (SELECT prefix.prefixid FROM prefix WHERE (netbox.ip << (prefix.netaddr)::inet) ORDER BY masklen((prefix.netaddr)::inet) DESC LIMIT 1) AS prefixid FROM netbox;


ALTER TABLE manage.netboxprefix OWNER TO nav;

--
-- Name: netboxsnmpoid; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE netboxsnmpoid (
    id integer NOT NULL,
    netboxid integer NOT NULL,
    snmpoidid integer NOT NULL,
    frequency integer
);


ALTER TABLE manage.netboxsnmpoid OWNER TO nav;

--
-- Name: netboxsnmpoid_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE netboxsnmpoid_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.netboxsnmpoid_id_seq OWNER TO nav;

--
-- Name: netboxsnmpoid_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE netboxsnmpoid_id_seq OWNED BY netboxsnmpoid.id;


--
-- Name: nettype; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE nettype (
    nettypeid character varying NOT NULL,
    descr character varying,
    edit boolean DEFAULT false
);


ALTER TABLE manage.nettype OWNER TO nav;

--
-- Name: org; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE org (
    orgid character varying(30) NOT NULL,
    parent character varying(30),
    descr character varying,
    contact character varying,
    data hstore DEFAULT ''::hstore NOT NULL
);


ALTER TABLE manage.org OWNER TO nav;

--
-- Name: patch; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE patch (
    patchid integer NOT NULL,
    interfaceid integer NOT NULL,
    cablingid integer NOT NULL,
    split character varying DEFAULT 'no'::character varying NOT NULL
);


ALTER TABLE manage.patch OWNER TO nav;

--
-- Name: patch_patchid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE patch_patchid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.patch_patchid_seq OWNER TO nav;

--
-- Name: patch_patchid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE patch_patchid_seq OWNED BY patch.patchid;


--
-- Name: powersupply_or_fan; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE powersupply_or_fan (
    powersupplyid integer NOT NULL,
    netboxid integer,
    deviceid integer,
    name character varying NOT NULL,
    model character varying,
    descr character varying,
    physical_class character varying NOT NULL,
    downsince timestamp without time zone,
    sensor_oid character varying,
    up character(1) DEFAULT 'u'::bpchar NOT NULL,
    CONSTRAINT powersupply_or_fan_up_check CHECK (((((up = 'y'::bpchar) OR (up = 'n'::bpchar)) OR (up = 'u'::bpchar)) OR (up = 'w'::bpchar)))
);


ALTER TABLE manage.powersupply_or_fan OWNER TO nav;

--
-- Name: powersupply_or_fan_powersupplyid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE powersupply_or_fan_powersupplyid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.powersupply_or_fan_powersupplyid_seq OWNER TO nav;

--
-- Name: powersupply_or_fan_powersupplyid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE powersupply_or_fan_powersupplyid_seq OWNED BY powersupply_or_fan.powersupplyid;


--
-- Name: prefix_active_ip_cnt; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW prefix_active_ip_cnt AS
    SELECT prefix.prefixid, count(DISTINCT arp.ip) AS active_ip_cnt FROM (prefix LEFT JOIN arp ON ((arp.ip << (prefix.netaddr)::inet))) WHERE (arp.end_time = 'infinity'::timestamp without time zone) GROUP BY prefix.prefixid;


ALTER TABLE manage.prefix_active_ip_cnt OWNER TO nav;

--
-- Name: prefix_max_ip_cnt; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW prefix_max_ip_cnt AS
    SELECT prefix.prefixid, CASE (pow((2)::double precision, ((32 - masklen((prefix.netaddr)::inet)))::double precision) - (2)::double precision) WHEN (-1) THEN (0)::double precision ELSE (pow((2)::double precision, ((32 - masklen((prefix.netaddr)::inet)))::double precision) - (2)::double precision) END AS max_ip_cnt FROM prefix;


ALTER TABLE manage.prefix_max_ip_cnt OWNER TO nav;

--
-- Name: prefix_prefixid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE prefix_prefixid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.prefix_prefixid_seq OWNER TO nav;

--
-- Name: prefix_prefixid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE prefix_prefixid_seq OWNED BY prefix.prefixid;


--
-- Name: room; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE room (
    roomid character varying(30) NOT NULL,
    locationid character varying(30),
    descr character varying,
    "position" point,
    data hstore DEFAULT ''::hstore NOT NULL
);


ALTER TABLE manage.room OWNER TO nav;

--
-- Name: rproto_attr_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE rproto_attr_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.rproto_attr_id_seq OWNER TO nav;

--
-- Name: rproto_attr_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE rproto_attr_id_seq OWNED BY rproto_attr.id;


--
-- Name: rrd_datasource; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE rrd_datasource (
    rrd_datasourceid integer NOT NULL,
    rrd_fileid integer,
    name character varying,
    descr character varying,
    dstype character varying,
    units character varying,
    threshold character varying,
    max character varying,
    delimiter character(1),
    thresholdstate character varying,
    CONSTRAINT rrd_datasource_delimiter_check CHECK (((delimiter = '>'::bpchar) OR (delimiter = '<'::bpchar))),
    CONSTRAINT rrd_datasource_dstype_check CHECK ((((((dstype)::text = 'GAUGE'::text) OR ((dstype)::text = 'DERIVE'::text)) OR ((dstype)::text = 'COUNTER'::text)) OR ((dstype)::text = 'ABSOLUTE'::text))),
    CONSTRAINT rrd_datasource_thresholdstate_check CHECK ((((thresholdstate)::text = 'active'::text) OR ((thresholdstate)::text = 'inactive'::text)))
);


ALTER TABLE manage.rrd_datasource OWNER TO nav;

--
-- Name: rrd_datasource_rrd_datasourceid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE rrd_datasource_rrd_datasourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.rrd_datasource_rrd_datasourceid_seq OWNER TO nav;

--
-- Name: rrd_datasource_rrd_datasourceid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE rrd_datasource_rrd_datasourceid_seq OWNED BY rrd_datasource.rrd_datasourceid;


--
-- Name: rrd_file; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE rrd_file (
    rrd_fileid integer NOT NULL,
    path character varying NOT NULL,
    filename character varying NOT NULL,
    step integer,
    subsystem character varying,
    netboxid integer,
    key character varying,
    value character varying,
    category character varying
);


ALTER TABLE manage.rrd_file OWNER TO nav;

--
-- Name: rrd_file_rrd_fileid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE rrd_file_rrd_fileid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.rrd_file_rrd_fileid_seq OWNER TO nav;

--
-- Name: rrd_file_rrd_fileid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE rrd_file_rrd_fileid_seq OWNED BY rrd_file.rrd_fileid;


--
-- Name: rrddatasourcenetbox; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW rrddatasourcenetbox AS
    SELECT DISTINCT rrd_datasource.descr, rrd_datasource.rrd_datasourceid, netbox.sysname FROM ((rrd_datasource JOIN rrd_file USING (rrd_fileid)) JOIN netbox USING (netboxid));


ALTER TABLE manage.rrddatasourcenetbox OWNER TO nav;

--
-- Name: schema_change_log; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE schema_change_log (
    id integer NOT NULL,
    major integer NOT NULL,
    minor integer NOT NULL,
    point integer NOT NULL,
    script_name character varying NOT NULL,
    date_applied timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE manage.schema_change_log OWNER TO nav;

--
-- Name: schema_change_log_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE schema_change_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.schema_change_log_id_seq OWNER TO nav;

--
-- Name: schema_change_log_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE schema_change_log_id_seq OWNED BY schema_change_log.id;


--
-- Name: sensor; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE sensor (
    sensorid integer NOT NULL,
    netboxid integer,
    oid character varying,
    unit_of_measurement character varying,
    "precision" integer DEFAULT 0,
    data_scale character varying,
    human_readable character varying,
    name character varying,
    internal_name character varying,
    mib character varying
);


ALTER TABLE manage.sensor OWNER TO nav;

--
-- Name: sensor_sensorid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE sensor_sensorid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.sensor_sensorid_seq OWNER TO nav;

--
-- Name: sensor_sensorid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE sensor_sensorid_seq OWNED BY sensor.sensorid;


--
-- Name: service; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE service (
    serviceid integer NOT NULL,
    netboxid integer,
    active boolean DEFAULT true,
    handler character varying,
    version character varying,
    up character(1) DEFAULT 'y'::bpchar NOT NULL,
    CONSTRAINT service_up_check CHECK ((((up = 'y'::bpchar) OR (up = 'n'::bpchar)) OR (up = 's'::bpchar)))
);


ALTER TABLE manage.service OWNER TO nav;

--
-- Name: service_serviceid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE service_serviceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.service_serviceid_seq OWNER TO nav;

--
-- Name: service_serviceid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE service_serviceid_seq OWNED BY service.serviceid;


--
-- Name: serviceproperty; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE serviceproperty (
    id integer NOT NULL,
    serviceid integer NOT NULL,
    property character varying(64) NOT NULL,
    value character varying
);


ALTER TABLE manage.serviceproperty OWNER TO nav;

--
-- Name: serviceproperty_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE serviceproperty_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.serviceproperty_id_seq OWNER TO nav;

--
-- Name: serviceproperty_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE serviceproperty_id_seq OWNED BY serviceproperty.id;


--
-- Name: snmpoid; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE snmpoid (
    snmpoidid integer NOT NULL,
    oidkey character varying NOT NULL,
    snmpoid character varying NOT NULL,
    oidsource character varying,
    getnext boolean DEFAULT true NOT NULL,
    decodehex boolean DEFAULT false NOT NULL,
    match_regex character varying,
    defaultfreq integer DEFAULT 21600 NOT NULL,
    uptodate boolean DEFAULT false NOT NULL,
    descr character varying,
    oidname character varying,
    mib character varying,
    unit character varying
);


ALTER TABLE manage.snmpoid OWNER TO nav;

--
-- Name: snmpoid_snmpoidid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE snmpoid_snmpoidid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.snmpoid_snmpoidid_seq OWNER TO nav;

--
-- Name: snmpoid_snmpoidid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE snmpoid_snmpoidid_seq OWNED BY snmpoid.snmpoidid;


--
-- Name: subsystem; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE subsystem (
    name character varying NOT NULL,
    descr character varying
);


ALTER TABLE manage.subsystem OWNER TO nav;

--
-- Name: swport; Type: VIEW; Schema: manage; Owner: nav
--

CREATE VIEW swport AS
    SELECT interface.interfaceid AS swportid, interface.moduleid, interface.ifindex, interface.baseport AS port, interface.ifdescr AS interface, CASE interface.ifadminstatus WHEN 1 THEN CASE interface.ifoperstatus WHEN 1 THEN 'y'::character(1) ELSE 'n'::character(1) END ELSE 'd'::character(1) END AS link, interface.speed, interface.duplex, interface.media, interface.vlan, interface.trunk, interface.ifalias AS portname, interface.to_netboxid, interface.to_interfaceid AS to_swportid FROM interface WHERE (NOT (interface.interfaceid IN (SELECT gwportprefix.interfaceid FROM gwportprefix)));


ALTER TABLE manage.swport OWNER TO nav;

--
-- Name: swportblocked; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE swportblocked (
    interfaceid integer NOT NULL,
    vlan integer NOT NULL,
    swportblockedid integer NOT NULL
);


ALTER TABLE manage.swportblocked OWNER TO nav;

--
-- Name: swportblocked_swportblockedid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE swportblocked_swportblockedid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.swportblocked_swportblockedid_seq OWNER TO nav;

--
-- Name: swportblocked_swportblockedid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE swportblocked_swportblockedid_seq OWNED BY swportblocked.swportblockedid;


--
-- Name: swportvlan; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE swportvlan (
    swportvlanid integer NOT NULL,
    interfaceid integer NOT NULL,
    vlanid integer NOT NULL,
    direction character(1) DEFAULT 'x'::bpchar NOT NULL
);


ALTER TABLE manage.swportvlan OWNER TO nav;

--
-- Name: swportvlan_swportvlanid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE swportvlan_swportvlanid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.swportvlan_swportvlanid_seq OWNER TO nav;

--
-- Name: swportvlan_swportvlanid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE swportvlan_swportvlanid_seq OWNED BY swportvlan.swportvlanid;


--
-- Name: thresholdrule; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE thresholdrule (
    id integer NOT NULL,
    target character varying NOT NULL,
    alert character varying NOT NULL,
    clear character varying,
    raw boolean DEFAULT false NOT NULL,
    description character varying,
    creator_id integer,
    created timestamp without time zone DEFAULT now(),
    period integer
);


ALTER TABLE manage.thresholdrule OWNER TO nav;

--
-- Name: thresholdrule_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE thresholdrule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.thresholdrule_id_seq OWNER TO nav;

--
-- Name: thresholdrule_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE thresholdrule_id_seq OWNED BY thresholdrule.id;


--
-- Name: type; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE type (
    typeid integer NOT NULL,
    vendorid character varying(15) NOT NULL,
    typename character varying NOT NULL,
    sysobjectid character varying NOT NULL,
    descr character varying
);


ALTER TABLE manage.type OWNER TO nav;

--
-- Name: type_typeid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE type_typeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.type_typeid_seq OWNER TO nav;

--
-- Name: type_typeid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE type_typeid_seq OWNED BY type.typeid;


--
-- Name: unrecognized_neighbor; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE unrecognized_neighbor (
    id integer NOT NULL,
    netboxid integer NOT NULL,
    interfaceid integer NOT NULL,
    remote_id character varying NOT NULL,
    remote_name character varying NOT NULL,
    source character varying NOT NULL,
    since timestamp without time zone DEFAULT now() NOT NULL,
    ignored_since timestamp without time zone
);


ALTER TABLE manage.unrecognized_neighbor OWNER TO nav;

--
-- Name: TABLE unrecognized_neighbor; Type: COMMENT; Schema: manage; Owner: nav
--

COMMENT ON TABLE unrecognized_neighbor IS 'Unrecognized neighboring devices reported by support discovery protocols';


--
-- Name: unrecognized_neighbor_id_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE unrecognized_neighbor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.unrecognized_neighbor_id_seq OWNER TO nav;

--
-- Name: unrecognized_neighbor_id_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE unrecognized_neighbor_id_seq OWNED BY unrecognized_neighbor.id;


--
-- Name: usage; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE usage (
    usageid character varying(30) NOT NULL,
    descr character varying NOT NULL
);


ALTER TABLE manage.usage OWNER TO nav;

--
-- Name: vendor; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE vendor (
    vendorid character varying(15) NOT NULL
);


ALTER TABLE manage.vendor OWNER TO nav;

--
-- Name: vlan; Type: TABLE; Schema: manage; Owner: nav; Tablespace: 
--

CREATE TABLE vlan (
    vlanid integer NOT NULL,
    vlan integer,
    nettype character varying NOT NULL,
    orgid character varying(30),
    usageid character varying(30),
    netident character varying,
    description character varying
);


ALTER TABLE manage.vlan OWNER TO nav;

--
-- Name: vlan_vlanid_seq; Type: SEQUENCE; Schema: manage; Owner: nav
--

CREATE SEQUENCE vlan_vlanid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE manage.vlan_vlanid_seq OWNER TO nav;

--
-- Name: vlan_vlanid_seq; Type: SEQUENCE OWNED BY; Schema: manage; Owner: nav
--

ALTER SEQUENCE vlan_vlanid_seq OWNED BY vlan.vlanid;


SET search_path = profiles, pg_catalog;

--
-- Name: account; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE account (
    id integer NOT NULL,
    login character varying NOT NULL,
    name character varying DEFAULT 'Noname'::character varying,
    password character varying,
    ext_sync character varying
);


ALTER TABLE profiles.account OWNER TO nav;

--
-- Name: account_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE account_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.account_id_seq OWNER TO nav;

--
-- Name: account_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE account_id_seq OWNED BY account.id;


--
-- Name: account_navlet; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE account_navlet (
    id integer NOT NULL,
    navlet character varying NOT NULL,
    account integer,
    col integer,
    displayorder integer NOT NULL,
    preferences character varying
);


ALTER TABLE profiles.account_navlet OWNER TO nav;

--
-- Name: account_navlet_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE account_navlet_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.account_navlet_id_seq OWNER TO nav;

--
-- Name: account_navlet_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE account_navlet_id_seq OWNED BY account_navlet.id;


--
-- Name: accountalertqueue; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountalertqueue (
    id integer NOT NULL,
    account_id integer,
    alert_id integer,
    subscription_id integer,
    insertion_time timestamp without time zone NOT NULL
);


ALTER TABLE profiles.accountalertqueue OWNER TO nav;

--
-- Name: accountalertqueue_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountalertqueue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountalertqueue_id_seq OWNER TO nav;

--
-- Name: accountalertqueue_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountalertqueue_id_seq OWNED BY accountalertqueue.id;


--
-- Name: accountgroup; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountgroup (
    id integer NOT NULL,
    name character varying DEFAULT 'Noname'::character varying,
    descr character varying
);


ALTER TABLE profiles.accountgroup OWNER TO nav;

--
-- Name: accountgroup_accounts; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountgroup_accounts (
    id integer NOT NULL,
    account_id integer NOT NULL,
    accountgroup_id integer NOT NULL
);


ALTER TABLE profiles.accountgroup_accounts OWNER TO nav;

--
-- Name: accountgroup_accounts_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountgroup_accounts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountgroup_accounts_id_seq OWNER TO nav;

--
-- Name: accountgroup_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountgroup_accounts_id_seq OWNED BY accountgroup_accounts.id;


--
-- Name: accountgroup_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountgroup_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountgroup_id_seq OWNER TO nav;

--
-- Name: accountgroup_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountgroup_id_seq OWNED BY accountgroup.id;


--
-- Name: accountgroupprivilege; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountgroupprivilege (
    id integer NOT NULL,
    accountgroupid integer NOT NULL,
    privilegeid integer NOT NULL,
    target character varying NOT NULL
);


ALTER TABLE profiles.accountgroupprivilege OWNER TO nav;

--
-- Name: accountgroupprivilege_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountgroupprivilege_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountgroupprivilege_id_seq OWNER TO nav;

--
-- Name: accountgroupprivilege_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountgroupprivilege_id_seq OWNED BY accountgroupprivilege.id;


--
-- Name: accountingroup; Type: VIEW; Schema: profiles; Owner: nav
--

CREATE VIEW accountingroup AS
    SELECT accountgroup_accounts.account_id AS accountid, accountgroup_accounts.accountgroup_id AS groupid FROM accountgroup_accounts;


ALTER TABLE profiles.accountingroup OWNER TO nav;

--
-- Name: accountorg; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountorg (
    id integer NOT NULL,
    account_id integer NOT NULL,
    organization_id character varying(30) NOT NULL
);


ALTER TABLE profiles.accountorg OWNER TO nav;

--
-- Name: accountorg_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountorg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountorg_id_seq OWNER TO nav;

--
-- Name: accountorg_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountorg_id_seq OWNED BY accountorg.id;


--
-- Name: accountproperty; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accountproperty (
    id integer NOT NULL,
    accountid integer,
    property character varying,
    value character varying
);


ALTER TABLE profiles.accountproperty OWNER TO nav;

--
-- Name: accountproperty_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accountproperty_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accountproperty_id_seq OWNER TO nav;

--
-- Name: accountproperty_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accountproperty_id_seq OWNED BY accountproperty.id;


--
-- Name: accounttool; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE accounttool (
    account_tool_id integer NOT NULL,
    toolname character varying,
    accountid integer NOT NULL,
    display boolean DEFAULT true,
    priority integer DEFAULT 0
);


ALTER TABLE profiles.accounttool OWNER TO nav;

--
-- Name: accounttool_account_tool_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE accounttool_account_tool_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.accounttool_account_tool_id_seq OWNER TO nav;

--
-- Name: accounttool_account_tool_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE accounttool_account_tool_id_seq OWNED BY accounttool.account_tool_id;


--
-- Name: alertaddress; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE alertaddress (
    id integer NOT NULL,
    accountid integer NOT NULL,
    type integer NOT NULL,
    address character varying
);


ALTER TABLE profiles.alertaddress OWNER TO nav;

--
-- Name: alertaddress_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE alertaddress_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.alertaddress_id_seq OWNER TO nav;

--
-- Name: alertaddress_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE alertaddress_id_seq OWNED BY alertaddress.id;


--
-- Name: alertpreference; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE alertpreference (
    accountid integer NOT NULL,
    activeprofile integer,
    lastsentday timestamp without time zone,
    lastsentweek timestamp without time zone
);


ALTER TABLE profiles.alertpreference OWNER TO nav;

--
-- Name: alertprofile; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE alertprofile (
    id integer NOT NULL,
    accountid integer NOT NULL,
    name character varying,
    daily_dispatch_time time without time zone DEFAULT '08:00:00'::time without time zone NOT NULL,
    weekly_dispatch_day integer DEFAULT 0 NOT NULL,
    weekly_dispatch_time time without time zone DEFAULT '08:30:00'::time without time zone NOT NULL
);


ALTER TABLE profiles.alertprofile OWNER TO nav;

--
-- Name: alertprofile_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE alertprofile_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.alertprofile_id_seq OWNER TO nav;

--
-- Name: alertprofile_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE alertprofile_id_seq OWNED BY alertprofile.id;


--
-- Name: alertsender; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE alertsender (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    handler character varying(100) NOT NULL
);


ALTER TABLE profiles.alertsender OWNER TO nav;

--
-- Name: alertsender_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE alertsender_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.alertsender_id_seq OWNER TO nav;

--
-- Name: alertsender_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE alertsender_id_seq OWNED BY alertsender.id;


--
-- Name: alertsubscription; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE alertsubscription (
    id integer NOT NULL,
    alert_address_id integer NOT NULL,
    time_period_id integer NOT NULL,
    filter_group_id integer NOT NULL,
    subscription_type integer,
    ignore_resolved_alerts boolean
);


ALTER TABLE profiles.alertsubscription OWNER TO nav;

--
-- Name: alertsubscription_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE alertsubscription_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.alertsubscription_id_seq OWNER TO nav;

--
-- Name: alertsubscription_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE alertsubscription_id_seq OWNED BY alertsubscription.id;


--
-- Name: django_session; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE profiles.django_session OWNER TO nav;

--
-- Name: expression; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE expression (
    id integer NOT NULL,
    filter_id integer NOT NULL,
    match_field_id integer NOT NULL,
    operator integer,
    value character varying
);


ALTER TABLE profiles.expression OWNER TO nav;

--
-- Name: expression_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE expression_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.expression_id_seq OWNER TO nav;

--
-- Name: expression_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE expression_id_seq OWNED BY expression.id;


--
-- Name: filter; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE filter (
    id integer NOT NULL,
    owner_id integer,
    name character varying
);


ALTER TABLE profiles.filter OWNER TO nav;

--
-- Name: filter_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE filter_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.filter_id_seq OWNER TO nav;

--
-- Name: filter_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE filter_id_seq OWNED BY filter.id;


--
-- Name: filtergroup; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE filtergroup (
    id integer NOT NULL,
    owner_id integer,
    name character varying,
    description character varying
);


ALTER TABLE profiles.filtergroup OWNER TO nav;

--
-- Name: filtergroup_group_permission; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE filtergroup_group_permission (
    id integer NOT NULL,
    accountgroup_id integer NOT NULL,
    filtergroup_id integer NOT NULL
);


ALTER TABLE profiles.filtergroup_group_permission OWNER TO nav;

--
-- Name: filtergroup_group_permission_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE filtergroup_group_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.filtergroup_group_permission_id_seq OWNER TO nav;

--
-- Name: filtergroup_group_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE filtergroup_group_permission_id_seq OWNED BY filtergroup_group_permission.id;


--
-- Name: filtergroup_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE filtergroup_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.filtergroup_id_seq OWNER TO nav;

--
-- Name: filtergroup_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE filtergroup_id_seq OWNED BY filtergroup.id;


--
-- Name: filtergroupcontent; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE filtergroupcontent (
    id integer NOT NULL,
    include boolean DEFAULT true NOT NULL,
    positive boolean DEFAULT true NOT NULL,
    priority integer NOT NULL,
    filter_id integer NOT NULL,
    filter_group_id integer NOT NULL
);


ALTER TABLE profiles.filtergroupcontent OWNER TO nav;

--
-- Name: filtergroupcontent_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE filtergroupcontent_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.filtergroupcontent_id_seq OWNER TO nav;

--
-- Name: filtergroupcontent_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE filtergroupcontent_id_seq OWNED BY filtergroupcontent.id;


--
-- Name: matchfield; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE matchfield (
    id integer NOT NULL,
    name character varying,
    description character varying,
    value_help character varying,
    value_id character varying,
    value_name character varying,
    value_sort character varying,
    list_limit integer DEFAULT 300,
    data_type integer DEFAULT 0 NOT NULL,
    show_list boolean
);


ALTER TABLE profiles.matchfield OWNER TO nav;

--
-- Name: matchfield_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE matchfield_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.matchfield_id_seq OWNER TO nav;

--
-- Name: matchfield_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE matchfield_id_seq OWNED BY matchfield.id;


--
-- Name: navbarlink; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE navbarlink (
    id integer NOT NULL,
    accountid integer DEFAULT 0 NOT NULL,
    name character varying,
    uri character varying
);


ALTER TABLE profiles.navbarlink OWNER TO nav;

--
-- Name: navbarlink_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE navbarlink_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.navbarlink_id_seq OWNER TO nav;

--
-- Name: navbarlink_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE navbarlink_id_seq OWNED BY navbarlink.id;


--
-- Name: netmap_view; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE netmap_view (
    viewid integer NOT NULL,
    owner integer NOT NULL,
    title character varying NOT NULL,
    zoom character varying NOT NULL,
    is_public boolean DEFAULT false NOT NULL,
    last_modified timestamp without time zone DEFAULT now() NOT NULL,
    topology integer NOT NULL,
    display_elinks boolean DEFAULT false NOT NULL,
    display_orphans boolean DEFAULT false NOT NULL,
    description text,
    location_room_filter character varying DEFAULT ''::character varying NOT NULL
);


ALTER TABLE profiles.netmap_view OWNER TO nav;

--
-- Name: TABLE netmap_view; Type: COMMENT; Schema: profiles; Owner: nav
--

COMMENT ON TABLE netmap_view IS 'Stored views with settings for NetMap';


--
-- Name: netmap_view_categories; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE netmap_view_categories (
    id integer NOT NULL,
    viewid integer NOT NULL,
    catid character varying(8) NOT NULL
);


ALTER TABLE profiles.netmap_view_categories OWNER TO nav;

--
-- Name: netmap_view_categories_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE netmap_view_categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.netmap_view_categories_id_seq OWNER TO nav;

--
-- Name: netmap_view_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE netmap_view_categories_id_seq OWNED BY netmap_view_categories.id;


--
-- Name: netmap_view_defaultview; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE netmap_view_defaultview (
    id integer NOT NULL,
    viewid integer NOT NULL,
    ownerid integer NOT NULL
);


ALTER TABLE profiles.netmap_view_defaultview OWNER TO nav;

--
-- Name: TABLE netmap_view_defaultview; Type: COMMENT; Schema: profiles; Owner: nav
--

COMMENT ON TABLE netmap_view_defaultview IS 'Stores default views for users in Netmap';


--
-- Name: netmap_view_defaultview_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE netmap_view_defaultview_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.netmap_view_defaultview_id_seq OWNER TO nav;

--
-- Name: netmap_view_defaultview_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE netmap_view_defaultview_id_seq OWNED BY netmap_view_defaultview.id;


--
-- Name: netmap_view_nodeposition; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE netmap_view_nodeposition (
    id integer NOT NULL,
    viewid integer NOT NULL,
    netboxid integer NOT NULL,
    x integer NOT NULL,
    y integer NOT NULL
);


ALTER TABLE profiles.netmap_view_nodeposition OWNER TO nav;

--
-- Name: netmap_view_nodeposition_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE netmap_view_nodeposition_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.netmap_view_nodeposition_id_seq OWNER TO nav;

--
-- Name: netmap_view_nodeposition_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE netmap_view_nodeposition_id_seq OWNED BY netmap_view_nodeposition.id;


--
-- Name: netmap_view_viewid_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE netmap_view_viewid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.netmap_view_viewid_seq OWNER TO nav;

--
-- Name: netmap_view_viewid_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE netmap_view_viewid_seq OWNED BY netmap_view.viewid;


--
-- Name: operator; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE operator (
    id integer NOT NULL,
    operator_id integer NOT NULL,
    match_field_id integer NOT NULL
);


ALTER TABLE profiles.operator OWNER TO nav;

--
-- Name: operator_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE operator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.operator_id_seq OWNER TO nav;

--
-- Name: operator_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE operator_id_seq OWNED BY operator.id;


--
-- Name: operator_operator_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE operator_operator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.operator_operator_id_seq OWNER TO nav;

--
-- Name: operator_operator_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE operator_operator_id_seq OWNED BY operator.operator_id;


--
-- Name: privilege; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE privilege (
    privilegeid integer NOT NULL,
    privilegename character varying(30) NOT NULL
);


ALTER TABLE profiles.privilege OWNER TO nav;

--
-- Name: privilege_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE privilege_id_seq
    START WITH 10000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.privilege_id_seq OWNER TO nav;

--
-- Name: privilege_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE privilege_id_seq OWNED BY privilege.privilegeid;


--
-- Name: privilegebygroup; Type: VIEW; Schema: profiles; Owner: nav
--

CREATE VIEW privilegebygroup AS
    SELECT a.accountgroupid, b.privilegename AS action, a.target FROM (accountgroupprivilege a NATURAL JOIN privilege b);


ALTER TABLE profiles.privilegebygroup OWNER TO nav;

--
-- Name: smsq; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE smsq (
    id integer NOT NULL,
    accountid integer,
    "time" timestamp without time zone NOT NULL,
    phone character varying(15) NOT NULL,
    msg character varying(145) NOT NULL,
    sent character(1) DEFAULT 'N'::bpchar NOT NULL,
    smsid integer,
    timesent timestamp without time zone,
    severity integer,
    CONSTRAINT smsq_sent_check CHECK ((((sent = 'Y'::bpchar) OR (sent = 'N'::bpchar)) OR (sent = 'I'::bpchar)))
);


ALTER TABLE profiles.smsq OWNER TO nav;

--
-- Name: smsq_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE smsq_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.smsq_id_seq OWNER TO nav;

--
-- Name: smsq_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE smsq_id_seq OWNED BY smsq.id;


--
-- Name: statuspreference; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE statuspreference (
    id integer NOT NULL,
    name character varying NOT NULL,
    "position" integer NOT NULL,
    type character varying NOT NULL,
    accountid integer NOT NULL,
    services character varying DEFAULT ''::character varying NOT NULL,
    states character varying DEFAULT 'n,s'::character varying NOT NULL
);


ALTER TABLE profiles.statuspreference OWNER TO nav;

--
-- Name: statuspreference_category; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE statuspreference_category (
    id integer NOT NULL,
    statuspreference_id integer NOT NULL,
    category_id character varying NOT NULL
);


ALTER TABLE profiles.statuspreference_category OWNER TO nav;

--
-- Name: statuspreference_category_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE statuspreference_category_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.statuspreference_category_id_seq OWNER TO nav;

--
-- Name: statuspreference_category_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE statuspreference_category_id_seq OWNED BY statuspreference_category.id;


--
-- Name: statuspreference_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE statuspreference_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.statuspreference_id_seq OWNER TO nav;

--
-- Name: statuspreference_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE statuspreference_id_seq OWNED BY statuspreference.id;


--
-- Name: statuspreference_organization; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE statuspreference_organization (
    id integer NOT NULL,
    statuspreference_id integer NOT NULL,
    organization_id character varying NOT NULL
);


ALTER TABLE profiles.statuspreference_organization OWNER TO nav;

--
-- Name: statuspreference_organization_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE statuspreference_organization_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.statuspreference_organization_id_seq OWNER TO nav;

--
-- Name: statuspreference_organization_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE statuspreference_organization_id_seq OWNED BY statuspreference_organization.id;


--
-- Name: timeperiod; Type: TABLE; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE TABLE timeperiod (
    id integer NOT NULL,
    alert_profile_id integer NOT NULL,
    start_time time without time zone NOT NULL,
    valid_during integer NOT NULL
);


ALTER TABLE profiles.timeperiod OWNER TO nav;

--
-- Name: timeperiod_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE timeperiod_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE profiles.timeperiod_id_seq OWNER TO nav;

--
-- Name: timeperiod_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE timeperiod_id_seq OWNED BY timeperiod.id;


SET search_path = radius, pg_catalog;

--
-- Name: radiusacct; Type: TABLE; Schema: radius; Owner: nav; Tablespace: 
--

CREATE TABLE radiusacct (
    radacctid bigint NOT NULL,
    acctsessionid character varying(96) NOT NULL,
    acctuniqueid character varying(32) NOT NULL,
    username character varying(70),
    realm character varying(24),
    nasipaddress inet NOT NULL,
    nasporttype character varying(32),
    cisconasport character varying(32),
    acctstarttime timestamp without time zone,
    acctstoptime timestamp without time zone,
    acctsessiontime bigint,
    acctinputoctets bigint,
    acctoutputoctets bigint,
    calledstationid character varying(50),
    callingstationid character varying(50),
    acctterminatecause character varying(32),
    framedprotocol character varying(32),
    framedipaddress inet,
    acctstartdelay bigint,
    acctstopdelay bigint
);


ALTER TABLE radius.radiusacct OWNER TO nav;

--
-- Name: radiusacct_radacctid_seq; Type: SEQUENCE; Schema: radius; Owner: nav
--

CREATE SEQUENCE radiusacct_radacctid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE radius.radiusacct_radacctid_seq OWNER TO nav;

--
-- Name: radiusacct_radacctid_seq; Type: SEQUENCE OWNED BY; Schema: radius; Owner: nav
--

ALTER SEQUENCE radiusacct_radacctid_seq OWNED BY radiusacct.radacctid;


--
-- Name: radiuslog; Type: TABLE; Schema: radius; Owner: nav; Tablespace: 
--

CREATE TABLE radiuslog (
    id bigint NOT NULL,
    "time" timestamp with time zone,
    type character varying(10),
    message character varying(200),
    status character varying(65),
    username character varying(70),
    client character varying(65),
    port character varying(8)
);


ALTER TABLE radius.radiuslog OWNER TO nav;

--
-- Name: radiuslog_id_seq; Type: SEQUENCE; Schema: radius; Owner: nav
--

CREATE SEQUENCE radiuslog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE radius.radiuslog_id_seq OWNER TO nav;

--
-- Name: radiuslog_id_seq; Type: SEQUENCE OWNED BY; Schema: radius; Owner: nav
--

ALTER SEQUENCE radiuslog_id_seq OWNED BY radiuslog.id;


SET search_path = arnold, pg_catalog;

--
-- Name: blockid; Type: DEFAULT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY block ALTER COLUMN blockid SET DEFAULT nextval('block_blockid_seq'::regclass);


--
-- Name: blocked_reasonid; Type: DEFAULT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY blocked_reason ALTER COLUMN blocked_reasonid SET DEFAULT nextval('blocked_reason_blocked_reasonid_seq'::regclass);


--
-- Name: eventid; Type: DEFAULT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY event ALTER COLUMN eventid SET DEFAULT nextval('event_eventid_seq'::regclass);


--
-- Name: identityid; Type: DEFAULT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY identity ALTER COLUMN identityid SET DEFAULT nextval('identity_identityid_seq'::regclass);


--
-- Name: quarantineid; Type: DEFAULT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY quarantine_vlans ALTER COLUMN quarantineid SET DEFAULT nextval('quarantine_vlans_quarantineid_seq'::regclass);


SET search_path = logger, pg_catalog;

--
-- Name: id; Type: DEFAULT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY errorerror ALTER COLUMN id SET DEFAULT nextval('errorerror_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message ALTER COLUMN id SET DEFAULT nextval('log_message_id_seq'::regclass);


--
-- Name: type; Type: DEFAULT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message_type ALTER COLUMN type SET DEFAULT nextval('log_message_type_type_seq'::regclass);


--
-- Name: origin; Type: DEFAULT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY origin ALTER COLUMN origin SET DEFAULT nextval('origin_origin_seq'::regclass);


SET search_path = manage, pg_catalog;

--
-- Name: adjacency_candidateid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY adjacency_candidate ALTER COLUMN adjacency_candidateid SET DEFAULT nextval('adjacency_candidate_adjacency_candidateid_seq'::regclass);


--
-- Name: alerthistid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist ALTER COLUMN alerthistid SET DEFAULT nextval('alerthist_alerthistid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthistmsg ALTER COLUMN id SET DEFAULT nextval('alerthistmsg_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthistvar ALTER COLUMN id SET DEFAULT nextval('alerthistvar_id_seq'::regclass);


--
-- Name: alertqid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq ALTER COLUMN alertqid SET DEFAULT nextval('alertq_alertqid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertqmsg ALTER COLUMN id SET DEFAULT nextval('alertqmsg_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertqvar ALTER COLUMN id SET DEFAULT nextval('alertqvar_id_seq'::regclass);


--
-- Name: alerttypeid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerttype ALTER COLUMN alerttypeid SET DEFAULT nextval('alerttype_alerttypeid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY apitoken ALTER COLUMN id SET DEFAULT nextval('apitoken_id_seq'::regclass);


--
-- Name: arpid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY arp ALTER COLUMN arpid SET DEFAULT nextval('arp_arpid_seq'::regclass);


--
-- Name: cablingid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY cabling ALTER COLUMN cablingid SET DEFAULT nextval('cabling_cablingid_seq'::regclass);


--
-- Name: camid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY cam ALTER COLUMN camid SET DEFAULT nextval('cam_camid_seq'::regclass);


--
-- Name: deviceid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY device ALTER COLUMN deviceid SET DEFAULT nextval('device_deviceid_seq'::regclass);


--
-- Name: eventqid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq ALTER COLUMN eventqid SET DEFAULT nextval('eventq_eventqid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventqvar ALTER COLUMN id SET DEFAULT nextval('eventqvar_id_seq'::regclass);


--
-- Name: imageid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY image ALTER COLUMN imageid SET DEFAULT nextval('image_imageid_seq'::regclass);


--
-- Name: interfaceid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface ALTER COLUMN interfaceid SET DEFAULT nextval('interface_interfaceid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface_stack ALTER COLUMN id SET DEFAULT nextval('interface_stack_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY ipdevpoll_job_log ALTER COLUMN id SET DEFAULT nextval('ipdevpoll_job_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY macwatch ALTER COLUMN id SET DEFAULT nextval('macwatch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY macwatch_match ALTER COLUMN id SET DEFAULT nextval('macwatch_match_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY maint_component ALTER COLUMN id SET DEFAULT nextval('maint_component_id_seq'::regclass);


--
-- Name: maint_taskid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY maint_task ALTER COLUMN maint_taskid SET DEFAULT nextval('maint_task_maint_taskid_seq'::regclass);


--
-- Name: memid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY mem ALTER COLUMN memid SET DEFAULT nextval('mem_memid_seq'::regclass);


--
-- Name: messageid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message ALTER COLUMN messageid SET DEFAULT nextval('message_messageid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message_to_maint_task ALTER COLUMN id SET DEFAULT nextval('message_to_maint_task_id_seq'::regclass);


--
-- Name: moduleid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY module ALTER COLUMN moduleid SET DEFAULT nextval('module_moduleid_seq'::regclass);


--
-- Name: netbiosid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbios ALTER COLUMN netbiosid SET DEFAULT nextval('netbios_netbiosid_seq'::regclass);


--
-- Name: netboxid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox ALTER COLUMN netboxid SET DEFAULT nextval('netbox_netboxid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox_vtpvlan ALTER COLUMN id SET DEFAULT nextval('netbox_vtpvlan_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxcategory ALTER COLUMN id SET DEFAULT nextval('netboxcategory_id_seq'::regclass);


--
-- Name: netboxinfoid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxinfo ALTER COLUMN netboxinfoid SET DEFAULT nextval('netboxinfo_netboxinfoid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxsnmpoid ALTER COLUMN id SET DEFAULT nextval('netboxsnmpoid_id_seq'::regclass);


--
-- Name: patchid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY patch ALTER COLUMN patchid SET DEFAULT nextval('patch_patchid_seq'::regclass);


--
-- Name: powersupplyid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY powersupply_or_fan ALTER COLUMN powersupplyid SET DEFAULT nextval('powersupply_or_fan_powersupplyid_seq'::regclass);


--
-- Name: prefixid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY prefix ALTER COLUMN prefixid SET DEFAULT nextval('prefix_prefixid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rproto_attr ALTER COLUMN id SET DEFAULT nextval('rproto_attr_id_seq'::regclass);


--
-- Name: rrd_datasourceid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rrd_datasource ALTER COLUMN rrd_datasourceid SET DEFAULT nextval('rrd_datasource_rrd_datasourceid_seq'::regclass);


--
-- Name: rrd_fileid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rrd_file ALTER COLUMN rrd_fileid SET DEFAULT nextval('rrd_file_rrd_fileid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY schema_change_log ALTER COLUMN id SET DEFAULT nextval('schema_change_log_id_seq'::regclass);


--
-- Name: sensorid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY sensor ALTER COLUMN sensorid SET DEFAULT nextval('sensor_sensorid_seq'::regclass);


--
-- Name: serviceid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY service ALTER COLUMN serviceid SET DEFAULT nextval('service_serviceid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY serviceproperty ALTER COLUMN id SET DEFAULT nextval('serviceproperty_id_seq'::regclass);


--
-- Name: snmpoidid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY snmpoid ALTER COLUMN snmpoidid SET DEFAULT nextval('snmpoid_snmpoidid_seq'::regclass);


--
-- Name: swportblockedid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportblocked ALTER COLUMN swportblockedid SET DEFAULT nextval('swportblocked_swportblockedid_seq'::regclass);


--
-- Name: swportvlanid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportvlan ALTER COLUMN swportvlanid SET DEFAULT nextval('swportvlan_swportvlanid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY thresholdrule ALTER COLUMN id SET DEFAULT nextval('thresholdrule_id_seq'::regclass);


--
-- Name: typeid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY type ALTER COLUMN typeid SET DEFAULT nextval('type_typeid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY unrecognized_neighbor ALTER COLUMN id SET DEFAULT nextval('unrecognized_neighbor_id_seq'::regclass);


--
-- Name: vlanid; Type: DEFAULT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY vlan ALTER COLUMN vlanid SET DEFAULT nextval('vlan_vlanid_seq'::regclass);


SET search_path = profiles, pg_catalog;

--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY account ALTER COLUMN id SET DEFAULT nextval('account_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY account_navlet ALTER COLUMN id SET DEFAULT nextval('account_navlet_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountalertqueue ALTER COLUMN id SET DEFAULT nextval('accountalertqueue_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroup ALTER COLUMN id SET DEFAULT nextval('accountgroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroup_accounts ALTER COLUMN id SET DEFAULT nextval('accountgroup_accounts_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroupprivilege ALTER COLUMN id SET DEFAULT nextval('accountgroupprivilege_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountorg ALTER COLUMN id SET DEFAULT nextval('accountorg_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountproperty ALTER COLUMN id SET DEFAULT nextval('accountproperty_id_seq'::regclass);


--
-- Name: account_tool_id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accounttool ALTER COLUMN account_tool_id SET DEFAULT nextval('accounttool_account_tool_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertaddress ALTER COLUMN id SET DEFAULT nextval('alertaddress_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertprofile ALTER COLUMN id SET DEFAULT nextval('alertprofile_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertsender ALTER COLUMN id SET DEFAULT nextval('alertsender_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertsubscription ALTER COLUMN id SET DEFAULT nextval('alertsubscription_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY expression ALTER COLUMN id SET DEFAULT nextval('expression_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filter ALTER COLUMN id SET DEFAULT nextval('filter_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroup ALTER COLUMN id SET DEFAULT nextval('filtergroup_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroup_group_permission ALTER COLUMN id SET DEFAULT nextval('filtergroup_group_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroupcontent ALTER COLUMN id SET DEFAULT nextval('filtergroupcontent_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY matchfield ALTER COLUMN id SET DEFAULT nextval('matchfield_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY navbarlink ALTER COLUMN id SET DEFAULT nextval('navbarlink_id_seq'::regclass);


--
-- Name: viewid; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view ALTER COLUMN viewid SET DEFAULT nextval('netmap_view_viewid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_categories ALTER COLUMN id SET DEFAULT nextval('netmap_view_categories_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_defaultview ALTER COLUMN id SET DEFAULT nextval('netmap_view_defaultview_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_nodeposition ALTER COLUMN id SET DEFAULT nextval('netmap_view_nodeposition_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY operator ALTER COLUMN id SET DEFAULT nextval('operator_id_seq'::regclass);


--
-- Name: operator_id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY operator ALTER COLUMN operator_id SET DEFAULT nextval('operator_operator_id_seq'::regclass);


--
-- Name: privilegeid; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY privilege ALTER COLUMN privilegeid SET DEFAULT nextval('privilege_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY smsq ALTER COLUMN id SET DEFAULT nextval('smsq_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference ALTER COLUMN id SET DEFAULT nextval('statuspreference_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_category ALTER COLUMN id SET DEFAULT nextval('statuspreference_category_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_organization ALTER COLUMN id SET DEFAULT nextval('statuspreference_organization_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY timeperiod ALTER COLUMN id SET DEFAULT nextval('timeperiod_id_seq'::regclass);


SET search_path = radius, pg_catalog;

--
-- Name: radacctid; Type: DEFAULT; Schema: radius; Owner: nav
--

ALTER TABLE ONLY radiusacct ALTER COLUMN radacctid SET DEFAULT nextval('radiusacct_radacctid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: radius; Owner: nav
--

ALTER TABLE ONLY radiuslog ALTER COLUMN id SET DEFAULT nextval('radiuslog_id_seq'::regclass);


SET search_path = arnold, pg_catalog;

--
-- Data for Name: block; Type: TABLE DATA; Schema: arnold; Owner: nav
--

COPY block (blockid, blocktitle, blockdesc, mailfile, reasonid, determined, incremental, blocktime, active, lastedited, lastedituser, inputfile, activeonvlans, detainmenttype, quarantineid) FROM stdin;
\.


--
-- Name: block_blockid_seq; Type: SEQUENCE SET; Schema: arnold; Owner: nav
--

SELECT pg_catalog.setval('block_blockid_seq', 1, false);


--
-- Data for Name: blocked_reason; Type: TABLE DATA; Schema: arnold; Owner: nav
--

COPY blocked_reason (blocked_reasonid, name, comment) FROM stdin;
\.


--
-- Name: blocked_reason_blocked_reasonid_seq; Type: SEQUENCE SET; Schema: arnold; Owner: nav
--

SELECT pg_catalog.setval('blocked_reason_blocked_reasonid_seq', 1, false);


--
-- Data for Name: event; Type: TABLE DATA; Schema: arnold; Owner: nav
--

COPY event (eventid, identityid, event_comment, blocked_status, blocked_reasonid, eventtime, autoenablestep, username) FROM stdin;
\.


--
-- Name: event_eventid_seq; Type: SEQUENCE SET; Schema: arnold; Owner: nav
--

SELECT pg_catalog.setval('event_eventid_seq', 1, false);


--
-- Data for Name: identity; Type: TABLE DATA; Schema: arnold; Owner: nav
--

COPY identity (identityid, mac, blocked_status, blocked_reasonid, swportid, ip, dns, netbios, starttime, lastchanged, autoenable, autoenablestep, mail, orgid, determined, fromvlan, tovlan, textual_interface) FROM stdin;
\.


--
-- Name: identity_identityid_seq; Type: SEQUENCE SET; Schema: arnold; Owner: nav
--

SELECT pg_catalog.setval('identity_identityid_seq', 1, false);


--
-- Data for Name: quarantine_vlans; Type: TABLE DATA; Schema: arnold; Owner: nav
--

COPY quarantine_vlans (quarantineid, vlan, description) FROM stdin;
\.


--
-- Name: quarantine_vlans_quarantineid_seq; Type: SEQUENCE SET; Schema: arnold; Owner: nav
--

SELECT pg_catalog.setval('quarantine_vlans_quarantineid_seq', 1, false);


SET search_path = logger, pg_catalog;

--
-- Data for Name: category; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY category (category) FROM stdin;
\.


--
-- Data for Name: errorerror; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY errorerror (id, message) FROM stdin;
\.


--
-- Name: errorerror_id_seq; Type: SEQUENCE SET; Schema: logger; Owner: nav
--

SELECT pg_catalog.setval('errorerror_id_seq', 1, false);


--
-- Data for Name: log_message; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY log_message (id, "time", origin, newpriority, type, message) FROM stdin;
\.


--
-- Name: log_message_id_seq; Type: SEQUENCE SET; Schema: logger; Owner: nav
--

SELECT pg_catalog.setval('log_message_id_seq', 1, false);


--
-- Data for Name: log_message_type; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY log_message_type (type, priority, facility, mnemonic) FROM stdin;
\.


--
-- Name: log_message_type_type_seq; Type: SEQUENCE SET; Schema: logger; Owner: nav
--

SELECT pg_catalog.setval('log_message_type_type_seq', 1, false);


--
-- Data for Name: origin; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY origin (origin, name, category) FROM stdin;
\.


--
-- Name: origin_origin_seq; Type: SEQUENCE SET; Schema: logger; Owner: nav
--

SELECT pg_catalog.setval('origin_origin_seq', 1, false);


--
-- Data for Name: priority; Type: TABLE DATA; Schema: logger; Owner: nav
--

COPY priority (priority, keyword, description) FROM stdin;
0	emergencies	System unusable
1	alerts	Immediate action needed
2	critical	Critical conditions
3	errors	Error conditions
4	warnings	Warning conditions
5	notifications	Normal but significant condition
6	informational	Informational messages only
7	debugging	Debugging messages
\.


SET search_path = manage, pg_catalog;

--
-- Data for Name: adjacency_candidate; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY adjacency_candidate (adjacency_candidateid, netboxid, interfaceid, to_netboxid, to_interfaceid, source, misscnt) FROM stdin;
3	3	484	2	329	cdp	0
4	3	519	2	\N	cam	0
5	3	482	2	327	cdp	0
6	3	481	2	326	cdp	0
7	2	326	3	481	lldp	0
8	2	447	3	\N	cam	0
10	2	327	3	482	lldp	0
11	2	329	3	484	lldp	0
12	2	329	3	484	cdp	0
13	2	327	3	482	cdp	0
14	2	326	3	481	cdp	0
\.


--
-- Name: adjacency_candidate_adjacency_candidateid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('adjacency_candidate_adjacency_candidateid_seq', 23, true);


--
-- Data for Name: alerthist; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alerthist (alerthistid, source, deviceid, netboxid, subid, start_time, end_time, eventtypeid, alerttypeid, value, severity) FROM stdin;
\.


--
-- Data for Name: alerthist_ack; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alerthist_ack (alert_id, account_id, comment, date) FROM stdin;
\.


--
-- Name: alerthist_alerthistid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alerthist_alerthistid_seq', 1, false);


--
-- Data for Name: alerthistmsg; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alerthistmsg (id, alerthistid, state, msgtype, language, msg) FROM stdin;
\.


--
-- Name: alerthistmsg_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alerthistmsg_id_seq', 1, false);


--
-- Data for Name: alerthistvar; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alerthistvar (id, alerthistid, state, var, val) FROM stdin;
\.


--
-- Name: alerthistvar_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alerthistvar_id_seq', 1, false);


--
-- Data for Name: alertq; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alertq (alertqid, source, deviceid, netboxid, subid, "time", eventtypeid, alerttypeid, state, value, severity, alerthistid) FROM stdin;
\.


--
-- Name: alertq_alertqid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alertq_alertqid_seq', 1, false);


--
-- Data for Name: alertqmsg; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alertqmsg (id, alertqid, msgtype, language, msg) FROM stdin;
\.


--
-- Name: alertqmsg_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alertqmsg_id_seq', 1, false);


--
-- Data for Name: alertqvar; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alertqvar (id, alertqid, var, val) FROM stdin;
\.


--
-- Name: alertqvar_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alertqvar_id_seq', 1, false);


--
-- Data for Name: alerttype; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY alerttype (alerttypeid, eventtypeid, alerttype, alerttypedesc) FROM stdin;
1	boxState	boxDownWarning	Warning sent before declaring the box down.
2	boxState	boxShadowWarning	Warning sent before declaring the box in shadow.
3	boxState	boxDown	Box declared down.
4	boxState	boxUp	Box declared up.
5	boxState	boxShadow	Box declared down, but is in shadow.
6	boxState	boxSunny	Box declared up from a previous shadow state.
7	moduleState	moduleDownWarning	Warning sent before declaring the module down.
8	moduleState	moduleDown	Module declared down.
9	moduleState	moduleUp	Module declared up.
10	serviceState	httpDown	http service not responding.
11	serviceState	httpUp	http service responding.
12	maintenanceState	onMaintenance	Box put on maintenance.
13	maintenanceState	offMaintenance	Box taken off maintenance.
14	thresholdState	exceededThreshold	Threshold exceeded.
15	thresholdState	belowThreshold	Value below threshold.
16	info	dnsMismatch	Mismatch between sysname and dnsname.
17	info	serialChanged	Serial number for the device has changed.
22	deviceState	deviceRMA	RMA event for device.
23	deviceNotice	deviceError	Error situation on device.
24	deviceNotice	deviceSwUpgrade	Software upgrade on device.
25	deviceNotice	deviceHwUpgrade	Hardware upgrade on device.
26	apState	apUp	AP associated with controller
27	apState	apDown	AP disassociated from controller
28	info	macWarning	Mac appeared on port
29	snmpAgentState	snmpAgentDown	SNMP agent is down or unreachable due to misconfiguration.
30	snmpAgentState	snmpAgentUp	SNMP agent is up.
31	psuState	psuNotOK	A PSU has entered a non-OK state
32	psuState	psuOK	A PSU has returned to an OK state
33	fanState	fanNotOK	A fan unit has entered a non-OK state
34	fanState	fanOK	A fan unit has returned to an OK state
18	boxRestart	coldStart	The IP device has coldstarted
19	boxRestart	warmStart	The IP device has warmstarted
20	deviceState	deviceInIPOperation	The device is now in operation with an active IP address
21	deviceState	deviceInStack	The device is now in operation as a chassis module
35	linkState	linkUp	Link active
36	linkState	linkDown	Link inactive
37	weathergoose_airflow	cmClimateAirflowTRAP	Climate Air Flow Sensor Trap
38	weathergoose_airflow	cmClimateAirflowCLEAR	Climate Air Flow Sensor Clear Trap
39	weathergoose_airflow	cmClimateAirflowNOTIFY	Climate Air Flow Sensor Trap
40	weathergoose_sound	cmClimateSoundTRAP	Climate Sound Sensor Trap
41	weathergoose_sound	cmClimateSoundCLEAR	Climate Sound Sensor Clear Trap
42	weathergoose_sound	cmClimateSoundNOTIFY	Climate Sound Sensor Trap
43	weathergoose_humidity	cmClimateHumidityTRAP	Climate Humidity Sensor Trap
44	weathergoose_humidity	cmClimateHumidityCLEAR	Climate Humidity Sensor Clear Trap
45	weathergoose_humidity	cmClimateHumidityNOTIFY	Climate Humidity Sensor Trap
46	weathergoose_light	cmClimateLightTRAP	Climate Light Sensor Trap
47	weathergoose_light	cmClimateLightCLEAR	Climate Light Sensor Clear Trap
48	weathergoose_light	cmClimateLightNOTIFY	Climate Light Sensor Trap
49	weathergoose_temperature	cmClimateTempCTRAP	Climate Temperature Sensor Trap
50	weathergoose_temperature	cmClimateTempCCLEAR	Climate Temperature Sensor Clear Trap
51	weathergoose_temperature	cmClimateTempCNOTIFY	Climate Temperature Sensor Trap
52	weathergoose_temperature	cmTempSensorTempCNOTIFY	Remote Temp Sensor - Temperature Trap
53	weathergoose_temperature	cmTempSensorTempCCLEAR	Remote Temp Sensor - Temperature Clear Trap
54	upsPowerState	upsOnBatteryPower	Ups running on battery power
55	upsPowerState	upsOnUtilityPower	Ups running on utility power
\.


--
-- Name: alerttype_alerttypeid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('alerttype_alerttypeid_seq', 55, true);


--
-- Data for Name: apitoken; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY apitoken (id, token, expires, client, scope) FROM stdin;
\.


--
-- Name: apitoken_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('apitoken_id_seq', 1, false);


--
-- Data for Name: arp; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY arp (arpid, netboxid, prefixid, sysname, ip, mac, start_time, end_time) FROM stdin;
226	3	\N	test-gsw.testorg.com	fe80::120e:7eff:fec6:cfc4	10:0e:7e:c6:cf:c4	2015-05-06 11:24:21.000257	infinity
227	3	\N	test-gsw.testorg.com	158.38.180.68	00:25:90:62:21:8c	2015-05-06 11:24:21.005772	infinity
228	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:171	00:17:a4:77:9c:40	2015-05-06 11:24:21.011312	infinity
229	3	\N	test-gsw.testorg.com	158.38.180.24	00:50:56:82:00:53	2015-05-06 11:24:21.016994	infinity
230	3	\N	test-gsw.testorg.com	158.38.179.78	00:05:1e:5b:b7:8f	2015-05-06 11:24:21.020897	infinity
231	3	\N	test-gsw.testorg.com	158.38.179.168	00:17:a4:77:9c:2e	2015-05-06 11:24:21.024712	infinity
232	3	\N	test-gsw.testorg.com	158.38.179.113	00:04:02:fc:55:d8	2015-05-06 11:24:21.030343	infinity
233	3	\N	test-gsw.testorg.com	158.38.180.2	00:1e:79:5d:04:00	2015-05-06 11:24:21.03405	infinity
234	3	\N	test-gsw.testorg.com	158.38.1.145	00:1e:79:5d:04:00	2015-05-06 11:24:21.037847	infinity
235	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:4c	00:50:56:82:00:4c	2015-05-06 11:24:21.041473	infinity
236	3	\N	test-gsw.testorg.com	158.38.38.4	00:15:17:bc:84:2e	2015-05-06 11:24:21.047295	infinity
237	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c0c	00:17:a4:77:9c:0c	2015-05-06 11:24:21.050969	infinity
238	3	\N	test-gsw.testorg.com	158.38.179.82	00:1e:0b:5f:e2:ae	2015-05-06 11:24:21.054643	infinity
239	3	\N	test-gsw.testorg.com	158.38.179.111	00:04:02:fc:51:96	2015-05-06 11:24:21.058205	infinity
240	3	\N	test-gsw.testorg.com	158.38.179.89	00:26:55:86:11:6e	2015-05-06 11:24:21.061712	infinity
241	3	\N	test-gsw.testorg.com	158.38.179.76	00:1b:78:6e:c0:2e	2015-05-06 11:24:21.065259	infinity
242	3	\N	test-gsw.testorg.com	fe80::215:17ff:fec4:fb8	00:15:17:c4:0f:b8	2015-05-06 11:24:21.067463	infinity
243	3	\N	test-gsw.testorg.com	158.38.180.66	00:25:90:62:21:80	2015-05-06 11:24:21.069928	infinity
244	3	\N	test-gsw.testorg.com	158.38.179.110	00:04:02:fc:46:e2	2015-05-06 11:24:21.072022	infinity
245	3	\N	test-gsw.testorg.com	158.38.179.182	00:17:a4:77:ec:3a	2015-05-06 11:24:21.074068	infinity
246	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c58	00:17:a4:77:9c:58	2015-05-06 11:24:21.076688	infinity
247	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:167	00:17:a4:77:9c:80	2015-05-06 11:24:21.078896	infinity
248	3	\N	test-gsw.testorg.com	fe80::225:90ff:fe62:2180	00:25:90:62:21:80	2015-05-06 11:24:21.084518	infinity
249	3	\N	test-gsw.testorg.com	158.38.179.77	00:1b:78:6e:c0:30	2015-05-06 11:24:21.086501	infinity
250	3	\N	test-gsw.testorg.com	2001:700:1:8::180:66	00:25:90:62:21:80	2015-05-06 11:24:21.089127	infinity
251	3	\N	test-gsw.testorg.com	158.38.180.33	00:15:17:c4:0f:b8	2015-05-06 11:24:21.091296	infinity
252	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c2e	00:17:a4:77:9c:2e	2015-05-06 11:24:21.093462	infinity
253	3	\N	test-gsw.testorg.com	158.38.179.179	00:17:a4:77:ec:36	2015-05-06 11:24:21.095681	infinity
254	3	\N	test-gsw.testorg.com	158.38.180.30	00:50:56:82:00:03	2015-05-06 11:24:21.097772	infinity
255	3	\N	test-gsw.testorg.com	2001:700:1:8::180:57	00:50:56:82:00:08	2015-05-06 11:24:21.099747	infinity
256	3	\N	test-gsw.testorg.com	158.38.179.165	00:17:a4:77:9c:00	2015-05-06 11:24:21.101702	infinity
257	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c74	00:17:a4:77:9c:74	2015-05-06 11:24:21.104344	infinity
258	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c00	00:17:a4:77:9c:00	2015-05-06 11:24:21.106419	infinity
259	3	\N	test-gsw.testorg.com	fe80::21e:79ff:fe5d:400	00:1e:79:5d:04:00	2015-05-06 11:24:21.112167	infinity
260	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:ec3a	00:17:a4:77:ec:3a	2015-05-06 11:24:21.115375	infinity
261	3	\N	test-gsw.testorg.com	2001:700:1:8::180:23	00:50:56:82:00:46	2015-05-06 11:24:21.116942	infinity
262	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:179	00:17:a4:77:ec:36	2015-05-06 11:24:21.118663	infinity
263	3	\N	test-gsw.testorg.com	158.38.180.3	00:22:55:f8:9b:2e	2015-05-06 11:24:21.12097	infinity
264	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:46	00:50:56:82:00:46	2015-05-06 11:24:21.122656	infinity
265	3	\N	test-gsw.testorg.com	158.38.179.70	00:1c:c4:15:f0:3d	2015-05-06 11:24:21.124623	infinity
266	3	\N	test-gsw.testorg.com	158.38.179.181	00:17:a4:77:9c:58	2015-05-06 11:24:21.126511	infinity
267	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:71	00:50:56:82:00:71	2015-05-06 11:24:21.12904	infinity
268	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:3	00:50:56:82:00:03	2015-05-06 11:24:21.130823	infinity
269	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:162	00:17:a4:77:9c:0c	2015-05-06 11:24:21.13284	infinity
270	3	\N	test-gsw.testorg.com	158.38.38.5	00:15:17:bc:84:2e	2015-05-06 11:24:21.134601	infinity
271	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c14	00:17:a4:77:9c:14	2015-05-06 11:24:21.136639	infinity
272	3	\N	test-gsw.testorg.com	158.38.180.65	00:25:90:62:21:82	2015-05-06 11:24:21.139777	infinity
273	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:53	00:50:56:82:00:53	2015-05-06 11:24:21.143274	infinity
274	3	\N	test-gsw.testorg.com	158.38.179.183	00:17:a4:77:9c:74	2015-05-06 11:24:21.146774	infinity
275	3	\N	test-gsw.testorg.com	158.38.38.3	00:22:55:f8:9b:2e	2015-05-06 11:24:21.150868	infinity
276	3	\N	test-gsw.testorg.com	127.0.0.12	00:00:21:00:00:00	2015-05-06 11:24:21.153993	infinity
277	3	\N	test-gsw.testorg.com	158.38.180.99	00:50:56:82:00:8b	2015-05-06 11:24:21.157419	infinity
278	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:ec36	00:17:a4:77:ec:36	2015-05-06 11:24:21.162847	infinity
279	3	\N	test-gsw.testorg.com	158.38.179.93	00:22:64:a2:38:40	2015-05-06 11:24:21.166361	infinity
280	3	\N	test-gsw.testorg.com	158.38.179.83	00:1e:0b:5f:d2:fa	2015-05-06 11:24:21.169916	infinity
281	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:ec46	00:17:a4:77:ec:46	2015-05-06 11:24:21.173694	infinity
282	3	\N	test-gsw.testorg.com	158.38.180.7	00:0c:29:59:26:e2	2015-05-06 11:24:21.177306	infinity
283	3	\N	test-gsw.testorg.com	2001:700:1:8::180:65	00:25:90:62:21:82	2015-05-06 11:24:21.180961	infinity
284	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:165	00:17:a4:77:9c:00	2015-05-06 11:24:21.184464	infinity
285	3	\N	test-gsw.testorg.com	2001:700:1:f03::1	10:0e:7e:c6:cf:c4	2015-05-06 11:24:21.188187	infinity
286	3	\N	test-gsw.testorg.com	158.38.180.69	00:25:90:62:21:be	2015-05-06 11:24:21.191686	infinity
287	3	\N	test-gsw.testorg.com	158.38.179.166	00:17:a4:77:9c:14	2015-05-06 11:24:21.19543	infinity
288	3	\N	test-gsw.testorg.com	158.38.0.1	00:22:55:f8:9b:2e	2015-05-06 11:24:21.204515	infinity
289	3	\N	test-gsw.testorg.com	158.38.179.84	00:23:7d:a2:78:c2	2015-05-06 11:24:21.208122	infinity
290	3	\N	test-gsw.testorg.com	2001:700:1:8::180:30	00:50:56:82:00:03	2015-05-06 11:24:21.221134	infinity
291	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c40	00:17:a4:77:9c:40	2015-05-06 11:24:21.226675	infinity
292	3	\N	test-gsw.testorg.com	158.38.179.95	00:23:7d:30:28:d8	2015-05-06 11:24:21.23047	infinity
293	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:183	00:17:a4:77:9c:74	2015-05-06 11:24:21.236442	infinity
294	3	\N	test-gsw.testorg.com	2001:700:1:8::180:64	00:25:90:62:21:b8	2015-05-06 11:24:21.241164	infinity
295	3	\N	test-gsw.testorg.com	158.38.38.1	00:00:5e:00:01:83	2015-05-06 11:24:21.244962	infinity
296	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:ec22	00:17:a4:77:ec:22	2015-05-06 11:24:21.248992	infinity
297	3	\N	test-gsw.testorg.com	158.38.179.162	00:17:a4:77:9c:0c	2015-05-06 11:24:21.253708	infinity
298	3	\N	test-gsw.testorg.com	158.38.180.20	00:50:56:b5:31:71	2015-05-06 11:24:21.256702	infinity
299	3	\N	test-gsw.testorg.com	158.38.180.40	00:50:56:82:00:71	2015-05-06 11:24:21.258946	infinity
300	3	\N	test-gsw.testorg.com	158.38.179.94	00:22:64:a0:b6:d0	2015-05-06 11:24:21.261343	infinity
301	3	\N	test-gsw.testorg.com	158.38.179.131	00:22:55:f8:9b:2e	2015-05-06 11:24:21.263492	infinity
302	3	\N	test-gsw.testorg.com	158.38.38.6	e8:39:35:20:30:2f	2015-05-06 11:24:21.265696	infinity
303	3	\N	test-gsw.testorg.com	158.38.38.2	00:1e:79:5d:04:00	2015-05-06 11:24:21.26861	infinity
304	3	\N	test-gsw.testorg.com	158.38.180.47	00:50:56:82:00:4c	2015-05-06 11:24:21.270798	infinity
305	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:26	00:50:56:82:00:26	2015-05-06 11:24:21.272627	infinity
306	3	\N	test-gsw.testorg.com	2001:700:1:8::180:33	00:15:17:c4:0f:b8	2015-05-06 11:24:21.27518	infinity
307	3	\N	test-gsw.testorg.com	158.38.179.2	00:1e:79:5d:04:00	2015-05-06 11:24:21.277546	infinity
308	3	\N	test-gsw.testorg.com	2001:700:0:8000::1	00:1c:f9:b2:84:00	2015-05-06 11:24:21.281617	infinity
309	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:8	00:50:56:82:00:08	2015-05-06 11:24:21.28389	infinity
310	3	\N	test-gsw.testorg.com	158.38.180.250	00:50:56:82:00:c7	2015-05-06 11:24:21.286222	infinity
311	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:170	00:17:a4:77:ec:22	2015-05-06 11:24:21.288482	infinity
312	3	\N	test-gsw.testorg.com	2001:700:1:8::180:241	00:50:56:82:00:26	2015-05-06 11:24:21.292256	infinity
313	3	\N	test-gsw.testorg.com	158.38.180.242	00:50:56:82:00:27	2015-05-06 11:24:21.298084	infinity
314	3	\N	test-gsw.testorg.com	2001:700:1:8::180:100	00:50:56:82:00:2a	2015-05-06 11:24:21.302606	infinity
315	3	\N	test-gsw.testorg.com	158.38.179.86	00:1f:29:6a:44:8c	2015-05-06 11:24:21.306365	infinity
316	3	\N	test-gsw.testorg.com	158.38.179.73	00:1b:78:6e:e0:52	2015-05-06 11:24:21.310527	infinity
317	3	\N	test-gsw.testorg.com	158.38.179.184	00:30:48:bf:2e:40	2015-05-06 11:24:21.314559	infinity
318	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:166	00:17:a4:77:9c:14	2015-05-06 11:24:21.318626	infinity
319	3	\N	test-gsw.testorg.com	158.38.179.132	00:0c:29:80:c3:5a	2015-05-06 11:24:21.324621	infinity
320	3	\N	test-gsw.testorg.com	158.38.179.164	00:17:a4:77:ec:46	2015-05-06 11:24:21.328703	infinity
321	3	\N	test-gsw.testorg.com	158.38.179.170	00:17:a4:77:ec:22	2015-05-06 11:24:21.332601	infinity
322	3	\N	test-gsw.testorg.com	fe80::225:90ff:fe62:2182	00:25:90:62:21:82	2015-05-06 11:24:21.339961	infinity
323	3	\N	test-gsw.testorg.com	158.38.179.92	00:1f:29:68:17:d2	2015-05-06 11:24:21.344738	infinity
324	3	\N	test-gsw.testorg.com	158.38.179.72	00:1b:78:6e:c0:22	2015-05-06 11:24:21.349559	infinity
325	3	\N	test-gsw.testorg.com	158.38.180.70	00:25:90:62:21:90	2015-05-06 11:24:21.356101	infinity
326	3	\N	test-gsw.testorg.com	158.38.180.29	e8:39:35:e8:0e:b9	2015-05-06 11:24:21.361026	infinity
327	3	\N	test-gsw.testorg.com	158.38.179.74	00:05:1e:5c:0b:b1	2015-05-06 11:24:21.363762	infinity
328	3	\N	test-gsw.testorg.com	2001:700:1:8::180:24	00:50:56:82:00:53	2015-05-06 11:24:21.366565	infinity
329	3	\N	test-gsw.testorg.com	158.38.179.91	00:1f:29:68:07:d8	2015-05-06 11:24:21.36888	infinity
330	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:2a	00:50:56:82:00:2a	2015-05-06 11:24:21.371099	infinity
331	3	\N	test-gsw.testorg.com	158.38.179.96	00:22:64:a2:38:3a	2015-05-06 11:24:21.374463	infinity
332	3	\N	test-gsw.testorg.com	158.38.234.6	00:22:55:f8:9b:2e	2015-05-06 11:24:21.376799	infinity
333	3	\N	test-gsw.testorg.com	fe80::217:a4ff:fe77:9c80	00:17:a4:77:9c:80	2015-05-06 11:24:21.379097	infinity
334	3	\N	test-gsw.testorg.com	158.38.179.85	00:1f:29:6a:64:e0	2015-05-06 11:24:21.381428	infinity
335	3	\N	test-gsw.testorg.com	158.38.179.1	00:00:5e:00:01:02	2015-05-06 11:24:21.383689	infinity
336	3	\N	test-gsw.testorg.com	158.38.179.87	00:1f:29:68:f6:a4	2015-05-06 11:24:21.386272	infinity
337	3	\N	test-gsw.testorg.com	158.38.179.3	00:22:55:f8:9b:2e	2015-05-06 11:24:21.389094	infinity
338	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:182	00:17:a4:77:ec:3a	2015-05-06 11:24:21.392043	infinity
339	3	\N	test-gsw.testorg.com	158.38.179.71	00:1c:c4:15:b0:43	2015-05-06 11:24:21.394533	infinity
340	3	\N	test-gsw.testorg.com	158.38.179.171	00:17:a4:77:9c:40	2015-05-06 11:24:21.39673	infinity
341	3	\N	test-gsw.testorg.com	2001:700:1:8::180:40	00:50:56:82:00:71	2015-05-06 11:24:21.398992	infinity
342	3	\N	test-gsw.testorg.com	158.38.179.129	00:00:5e:00:01:03	2015-05-06 11:24:21.402756	infinity
343	3	\N	test-gsw.testorg.com	158.38.180.241	00:50:56:82:00:26	2015-05-06 11:24:21.406754	infinity
344	3	\N	test-gsw.testorg.com	128.39.70.10	00:22:55:f8:9b:2e	2015-05-06 11:24:21.413131	infinity
345	3	\N	test-gsw.testorg.com	158.38.179.90	00:22:64:a2:28:6a	2015-05-06 11:24:21.416883	infinity
346	3	\N	test-gsw.testorg.com	158.38.180.64	00:25:90:62:21:b8	2015-05-06 11:24:21.420757	infinity
347	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:164	00:17:a4:77:ec:46	2015-05-06 11:24:21.42482	infinity
348	3	\N	test-gsw.testorg.com	fe80::250:56ff:fe82:1d	00:50:56:82:00:1d	2015-05-06 11:24:21.429006	infinity
349	3	\N	test-gsw.testorg.com	fe80::225:90ff:fe62:21b8	00:25:90:62:21:b8	2015-05-06 11:24:21.433292	infinity
350	3	\N	test-gsw.testorg.com	158.38.180.57	00:50:56:82:00:08	2015-05-06 11:24:21.438791	infinity
351	3	\N	test-gsw.testorg.com	158.38.179.167	00:17:a4:77:9c:80	2015-05-06 11:24:21.442967	infinity
352	3	\N	test-gsw.testorg.com	158.38.234.5	10:0e:7e:c6:cf:c4	2015-05-06 11:24:21.44692	infinity
353	3	\N	test-gsw.testorg.com	158.38.180.1	00:00:5e:00:01:04	2015-05-06 11:24:21.450992	infinity
354	3	\N	test-gsw.testorg.com	158.38.180.23	00:50:56:82:00:46	2015-05-06 11:24:21.454944	infinity
355	3	\N	test-gsw.testorg.com	158.38.180.100	00:50:56:82:00:2a	2015-05-06 11:24:21.458994	infinity
356	3	\N	test-gsw.testorg.com	158.38.179.130	00:1e:79:5d:04:00	2015-05-06 11:24:21.466396	infinity
357	3	\N	test-gsw.testorg.com	128.39.70.9	00:1c:f9:b2:84:00	2015-05-06 11:24:21.470341	infinity
358	3	\N	test-gsw.testorg.com	2001:700:1:8::180:32	00:50:56:82:00:1d	2015-05-06 11:24:21.472705	infinity
359	3	\N	test-gsw.testorg.com	2001:700:1:8::180:47	00:50:56:82:00:4c	2015-05-06 11:24:21.47513	infinity
360	3	\N	test-gsw.testorg.com	158.38.179.88	00:1f:29:68:07:e6	2015-05-06 11:24:21.477679	infinity
361	3	\N	test-gsw.testorg.com	158.38.0.2	58:8d:09:7e:19:7f	2015-05-06 11:24:21.480534	infinity
362	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:181	00:17:a4:77:9c:58	2015-05-06 11:24:21.48383	infinity
363	3	\N	test-gsw.testorg.com	158.38.180.32	00:50:56:82:00:1d	2015-05-06 11:24:21.486043	infinity
364	3	\N	test-gsw.testorg.com	2001:700:0:4529::179:168	00:17:a4:77:9c:2e	2015-05-06 11:24:21.488432	infinity
365	3	\N	test-gsw.testorg.com	158.38.180.13	00:0c:29:83:dc:24	2015-05-06 11:24:21.491035	infinity
\.


--
-- Name: arp_arpid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('arp_arpid_seq', 590, true);


--
-- Data for Name: cabling; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY cabling (cablingid, roomid, jack, building, targetroom, descr, category) FROM stdin;
\.


--
-- Name: cabling_cablingid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('cabling_cablingid_seq', 1, false);


--
-- Data for Name: cam; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY cam (camid, netboxid, sysname, ifindex, module, port, mac, start_time, end_time, misscnt) FROM stdin;
1	2	test-sw.testorg.com	108		Te4/4	00:0c:29:83:dc:24	2015-05-06 10:40:22.194997	infinity	0
2	2	test-sw.testorg.com	57		Gi3/1	00:05:1e:5c:0b:b1	2015-05-06 10:40:22.196231	infinity	0
3	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:d3	2015-05-06 10:40:22.197804	infinity	0
4	2	test-sw.testorg.com	48		Gi2/40	e8:39:35:e8:0e:b9	2015-05-06 10:40:22.198547	infinity	0
5	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:03	2015-05-06 10:40:22.199313	infinity	0
6	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:ec:46	2015-05-06 10:40:22.200225	infinity	0
7	2	test-sw.testorg.com	90		Gi3/34	00:1d:d8:b7:1e:73	2015-05-06 10:40:22.201041	infinity	0
8	2	test-sw.testorg.com	108		Te4/4	00:0c:29:a3:90:61	2015-05-06 10:40:22.201838	infinity	0
9	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:d8	2015-05-06 10:40:22.20263	infinity	0
10	2	test-sw.testorg.com	45		Gi2/37	2c:41:38:88:66:69	2015-05-06 10:40:22.203484	infinity	0
11	2	test-sw.testorg.com	108		Te4/4	00:0c:29:80:c3:5a	2015-05-06 10:40:22.204387	infinity	0
12	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:2e	2015-05-06 10:40:22.205401	infinity	0
13	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:40	2015-05-06 10:40:22.207541	infinity	0
14	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:0c	2015-05-06 10:40:22.208512	infinity	0
645	2	test-sw.testorg.com	57		Gi3/1	00:1c:c4:15:f0:3d	2015-05-06 11:30:48.186911	infinity	0
16	2	test-sw.testorg.com	105		Te4/1	00:05:73:a0:00:0b	2015-05-06 10:40:22.210516	infinity	0
17	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:42	2015-05-06 10:40:22.211544	infinity	0
18	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:53	2015-05-06 10:40:22.212543	infinity	0
19	2	test-sw.testorg.com	90		Gi3/34	10:60:4b:ab:cc:fe	2015-05-06 10:40:22.214671	infinity	0
20	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:08	2015-05-06 10:40:22.215598	infinity	0
21	2	test-sw.testorg.com	108		Te4/4	00:0c:29:8f:fe:21	2015-05-06 10:40:22.216602	infinity	0
22	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:32	2015-05-06 10:40:22.230803	infinity	0
23	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:58	2015-05-06 10:40:22.231462	infinity	0
24	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:0d	2015-05-06 10:40:22.231942	infinity	0
25	2	test-sw.testorg.com	46		Gi2/38	2c:41:38:88:66:6a	2015-05-06 10:40:22.232507	infinity	0
26	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:36	2015-05-06 10:40:22.23297	infinity	0
27	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:41	2015-05-06 10:40:22.233474	infinity	0
28	2	test-sw.testorg.com	60		Gi3/4	68:b5:99:c0:16:d0	2015-05-06 10:40:22.233911	infinity	0
29	2	test-sw.testorg.com	43		Gi2/35	e8:39:35:20:30:2f	2015-05-06 10:40:22.234435	infinity	0
30	2	test-sw.testorg.com	90		Gi3/34	10:60:4b:ab:5b:c6	2015-05-06 10:40:22.234848	infinity	0
31	2	test-sw.testorg.com	85		Gi3/29	d4:85:64:5e:6c:80	2015-05-06 10:40:22.235314	infinity	0
32	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:ec:36	2015-05-06 10:40:22.235759	infinity	0
33	2	test-sw.testorg.com	57		Gi3/1	00:1b:78:6e:c0:22	2015-05-06 10:40:22.236215	infinity	0
34	2	test-sw.testorg.com	90		Gi3/34	10:60:4b:ab:fa:8e	2015-05-06 10:40:22.236654	infinity	0
35	2	test-sw.testorg.com	75		Gi3/19	3c:4a:92:e2:2b:74	2015-05-06 10:40:22.237054	infinity	0
36	2	test-sw.testorg.com	108		Te4/4	00:0c:29:95:b9:76	2015-05-06 10:40:22.23753	infinity	0
37	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:59	2015-05-06 10:40:22.237985	infinity	0
38	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:ec:3a	2015-05-06 10:40:22.238384	infinity	0
39	2	test-sw.testorg.com	59		Gi3/3	00:04:02:fc:46:e2	2015-05-06 10:40:22.2389	infinity	0
40	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:02	2015-05-06 10:40:22.239288	infinity	0
41	2	test-sw.testorg.com	108		Te4/4	00:0c:29:59:26:e2	2015-05-06 10:40:22.239834	infinity	0
42	2	test-sw.testorg.com	108		Te4/4	00:50:56:b5:31:71	2015-05-06 10:40:22.240221	infinity	0
43	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:4c	2015-05-06 10:40:22.240754	infinity	0
44	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:46	2015-05-06 10:40:22.241208	infinity	0
45	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:ed	2015-05-06 10:40:22.241588	infinity	0
46	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:57	2015-05-06 10:40:22.242072	infinity	0
47	2	test-sw.testorg.com	105		Te4/1	00:05:73:a0:00:06	2015-05-06 10:40:22.242453	infinity	0
48	2	test-sw.testorg.com	108		Te4/4	00:0c:29:01:3a:7d	2015-05-06 10:40:22.242909	infinity	0
49	2	test-sw.testorg.com	105		Te4/1	00:00:5e:00:01:08	2015-05-06 10:40:22.243357	infinity	0
50	2	test-sw.testorg.com	90		Gi3/34	00:1d:d8:b7:1e:71	2015-05-06 10:40:22.243744	infinity	0
51	2	test-sw.testorg.com	70		Gi3/14	d8:d3:85:a9:be:80	2015-05-06 10:40:22.244222	infinity	0
52	2	test-sw.testorg.com	57		Gi3/1	00:1b:78:6e:c0:30	2015-05-06 10:40:22.244655	infinity	0
53	2	test-sw.testorg.com	108		Te4/4	00:0c:29:f0:da:ad	2015-05-06 10:40:22.245053	infinity	0
54	2	test-sw.testorg.com	79		Gi3/23	3c:4a:92:e4:d3:90	2015-05-06 10:40:22.245561	infinity	0
55	2	test-sw.testorg.com	105		Te4/1	00:00:5e:00:01:07	2015-05-06 10:40:22.245948	infinity	0
56	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:c7	2015-05-06 10:40:22.246431	infinity	0
57	2	test-sw.testorg.com	62		Gi3/6	00:04:02:fc:55:d8	2015-05-06 10:40:22.246862	infinity	0
58	2	test-sw.testorg.com	57		Gi3/1	00:1b:78:6e:e0:52	2015-05-06 10:40:22.247251	infinity	0
59	2	test-sw.testorg.com	108		Te4/4	00:0c:29:f8:2a:86	2015-05-06 10:40:22.247701	infinity	0
60	2	test-sw.testorg.com	108		Te4/4	00:0c:29:c1:9e:0e	2015-05-06 10:40:22.248139	infinity	0
61	2	test-sw.testorg.com	69		Gi3/13	d4:85:64:60:3c:94	2015-05-06 10:40:22.248649	infinity	0
62	2	test-sw.testorg.com	108		Te4/4	00:0c:29:53:ed:82	2015-05-06 10:40:22.252155	infinity	0
63	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:8b	2015-05-06 10:40:22.252764	infinity	0
64	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:74	2015-05-06 10:40:22.25323	infinity	0
65	2	test-sw.testorg.com	73		Gi3/17	68:b5:99:b5:b9:10	2015-05-06 10:40:22.253768	infinity	0
66	2	test-sw.testorg.com	108		Te4/4	00:0c:29:b7:06:cc	2015-05-06 10:40:22.254185	infinity	0
67	2	test-sw.testorg.com	35		Gi2/27	00:25:90:62:21:be	2015-05-06 10:40:22.254645	infinity	0
68	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:27	2015-05-06 10:40:22.255085	infinity	0
70	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:ec:22	2015-05-06 10:40:22.255973	infinity	0
71	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:00	2015-05-06 10:40:22.25637	infinity	0
72	2	test-sw.testorg.com	105		Te4/1	00:05:73:a0:00:07	2015-05-06 10:40:22.256885	infinity	0
74	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:26	2015-05-06 10:40:22.257806	infinity	0
75	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:00	2015-05-06 10:40:22.258269	infinity	0
69	2	test-sw.testorg.com	57		Gi3/1	00:22:64:a2:28:6a	2015-05-06 10:40:22.255472	infinity	0
76	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:2a	2015-05-06 10:40:22.258659	infinity	0
77	2	test-sw.testorg.com	90		Gi3/34	00:1d:d8:b7:1e:72	2015-05-06 10:40:22.259264	infinity	0
78	2	test-sw.testorg.com	57		Gi3/1	00:1b:78:6e:c0:2e	2015-05-06 10:40:22.259674	infinity	0
79	2	test-sw.testorg.com	108		Te4/4	00:0c:29:e4:b7:e2	2015-05-06 10:40:22.260171	infinity	0
80	2	test-sw.testorg.com	90		Gi3/34	00:15:5d:09:df:14	2015-05-06 10:40:22.260564	infinity	0
81	2	test-sw.testorg.com	29		Gi2/21	00:25:90:6d:b7:83	2015-05-06 10:40:22.261022	infinity	0
646	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:68:17:d2	2015-05-06 11:30:48.187919	infinity	0
83	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:07	2015-05-06 10:40:22.261852	infinity	0
84	2	test-sw.testorg.com	105		Te4/1	00:00:5e:00:01:06	2015-05-06 10:40:22.262311	infinity	0
85	2	test-sw.testorg.com	27		Gi2/19	00:25:90:6d:b7:81	2015-05-06 10:40:22.262737	infinity	0
86	2	test-sw.testorg.com	77		Gi3/21	d8:d3:85:a9:be:78	2015-05-06 10:40:22.263124	infinity	0
87	2	test-sw.testorg.com	83		Gi3/27	d4:85:64:5e:6c:82	2015-05-06 10:40:22.263661	infinity	0
88	2	test-sw.testorg.com	105		Te4/1	00:1c:f9:b2:84:00	2015-05-06 10:40:22.264059	infinity	0
89	2	test-sw.testorg.com	28		Gi2/20	00:25:90:6d:b7:9a	2015-05-06 10:40:22.264572	infinity	0
90	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:ec	2015-05-06 10:40:22.265166	infinity	0
91	2	test-sw.testorg.com	105		Te4/1	00:00:5e:00:01:0b	2015-05-06 10:40:22.266073	infinity	0
92	2	test-sw.testorg.com	31		Gi2/23	00:25:90:62:21:8c	2015-05-06 10:40:22.267039	infinity	0
93	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:1d	2015-05-06 10:40:22.26792	infinity	0
94	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:14	2015-05-06 10:40:22.268939	infinity	0
1539	2	test-sw.testorg.com	133		Po5	00:1c:0f:5f:c8:00	2015-05-06 11:48:35.406465	infinity	0
96	2	test-sw.testorg.com	105		Te4/1	00:05:73:a0:00:0f	2015-05-06 10:40:22.270705	infinity	0
647	2	test-sw.testorg.com	57		Gi3/1	00:23:7d:a2:78:c2	2015-05-06 11:30:48.188432	infinity	0
98	2	test-sw.testorg.com	39		Gi2/31	00:25:90:62:21:90	2015-05-06 10:40:22.277116	infinity	0
99	2	test-sw.testorg.com	51		Gi2/43	00:04:02:fc:51:96	2015-05-06 10:40:22.277563	infinity	0
100	2	test-sw.testorg.com	49		Gi2/41	e8:39:35:e8:0e:ba	2015-05-06 10:40:22.27799	infinity	0
648	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:6a:64:e0	2015-05-06 11:30:48.188927	infinity	0
102	2	test-sw.testorg.com	108		Te4/4	00:17:a4:77:9c:80	2015-05-06 10:40:22.278868	infinity	0
103	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:71	2015-05-06 10:40:22.279371	infinity	0
104	2	test-sw.testorg.com	108		Te4/4	00:0c:29:62:4f:9d	2015-05-06 10:40:22.279767	infinity	0
105	2	test-sw.testorg.com	108		Te4/4	00:50:56:82:00:26	2015-05-06 10:40:22.280348	infinity	0
649	2	test-sw.testorg.com	57		Gi3/1	00:1e:0b:5f:e2:ae	2015-05-06 11:30:48.189401	infinity	0
650	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:68:f6:a4	2015-05-06 11:30:48.18987	infinity	0
651	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:68:07:d8	2015-05-06 11:30:48.190335	infinity	0
652	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:6a:44:8c	2015-05-06 11:30:48.190894	infinity	0
653	2	test-sw.testorg.com	57		Gi3/1	00:1f:29:68:07:e6	2015-05-06 11:30:48.191484	infinity	0
654	2	test-sw.testorg.com	57		Gi3/1	00:05:1e:5b:b7:8f	2015-05-06 11:30:48.191989	infinity	0
655	2	test-sw.testorg.com	57		Gi3/1	00:23:7d:30:28:d8	2015-05-06 11:30:48.192444	infinity	0
73	2	test-sw.testorg.com	58		Gi3/2	00:1c:c4:15:b0:43	2015-05-06 10:40:22.257325	infinity	0
101	2	test-sw.testorg.com	57		Gi3/1	00:22:64:a2:38:3a	2015-05-06 10:40:22.278445	infinity	0
1540	2	test-sw.testorg.com	133		Po5	44:1e:a1:4e:9a:cc	2015-05-06 11:48:35.407757	infinity	0
95	2	test-sw.testorg.com	130		Po2	00:22:55:f8:9b:2e	2015-05-06 10:40:22.270012	2015-05-06 11:30:48.203534	\N
1543	2	test-sw.testorg.com	133		Po5	cc:5d:4e:39:60:b2	2015-05-06 11:48:35.411142	infinity	0
1545	2	test-sw.testorg.com	133		Po5	3c:97:0e:68:3a:a7	2015-05-06 11:48:35.41288	infinity	0
1547	2	test-sw.testorg.com	133		Po5	00:20:4a:e9:99:16	2015-05-06 11:48:35.414762	infinity	0
1548	2	test-sw.testorg.com	133		Po5	00:05:73:a0:00:02	2015-05-06 11:48:35.415703	infinity	0
1549	2	test-sw.testorg.com	133		Po5	f0:de:f1:93:14:20	2015-05-06 11:48:35.416568	infinity	0
1550	2	test-sw.testorg.com	133		Po5	00:14:5e:dc:00:4f	2015-05-06 11:48:35.417447	infinity	0
1552	2	test-sw.testorg.com	133		Po5	00:00:5e:00:01:83	2015-05-06 11:48:35.419294	infinity	0
1553	2	test-sw.testorg.com	133		Po5	9c:8e:99:2c:e0:00	2015-05-06 11:48:35.420223	infinity	0
1554	2	test-sw.testorg.com	133		Po5	00:1a:64:9d:49:11	2015-05-06 11:48:35.421157	infinity	0
1555	2	test-sw.testorg.com	133		Po5	00:08:9b:c4:75:f7	2015-05-06 11:48:35.422027	infinity	0
1557	2	test-sw.testorg.com	133		Po5	f8:c0:01:c9:1d:81	2015-05-06 11:48:35.42371	infinity	0
1558	2	test-sw.testorg.com	133		Po5	00:15:17:c4:0f:b8	2015-05-06 11:48:35.424542	infinity	0
1559	2	test-sw.testorg.com	133		Po5	00:8c:fa:c8:61:16	2015-05-06 11:48:35.42538	infinity	0
1560	2	test-sw.testorg.com	133		Po5	d4:be:d9:a6:29:80	2015-05-06 11:48:35.42621	infinity	0
1561	2	test-sw.testorg.com	133		Po5	00:1a:64:94:e4:c8	2015-05-06 11:48:35.427047	infinity	0
1562	2	test-sw.testorg.com	133		Po5	00:15:5d:3e:99:04	2015-05-06 11:48:35.42788	infinity	0
1563	2	test-sw.testorg.com	133		Po5	cc:e1:7f:f5:3b:56	2015-05-06 11:48:35.428699	infinity	0
1542	2	test-sw.testorg.com	133		Po5	00:50:b6:7c:89:5f	2015-05-06 11:48:35.410203	2015-05-06 12:18:35.5147	\N
1565	2	test-sw.testorg.com	133		Po5	9c:8e:99:25:5e:dc	2015-05-06 11:48:35.430201	infinity	0
1566	2	test-sw.testorg.com	133		Po5	00:0d:60:1c:ce:6e	2015-05-06 11:48:35.43089	infinity	0
1567	2	test-sw.testorg.com	133		Po5	40:6c:8f:04:30:32	2015-05-06 11:48:35.431574	infinity	0
1568	2	test-sw.testorg.com	133		Po5	0c:4d:e9:a6:87:4d	2015-05-06 11:48:35.432267	infinity	0
1570	2	test-sw.testorg.com	133		Po5	a8:20:66:44:ca:d8	2015-05-06 11:48:35.433648	infinity	0
1571	2	test-sw.testorg.com	133		Po5	cc:5d:4e:39:66:41	2015-05-06 11:48:35.434336	infinity	0
1572	2	test-sw.testorg.com	133		Po5	00:00:5e:00:01:02	2015-05-06 11:48:35.435017	infinity	0
1573	2	test-sw.testorg.com	133		Po5	00:21:5e:42:98:8c	2015-05-06 11:48:35.435698	infinity	0
82	2	test-sw.testorg.com	57		Gi3/1	00:22:64:a0:b6:d0	2015-05-06 10:40:22.261467	infinity	0
1752	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:15:bd	2015-05-06 12:48:35.490924	infinity	0
1753	2	test-sw.testorg.com	133		Po5	00:25:90:0a:44:58	2015-05-06 12:48:35.491794	2015-05-06 13:03:35.578588	\N
1564	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:e4	2015-05-06 11:48:35.429492	2015-05-06 13:33:35.6446	1
1556	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:a7	2015-05-06 11:48:35.422874	2015-05-06 13:33:35.664929	1
1751	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:15:a4	2015-05-06 12:48:35.489759	2015-05-06 13:18:35.7071	2
1574	2	test-sw.testorg.com	133		Po5	00:14:4f:2d:91:2a	2015-05-06 11:48:35.436383	infinity	0
1575	2	test-sw.testorg.com	133		Po5	00:21:5e:f0:9d:7a	2015-05-06 11:48:35.437108	infinity	0
1576	2	test-sw.testorg.com	133		Po5	3c:07:54:66:ed:69	2015-05-06 11:48:35.43782	infinity	0
1577	2	test-sw.testorg.com	133		Po5	cc:5d:4e:39:61:bd	2015-05-06 11:48:35.438644	infinity	0
1582	2	test-sw.testorg.com	133		Po5	00:50:56:00:4a:01	2015-05-06 11:48:35.442406	infinity	0
1583	2	test-sw.testorg.com	133		Po5	b4:b5:2f:52:c0:18	2015-05-06 11:48:35.44305	infinity	0
1584	2	test-sw.testorg.com	133		Po5	54:e0:32:81:fc:81	2015-05-06 11:48:35.443689	infinity	0
1585	2	test-sw.testorg.com	133		Po5	00:25:90:85:91:83	2015-05-06 11:48:35.444333	infinity	0
1586	2	test-sw.testorg.com	133		Po5	cc:5d:4e:39:65:e8	2015-05-06 11:48:35.445044	infinity	0
1588	2	test-sw.testorg.com	133		Po5	00:15:5d:64:87:03	2015-05-06 11:48:35.446423	infinity	0
1589	2	test-sw.testorg.com	133		Po5	00:0a:5c:1e:ef:84	2015-05-06 11:48:35.447113	infinity	0
1591	2	test-sw.testorg.com	133		Po5	2c:44:fd:7a:5a:2c	2015-05-06 11:48:35.44849	infinity	0
1593	2	test-sw.testorg.com	133		Po5	00:02:55:67:0d:f5	2015-05-06 11:48:35.449903	infinity	0
1595	2	test-sw.testorg.com	133		Po5	5c:f9:dd:78:72:8a	2015-05-06 11:48:35.451354	infinity	0
1596	2	test-sw.testorg.com	133		Po5	00:05:73:a0:00:03	2015-05-06 11:48:35.452071	infinity	0
1597	2	test-sw.testorg.com	133		Po5	00:1a:64:9c:39:aa	2015-05-06 11:48:35.452808	infinity	0
1598	2	test-sw.testorg.com	133		Po5	3c:07:54:65:a4:81	2015-05-06 11:48:35.453434	infinity	0
1599	2	test-sw.testorg.com	133		Po5	00:00:5e:00:01:03	2015-05-06 11:48:35.454044	infinity	0
1600	2	test-sw.testorg.com	133		Po5	00:00:5e:00:01:04	2015-05-06 11:48:35.454651	infinity	0
1602	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:09:f5	2015-05-06 11:48:35.455972	infinity	0
1603	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0e:45	2015-05-06 11:48:35.456584	infinity	0
1631	2	test-sw.testorg.com	133		Po5	00:50:b6:5c:c0:fd	2015-05-06 11:48:35.475887	2015-05-06 12:18:35.518171	\N
1605	2	test-sw.testorg.com	133		Po5	00:25:90:62:21:b8	2015-05-06 11:48:35.45799	infinity	0
1607	2	test-sw.testorg.com	133		Po5	00:1a:64:2c:5e:cf	2015-05-06 11:48:35.459368	infinity	0
1615	2	test-sw.testorg.com	133		Po5	40:6c:8f:2d:5b:bc	2015-05-06 11:48:35.465149	2015-05-06 12:48:35.710746	\N
1610	2	test-sw.testorg.com	133		Po5	00:25:90:86:db:be	2015-05-06 11:48:35.461582	infinity	0
1612	2	test-sw.testorg.com	133		Po5	ac:16:2d:c0:63:d2	2015-05-06 11:48:35.463028	infinity	0
1613	2	test-sw.testorg.com	133		Po5	40:a8:f0:a3:4a:2c	2015-05-06 11:48:35.463727	infinity	0
1614	2	test-sw.testorg.com	133		Po5	00:04:a3:2b:6b:66	2015-05-06 11:48:35.464418	infinity	0
1616	2	test-sw.testorg.com	133		Po5	68:5b:35:80:ff:cd	2015-05-06 11:48:35.465802	infinity	0
1546	2	test-sw.testorg.com	133		Po5	08:81:f4:88:0d:ef	2015-05-06 11:48:35.413809	2015-05-06 12:48:35.549398	\N
1619	2	test-sw.testorg.com	133		Po5	cc:5d:4e:39:60:16	2015-05-06 11:48:35.467838	infinity	0
1620	2	test-sw.testorg.com	133		Po5	64:51:06:4e:61:8a	2015-05-06 11:48:35.468504	infinity	0
1621	2	test-sw.testorg.com	133		Po5	f0:de:f1:c9:91:2d	2015-05-06 11:48:35.469194	infinity	0
1608	2	test-sw.testorg.com	133		Po5	b4:b5:2f:e4:69:fc	2015-05-06 11:48:35.460081	infinity	0
1624	2	test-sw.testorg.com	133		Po5	00:25:90:62:21:80	2015-05-06 11:48:35.471196	infinity	0
1625	2	test-sw.testorg.com	133		Po5	3c:07:54:65:bd:f6	2015-05-06 11:48:35.471864	infinity	0
1627	2	test-sw.testorg.com	133		Po5	00:1a:64:9a:c8:81	2015-05-06 11:48:35.473206	infinity	0
1628	2	test-sw.testorg.com	133		Po5	d4:c9:ef:e2:80:3b	2015-05-06 11:48:35.47388	infinity	0
1629	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:09:9a	2015-05-06 11:48:35.47455	infinity	0
1630	2	test-sw.testorg.com	133		Po5	28:28:5d:bf:3a:0b	2015-05-06 11:48:35.475216	infinity	0
1609	2	test-sw.testorg.com	133		Po5	a8:5b:78:11:2b:bd	2015-05-06 11:48:35.46084	infinity	0
1632	2	test-sw.testorg.com	133		Po5	2c:59:e5:44:19:9c	2015-05-06 11:48:35.476554	infinity	0
1633	2	test-sw.testorg.com	133		Po5	3c:97:0e:b9:c7:4f	2015-05-06 11:48:35.47729	infinity	0
1634	2	test-sw.testorg.com	133		Po5	64:51:06:4f:1e:eb	2015-05-06 11:48:35.478003	infinity	0
1636	2	test-sw.testorg.com	133		Po5	00:05:73:a0:00:04	2015-05-06 11:48:35.479406	infinity	0
1637	2	test-sw.testorg.com	133		Po5	00:25:90:3d:71:b2	2015-05-06 11:48:35.480112	infinity	0
1638	2	test-sw.testorg.com	133		Po5	90:b1:1c:61:2c:93	2015-05-06 11:48:35.480848	infinity	0
1640	2	test-sw.testorg.com	133		Po5	28:94:0f:ad:e9:6f	2015-05-06 11:48:35.482279	infinity	0
1767	2	test-sw.testorg.com	133		Po5	00:16:3e:ca:a7:95	2015-05-06 13:18:35.541581	2015-05-06 13:33:35.554433	1
1642	2	test-sw.testorg.com	133		Po5	00:1e:79:5d:04:00	2015-05-06 11:48:35.483699	infinity	0
1643	2	test-sw.testorg.com	133		Po5	10:60:4b:87:bb:80	2015-05-06 11:48:35.484407	infinity	0
1644	2	test-sw.testorg.com	133		Po5	18:a9:05:52:09:74	2015-05-06 11:48:35.485133	infinity	0
1645	2	test-sw.testorg.com	133		Po5	4c:96:14:f3:aa:a0	2015-05-06 11:48:35.48587	infinity	0
1646	2	test-sw.testorg.com	133		Po5	00:11:25:ab:20:da	2015-05-06 11:48:35.486619	infinity	0
1647	2	test-sw.testorg.com	133		Po5	00:04:20:22:51:9e	2015-05-06 11:48:35.487354	infinity	0
1639	2	test-sw.testorg.com	133		Po5	28:d2:44:4f:b4:ad	2015-05-06 11:48:35.481565	2015-05-06 12:33:35.51748	\N
1578	2	test-sw.testorg.com	133		Po5	68:5b:35:b3:15:83	2015-05-06 11:48:35.439498	2015-05-06 12:33:35.617281	\N
1580	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:d3	2015-05-06 11:48:35.441111	2015-05-06 13:33:35.584498	1
1754	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0d:b0	2015-05-06 12:48:35.492679	2015-05-06 13:18:35.691827	2
1594	2	test-sw.testorg.com	133		Po5	00:1a:64:11:7a:2c	2015-05-06 11:48:35.450637	2015-05-06 13:18:35.732671	2
1755	2	test-sw.testorg.com	133		Po5	30:f7:0d:08:0a:4c	2015-05-06 12:48:35.493578	2015-05-06 13:18:35.664736	2
1601	2	test-sw.testorg.com	133		Po5	00:14:5e:cd:46:c0	2015-05-06 11:48:35.45526	2015-05-06 13:18:35.645184	2
1606	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:05:a8	2015-05-06 11:48:35.458672	2015-05-06 13:33:35.681264	1
1768	2	test-sw.testorg.com	133		Po5	00:25:64:d7:a5:83	2015-05-06 13:18:35.542292	2015-05-06 13:33:35.685926	1
1766	2	test-sw.testorg.com	133		Po5	00:24:a8:4e:85:a0	2015-05-06 13:18:35.540809	2015-05-06 13:33:35.688176	1
1765	2	test-sw.testorg.com	133		Po5	00:16:3e:07:89:fb	2015-05-06 13:18:35.539338	2015-05-06 13:33:35.708536	1
1769	2	test-sw.testorg.com	133		Po5	00:16:3e:dd:40:6a	2015-05-06 13:18:35.542967	2015-05-06 13:33:35.713033	1
1579	2	test-sw.testorg.com	133		Po5	00:15:5d:3e:99:03	2015-05-06 11:48:35.440218	infinity	0
1622	2	test-sw.testorg.com	133		Po5	d4:be:d9:a6:29:69	2015-05-06 11:48:35.46986	infinity	0
1648	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0d:b0	2015-05-06 11:48:35.488085	2015-05-06 12:03:35.528269	\N
1649	2	test-sw.testorg.com	133		Po5	28:d2:44:60:36:04	2015-05-06 11:48:35.488834	infinity	0
1650	2	test-sw.testorg.com	133		Po5	10:0e:7e:c6:cc:30	2015-05-06 11:48:35.489553	infinity	0
1651	2	test-sw.testorg.com	133		Po5	44:1e:a1:53:90:44	2015-05-06 11:48:35.490272	infinity	0
1653	2	test-sw.testorg.com	133		Po5	00:30:48:bf:2e:40	2015-05-06 11:48:35.491825	infinity	0
1654	2	test-sw.testorg.com	133		Po5	00:15:5d:64:87:1f	2015-05-06 11:48:35.492543	infinity	0
1656	2	test-sw.testorg.com	133		Po5	28:d2:44:60:31:e6	2015-05-06 11:48:35.493795	infinity	0
1544	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:09:98	2015-05-06 11:48:35.412006	infinity	0
1658	2	test-sw.testorg.com	133		Po5	28:d2:44:48:6c:1c	2015-05-06 11:48:35.495021	infinity	0
1611	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:6a	2015-05-06 11:48:35.462309	infinity	0
1618	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:7d	2015-05-06 11:48:35.46715	infinity	0
1662	2	test-sw.testorg.com	133		Po5	00:50:b6:5c:b6:d7	2015-05-06 11:48:35.497953	infinity	0
1661	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0d:e2	2015-05-06 11:48:35.497227	2015-05-06 12:18:35.589598	\N
1664	2	test-sw.testorg.com	133		Po5	6c:3b:e5:0c:43:5c	2015-05-06 11:48:35.499429	infinity	0
1665	2	test-sw.testorg.com	133		Po5	28:d2:44:60:3e:ac	2015-05-06 11:48:35.500165	infinity	0
1666	2	test-sw.testorg.com	133		Po5	00:1b:3f:f2:0a:c0	2015-05-06 11:48:35.50094	infinity	0
1667	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:09:a9	2015-05-06 11:48:35.501517	infinity	0
1668	2	test-sw.testorg.com	133		Po5	18:a9:05:52:09:7c	2015-05-06 11:48:35.502083	infinity	0
1669	2	test-sw.testorg.com	133		Po5	00:3e:e1:bf:a6:fb	2015-05-06 11:48:35.502708	infinity	0
1672	2	test-sw.testorg.com	133		Po5	00:25:90:d1:0e:bc	2015-05-06 11:48:35.504866	infinity	0
1673	2	test-sw.testorg.com	133		Po5	00:11:25:22:6d:29	2015-05-06 11:48:35.505579	infinity	0
1674	2	test-sw.testorg.com	133		Po5	00:50:b6:7b:76:4b	2015-05-06 11:48:35.506287	infinity	0
1676	2	test-sw.testorg.com	133		Po5	00:1a:64:9c:39:32	2015-05-06 11:48:35.507709	infinity	0
1677	2	test-sw.testorg.com	133		Po5	00:25:64:d7:a9:f6	2015-05-06 11:48:35.508418	infinity	0
1678	2	test-sw.testorg.com	133		Po5	00:14:5e:cd:6c:0c	2015-05-06 11:48:35.509156	infinity	0
1679	2	test-sw.testorg.com	133		Po5	a0:48:1c:81:40:a6	2015-05-06 11:48:35.509884	infinity	0
1680	2	test-sw.testorg.com	133		Po5	f0:de:f1:fa:63:c6	2015-05-06 11:48:35.510626	infinity	0
1681	2	test-sw.testorg.com	133		Po5	00:1a:64:c4:07:28	2015-05-06 11:48:35.511355	infinity	0
1682	2	test-sw.testorg.com	133		Po5	00:11:32:2b:1e:f3	2015-05-06 11:48:35.512087	infinity	0
1683	2	test-sw.testorg.com	133		Po5	00:20:4a:e9:9a:32	2015-05-06 11:48:35.512833	infinity	0
1684	2	test-sw.testorg.com	133		Po5	00:25:90:62:21:82	2015-05-06 11:48:35.513544	infinity	0
1686	2	test-sw.testorg.com	133		Po5	10:60:4b:68:5c:cd	2015-05-06 11:48:35.514967	infinity	0
1687	2	test-sw.testorg.com	133		Po5	00:15:17:bc:84:2e	2015-05-06 11:48:35.515676	infinity	0
1688	2	test-sw.testorg.com	133		Po5	84:38:35:62:9f:5c	2015-05-06 11:48:35.516388	infinity	0
1641	2	test-sw.testorg.com	133		Po5	00:25:90:57:54:4d	2015-05-06 11:48:35.48299	infinity	0
1689	2	test-sw.testorg.com	133		Po5	68:f7:28:40:e3:97	2015-05-06 11:48:35.517121	2015-05-06 12:03:35.547696	\N
1692	2	test-sw.testorg.com	133		Po5	74:27:ea:bf:6d:7e	2015-05-06 12:03:35.457528	infinity	0
1708	2	test-sw.testorg.com	133		Po5	10:60:4b:6d:c0:78	2015-05-06 12:03:35.471361	infinity	0
1690	2	test-sw.testorg.com	133		Po5	40:a8:f0:a6:d3:51	2015-05-06 12:03:35.45561	infinity	0
1704	2	test-sw.testorg.com	133		Po5	78:d0:04:20:01:41	2015-05-06 12:03:35.467842	infinity	0
1538	2	test-sw.testorg.com	133		Po5	68:f7:28:78:68:9b	2015-05-06 11:48:35.404706	infinity	0
1720	2	test-sw.testorg.com	133		Po5	d4:be:d9:8e:34:51	2015-05-06 12:03:35.482502	infinity	0
1659	2	test-sw.testorg.com	133		Po5	e4:1f:13:43:1a:52	2015-05-06 11:48:35.49575	infinity	0
1663	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:64	2015-05-06 11:48:35.498693	2015-05-06 13:33:35.543625	1
1657	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:88	2015-05-06 11:48:35.494395	2015-05-06 13:33:35.550852	1
1758	2	test-sw.testorg.com	133		Po5	52:54:00:ef:d1:e4	2015-05-06 13:03:35.514877	2015-05-06 13:18:35.715004	2
1761	2	test-sw.testorg.com	133		Po5	b4:39:d6:c7:26:c0	2015-05-06 13:03:35.518212	2015-05-06 13:18:35.577672	2
1587	2	test-sw.testorg.com	133		Po5	00:14:5e:dc:00:4b	2015-05-06 11:48:35.445735	2015-05-06 13:18:35.724369	2
1670	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:7b	2015-05-06 11:48:35.503424	2015-05-06 13:33:35.579076	1
1763	2	test-sw.testorg.com	133		Po5	2c:41:38:88:66:4c	2015-05-06 13:03:35.5204	2015-05-06 13:18:35.633825	2
1759	2	test-sw.testorg.com	133		Po5	00:16:3e:1e:97:51	2015-05-06 13:03:35.516003	2015-05-06 13:18:35.625499	2
1760	2	test-sw.testorg.com	133		Po5	32:27:6d:49:aa:68	2015-05-06 13:03:35.517147	2015-05-06 13:18:35.729243	2
1623	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:96	2015-05-06 11:48:35.470525	2015-05-06 13:18:35.661836	2
1770	2	test-sw.testorg.com	133		Po5	28:d2:44:4f:b4:ad	2015-05-06 13:18:35.543684	2015-05-06 13:33:35.612966	1
1739	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:16:35	2015-05-06 12:18:35.455669	2015-05-06 13:33:35.616801	1
1592	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:78	2015-05-06 11:48:35.449189	2015-05-06 13:33:35.62236	1
1764	2	test-sw.testorg.com	133		Po5	2c:76:8a:5d:54:08	2015-05-06 13:03:35.521505	2015-05-06 13:18:35.689117	2
1757	2	test-sw.testorg.com	133		Po5	78:e7:d1:df:fa:76	2015-05-06 13:03:35.513178	2015-05-06 13:18:35.574219	2
1762	2	test-sw.testorg.com	133		Po5	20:c9:d0:83:45:b7	2015-05-06 13:03:35.51928	2015-05-06 13:33:35.652064	1
1728	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:54:a8	2015-05-06 12:18:35.446858	2015-05-06 13:18:35.598679	2
1660	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:eb	2015-05-06 11:48:35.496481	2015-05-06 13:33:35.673661	1
1741	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:66	2015-05-06 12:18:35.457358	2015-05-06 13:18:35.740999	2
1685	2	test-sw.testorg.com	133		Po5	00:09:3d:11:00:64	2015-05-06 11:48:35.514252	2015-05-06 13:33:35.692694	1
1655	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:aa	2015-05-06 11:48:35.493199	2015-05-06 13:18:35.606337	2
1652	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:52	2015-05-06 11:48:35.490985	2015-05-06 13:33:35.699083	1
1675	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:61	2015-05-06 11:48:35.506998	2015-05-06 13:33:35.701842	1
1671	2	test-sw.testorg.com	133		Po5	00:25:90:fe:38:0f	2015-05-06 11:48:35.504145	2015-05-06 13:33:35.704071	1
1756	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0e:92	2015-05-06 12:48:35.494529	2015-05-06 13:33:35.706263	1
1604	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:da	2015-05-06 11:48:35.457283	2015-05-06 13:33:35.717295	1
1697	2	test-sw.testorg.com	133		Po5	68:f7:28:78:6e:63	2015-05-06 12:03:35.461238	infinity	0
1734	2	test-sw.testorg.com	133		Po5	00:1f:16:07:02:08	2015-05-06 12:18:35.451499	infinity	0
1700	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0f:72	2015-05-06 12:03:35.463945	2015-05-06 12:18:35.495399	\N
1725	2	test-sw.testorg.com	133		Po5	00:1e:4f:ed:0e:8f	2015-05-06 12:18:35.444413	2015-05-06 12:48:35.592413	\N
1771	2	test-sw.testorg.com	133		Po5	00:15:5d:3a:a6:00	2015-05-06 13:33:35.527045	infinity	0
1709	2	test-sw.testorg.com	133		Po5	2c:41:38:88:66:4c	2015-05-06 12:03:35.47232	2015-05-06 12:18:35.498829	\N
1714	2	test-sw.testorg.com	133		Po5	28:d2:44:63:a1:91	2015-05-06 12:03:35.47717	infinity	0
1772	2	test-sw.testorg.com	133		Po5	08:81:f4:88:0d:ef	2015-05-06 13:33:35.528582	infinity	0
1716	2	test-sw.testorg.com	133		Po5	3c:97:0e:72:2e:f7	2015-05-06 12:03:35.479164	infinity	0
1773	2	test-sw.testorg.com	133		Po5	64:4b:f0:00:0c:50	2015-05-06 13:33:35.529627	infinity	0
1718	2	test-sw.testorg.com	133		Po5	00:40:8c:f3:f3:6f	2015-05-06 12:03:35.480963	infinity	0
1774	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:15:32	2015-05-06 13:33:35.530556	infinity	0
1775	2	test-sw.testorg.com	133		Po5	e8:39:35:c1:fd:4a	2015-05-06 13:33:35.531528	infinity	0
1715	2	test-sw.testorg.com	133		Po5	52:54:00:ef:d1:e4	2015-05-06 12:03:35.478213	2015-05-06 12:18:35.595136	\N
1691	2	test-sw.testorg.com	133		Po5	b8:27:eb:3a:0d:8b	2015-05-06 12:03:35.456749	infinity	0
1712	2	test-sw.testorg.com	133		Po5	84:2b:2b:ab:b8:d2	2015-05-06 12:03:35.475225	infinity	0
1694	2	test-sw.testorg.com	133		Po5	6c:3b:e5:2f:b2:e6	2015-05-06 12:03:35.458984	infinity	0
1724	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0a:ae	2015-05-06 12:18:35.443567	infinity	0
1701	2	test-sw.testorg.com	133		Po5	00:15:5d:3e:99:08	2015-05-06 12:03:35.46487	infinity	0
1696	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:6c	2015-05-06 12:03:35.460402	infinity	0
1705	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d3:38	2015-05-06 12:03:35.468721	infinity	0
1703	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:ec	2015-05-06 12:03:35.46694	infinity	0
1706	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:d0	2015-05-06 12:03:35.469613	infinity	0
1617	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:a5	2015-05-06 11:48:35.466476	2015-05-06 13:33:35.541351	1
1733	2	test-sw.testorg.com	133		Po5	44:1e:a1:4e:9a:ce	2015-05-06 12:18:35.450723	2015-05-06 13:33:35.545854	1
1731	2	test-sw.testorg.com	133		Po5	28:d2:44:60:31:dd	2015-05-06 12:18:35.449175	infinity	0
1735	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:8f	2015-05-06 12:18:35.452264	2015-05-06 13:18:35.637177	2
1551	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:ce	2015-05-06 11:48:35.418365	2015-05-06 13:33:35.564996	1
1635	2	test-sw.testorg.com	133		Po5	b4:b5:2f:52:c0:1a	2015-05-06 11:48:35.478705	2015-05-06 13:33:35.60545	1
1736	2	test-sw.testorg.com	133		Po5	3c:97:0e:95:dc:62	2015-05-06 12:18:35.4531	infinity	0
1723	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:55:80	2015-05-06 12:18:35.442764	2015-05-06 13:18:35.693643	2
1590	2	test-sw.testorg.com	133		Po5	b4:b5:2f:e4:69:fd	2015-05-06 11:48:35.447803	2015-05-06 13:18:35.569621	2
1695	2	test-sw.testorg.com	133		Po5	a8:20:66:2d:6c:51	2015-05-06 12:03:35.459656	2015-05-06 13:18:35.696877	2
1740	2	test-sw.testorg.com	133		Po5	00:1f:6d:8c:5c:18	2015-05-06 12:18:35.456498	2015-05-06 13:33:35.690449	1
1713	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:15:32	2015-05-06 12:03:35.47618	2015-05-06 12:18:35.511251	\N
1626	2	test-sw.testorg.com	133		Po5	00:0a:5c:1e:ef:7a	2015-05-06 11:48:35.472529	infinity	0
1698	2	test-sw.testorg.com	133		Po5	32:27:6d:49:aa:68	2015-05-06 12:03:35.462157	2015-05-06 12:18:35.47092	\N
1726	2	test-sw.testorg.com	133		Po5	00:1a:64:d5:6e:d1	2015-05-06 12:18:35.445267	2015-05-06 12:33:35.621356	\N
1581	2	test-sw.testorg.com	133		Po5	28:d2:44:48:6c:0b	2015-05-06 11:48:35.44176	2015-05-06 12:33:35.565477	\N
1729	2	test-sw.testorg.com	133		Po5	00:25:64:d7:a5:83	2015-05-06 12:18:35.447634	2015-05-06 12:33:35.562067	\N
1738	2	test-sw.testorg.com	133		Po5	2c:41:38:88:66:20	2015-05-06 12:18:35.454829	2015-05-06 12:33:35.591577	\N
1730	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0e:94	2015-05-06 12:18:35.448401	2015-05-06 12:33:35.61293	\N
1742	2	test-sw.testorg.com	133		Po5	28:92:4a:ff:62:e0	2015-05-06 12:18:35.45814	2015-05-06 12:33:35.51112	\N
1721	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:a8	2015-05-06 12:03:35.483265	infinity	0
1745	2	test-sw.testorg.com	133		Po5	64:4b:f0:00:0c:50	2015-05-06 12:33:35.495106	2015-05-06 12:48:35.509367	\N
1749	2	test-sw.testorg.com	133		Po5	64:4b:f0:00:0c:4f	2015-05-06 12:33:35.497869	infinity	0
1747	2	test-sw.testorg.com	133		Po5	00:1f:28:6a:4c:40	2015-05-06 12:33:35.496683	2015-05-06 12:48:35.658602	\N
1750	2	test-sw.testorg.com	133		Po5	00:15:5d:3a:a6:00	2015-05-06 12:33:35.498431	2015-05-06 12:48:35.686512	\N
1707	2	test-sw.testorg.com	133		Po5	6c:3b:e5:2f:b2:e8	2015-05-06 12:03:35.470493	infinity	0
1717	2	test-sw.testorg.com	133		Po5	c4:34:6b:53:93:29	2015-05-06 12:03:35.480062	infinity	0
1693	2	test-sw.testorg.com	133		Po5	f0:de:f1:ca:a2:0e	2015-05-06 12:03:35.458265	infinity	0
1710	2	test-sw.testorg.com	133		Po5	84:2b:2b:ab:b4:6b	2015-05-06 12:03:35.473307	infinity	0
1743	2	test-sw.testorg.com	133		Po5	00:50:b6:63:c0:2a	2015-05-06 12:18:35.458908	infinity	0
1541	2	test-sw.testorg.com	133		Po5	c8:cb:b8:2a:07:1a	2015-05-06 11:48:35.409058	infinity	0
1719	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0e:0d	2015-05-06 12:03:35.481736	infinity	0
1702	2	test-sw.testorg.com	133		Po5	10:60:4b:6b:11:05	2015-05-06 12:03:35.465799	infinity	0
1699	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:15:46	2015-05-06 12:03:35.463036	infinity	0
1711	2	test-sw.testorg.com	133		Po5	10:60:4b:6b:10:d4	2015-05-06 12:03:35.474264	infinity	0
1732	2	test-sw.testorg.com	133		Po5	54:ee:75:3b:af:04	2015-05-06 12:18:35.449949	infinity	0
1748	2	test-sw.testorg.com	133		Po5	e8:39:35:e8:0e:46	2015-05-06 12:33:35.497273	2015-05-06 13:03:35.548597	\N
1746	2	test-sw.testorg.com	133		Po5	00:8c:fa:c8:61:14	2015-05-06 12:33:35.496098	2015-05-06 13:18:35.650651	2
1737	2	test-sw.testorg.com	133		Po5	00:c0:b7:94:d2:e8	2015-05-06 12:18:35.453952	2015-05-06 13:18:35.602516	2
1722	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:a1	2015-05-06 12:18:35.441546	2015-05-06 13:18:35.744425	2
1569	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:53:a4	2015-05-06 11:48:35.432964	2015-05-06 13:33:35.668811	1
1744	2	test-sw.testorg.com	133		Po5	00:1f:28:6a:6c:00	2015-05-06 12:18:35.45967	2015-05-06 13:18:35.721055	2
1727	2	test-sw.testorg.com	133		Po5	00:c0:b7:b3:54:e2	2015-05-06 12:18:35.446064	2015-05-06 13:18:35.667528	2
15	2	test-sw.testorg.com	57		Gi3/1	00:22:64:a2:38:40	2015-05-06 10:40:22.209535	infinity	0
590	2	test-sw.testorg.com	44		Gi2/36	e8:39:35:20:30:31	2015-05-06 10:55:21.713782	2015-05-06 11:10:21.777703	\N
589	2	test-sw.testorg.com	57		Gi3/1	00:26:55:86:11:6e	2015-05-06 10:55:21.711911	infinity	0
97	2	test-sw.testorg.com	57		Gi3/1	00:1e:0b:5f:d2:fa	2015-05-06 10:40:22.271469	infinity	0
\.


--
-- Name: cam_camid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('cam_camid_seq', 1775, true);


--
-- Data for Name: cat; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY cat (catid, descr, req_snmp) FROM stdin;
GW	Routers (layer 3 device)	t
GSW	A layer 2 and layer 3 device	t
SW	Core switches (layer 2), typically with many vlans	t
EDGE	Edge switch without vlans (layer 2)	t
WLAN	Wireless equipment	t
SRV	Server	f
OTHER	Other equipment	f
ENV	Environmental probes	t
POWER	Power distribution equipment	t
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY device (deviceid, serial, hw_ver, fw_ver, sw_ver, discovered) FROM stdin;
2	SMT1136F638	\N	\N	\N	2015-05-06 10:36:26.326853
3	SAL1550Y7LX	V03	\N	\N	2015-05-06 10:36:26.373358
4	FBXXL32	V03	\N	\N	2015-05-06 10:36:26.378812
5	FBXXL30	V03	\N	\N	2015-05-06 10:36:26.38319
6	SAL11391SS4	V03	8.4(1)	12.2(33)SXJ7	2015-05-06 10:36:26.386991
7	JAF1234ABFL	V04	12.2(18r)S1	12.2(33)SXJ7	2015-05-06 10:36:26.391103
8	SMT1142E997	\N	\N	\N	2015-05-06 10:36:26.395217
9	FBXXS070	V03	\N	\N	2015-05-06 10:36:26.399301
10	JAF1236AEAF	V06	\N	\N	2015-05-06 10:36:26.402762
11	SAL11499E9Q	V03	8.4(1)	12.2(33)SXJ7	2015-05-06 10:36:26.406348
12	FBXXS014	V03	\N	\N	2015-05-06 10:36:26.410048
13	SMT1142E572	\N	\N	\N	2015-05-06 10:36:26.413669
14	FNS115000694	\N	\N	\N	2015-05-06 10:36:26.417348
15	SMT1142F005	\N	\N	\N	2015-05-06 10:36:26.420693
1	SMC1145003Z	V04	\N	12.2(33)SXJ7	2015-05-06 10:35:58.953652
16	3134803307	V01	\N	\N	2015-05-06 10:36:26.427881
17	SAL1550XXPW	V10	12.2(18r)S1	12.2(33)SXJ7	2015-05-06 10:36:26.431648
18	SAL1151AL1N	V05	\N	\N	2015-05-06 10:36:26.435229
19	SAL1150ABRW	\N	12.2(17r)S4	12.2(33)SXJ7	2015-05-06 10:36:26.437653
20	SNI1148AW5Q	V01			2015-05-06 10:36:26.439903
21	SAL1150ACXH	V01	\N	\N	2015-05-06 10:36:26.442034
22	M823805	\N	\N	\N	2015-05-06 10:36:26.444128
23	SNI1147AWJ5	V01			2015-05-06 10:36:26.446491
24	FBXXL27	V03	\N	\N	2015-05-06 10:36:26.449118
25	M823803	\N	\N	\N	2015-05-06 10:36:26.466164
26	SAL1151ASHN	V03	12.2(18r)S1	12.2(33)SXJ7	2015-05-06 10:36:26.468982
27	DCH11420667	V03			2015-05-06 10:36:26.471549
28	OE31006280	V01	\N	\N	2015-05-06 10:36:26.47423
29	SAL07100506	\N	8.3(1)	12.2(33)SXJ7	2015-05-06 10:36:26.47651
30	H11K741	\N	\N	\N	2015-05-06 10:36:26.478733
31	SAL1150ABJH	V05	8.5(2)	12.2(33)SXJ7	2015-05-06 10:36:26.480992
33	JAE14430HD0	V04	12.2(44r)SG5	12.2(54)SG	2015-05-06 10:38:22.250712
34	JAE144309MF	V05	\N	\N	2015-05-06 10:38:22.260568
32	FOX1440GYD9	V02	\N	12.2(54)SG	2015-05-06 10:36:55.357625
35	JAE144005KO	V03	\N	\N	2015-05-06 10:38:22.267943
36	JAE144309O6	V05	\N	\N	2015-05-06 10:38:22.271713
37	FOX1440GTRD	V03			2015-05-06 10:40:22.61715
38	SNI1438A876	V06			2015-05-06 10:40:22.661281
39	SNI1438A87Q	V06			2015-05-06 10:40:22.665359
42	FNS115000693	\N	\N	\N	2015-05-06 11:24:24.245442
43	FNS115000692	\N	\N	\N	2015-05-06 11:24:24.250315
41	SAL13505XKF	V05	\N	12.2(33)SXI13	2015-05-06 11:22:38.045994
44	SAL1346402S	V04	\N	\N	2015-05-06 11:24:24.257551
45	SAL13495UQR	V04	12.2(17r)SX3	12.2(33)SXI13	2015-05-06 11:24:24.261051
46	FNS115000425	\N	\N	\N	2015-05-06 11:24:24.264577
47	FNS115000426	\N	\N	\N	2015-05-06 11:24:24.268108
48	DP514040112	V02			2015-05-06 11:26:29.642759
49	DP513450089	V02			2015-05-06 11:26:29.688244
50	SAL13495UP1	V01			2015-05-06 11:26:29.693521
52	BP0211430396	\N	\N	12.3R5.7	2015-05-06 11:40:35.883273
\.


--
-- Name: device_deviceid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('device_deviceid_seq', 52, true);


--
-- Data for Name: eventq; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY eventq (eventqid, source, target, deviceid, netboxid, subid, "time", eventtypeid, state, value, severity) FROM stdin;
\.


--
-- Name: eventq_eventqid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('eventq_eventqid_seq', 1, false);


--
-- Data for Name: eventqvar; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY eventqvar (id, eventqid, var, val) FROM stdin;
\.


--
-- Name: eventqvar_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('eventqvar_id_seq', 1, false);


--
-- Data for Name: eventtype; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY eventtype (eventtypeid, eventtypedesc, stateful) FROM stdin;
boxState	Tells us whether a network-unit is down or up.	y
serviceState	Tells us whether a service on a server is up or down.	y
moduleState	Tells us whether a module in a device is working or not.	y
thresholdState	Tells us whether the load has passed a certain threshold.	y
linkState	Tells us whether a link is up or down.	y
boxRestart	Tells us that a network-unit has done a restart	n
info	Basic information	n
notification	Notification event, typically between NAV systems	n
deviceActive	Lifetime event for a device	y
deviceState	Registers the state of a device	y
deviceNotice	Registers a notice on a device	n
maintenanceState	Tells us if something is set on maintenance	y
apState	Tells us whether an access point has disassociated or associated from the controller	y
snmpAgentState	Tells us whether the SNMP agent on a device is down or up.	y
psuState	Reports state changes in power supply units	y
fanState	Reports state changes in fan units	y
weathergoose_airflow		y
weathergoose_sound		y
weathergoose_humidity		y
weathergoose_light		y
weathergoose_temperature		y
upsPowerState	UPS running on battery or utility power	y
\.


--
-- Data for Name: gwportprefix; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY gwportprefix (interfaceid, prefixid, gwip, virtual) FROM stdin;
451	18	158.38.0.2	f
551	16	158.38.38.3	f
518	25	128.39.103.25	f
523	19	158.38.180.3	f
511	8	2001:700:1:f01::2	f
511	22	158.38.0.1	f
518	28	2001:700:1:f00::2	f
522	17	158.38.179.131	f
512	26	128.39.70.10	f
521	3	2001:700:0:4528::1	f
522	2	2001:700:0:4529::1	f
520	24	158.38.234.6	f
521	18	158.38.179.3	f
512	29	2001:700:0:8000::2	f
520	27	2001:700:1:f03::2	f
523	6	2001:700:1:8::2	f
\.


--
-- Data for Name: iana_iftype; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY iana_iftype (iftype, name, descr) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY image (imageid, roomid, title, path, name, created, uploader, priority) FROM stdin;
\.


--
-- Name: image_imageid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('image_imageid_seq', 1, false);


--
-- Data for Name: interface; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY interface (interfaceid, netboxid, moduleid, ifindex, ifname, ifdescr, iftype, speed, ifphysaddress, ifadminstatus, ifoperstatus, iflastchange, ifconnectorpresent, ifpromiscuousmode, ifalias, baseport, media, vlan, trunk, duplex, to_netboxid, to_interfaceid, gone_since) FROM stdin;
327	2	29	10	Gi2/2	GigabitEthernet2/2	6	1000	58:8d:09:dd:57:01	1	1	\N	t	\N	lokal link, blaasal-sw.uninett-gsw2-2	66	\N	1	t	f	3	482	\N
326	2	29	9	Gi2/1	GigabitEthernet2/1	6	1000	58:8d:09:dd:57:00	1	1	\N	t	\N	lokal link, blaasal-sw.uninett-gsw2-1	65	\N	1	t	f	3	481	\N
329	2	29	12	Gi2/4	GigabitEthernet2/4	6	1000	58:8d:09:dd:57:03	1	1	\N	t	\N	lokal link, blaasal-sw.uninett-gsw2-4	68	\N	1	t	f	3	484	\N
447	2	\N	130	Po2	Port-channel2	53	3000	58:8d:09:dd:57:00	1	1	\N	f	\N	lokal link, blaasal-sw.uninett-gsw2	642	\N	1	t	\N	3	519	\N
481	3	34	1	Gi1/1	GigabitEthernet1/1	6	1000	00:22:55:f8:9b:0c	1	1	\N	t	\N	lokal link, uninett-gsw2.blaasal-sw-1	\N	\N	1	t	f	2	326	\N
482	3	34	2	Gi1/2	GigabitEthernet1/2	6	1000	00:22:55:f8:9b:0d	1	1	\N	t	\N	lokal link, uninett-gsw2.blaasal-sw-2	\N	\N	1	t	f	2	327	\N
519	3	\N	39	Po2	Port-channel2	53	3000	00:22:55:f8:9b:0c	1	1	\N	f	\N	lokal link, uninett-gsw2.blaasal-sw	1665	\N	1	t	\N	2	447	\N
328	2	29	11	Gi2/3	GigabitEthernet2/3	6	1000	58:8d:09:dd:57:02	1	2	\N	t	\N	lokal link, blaasal-sw.uninett-gsw2-3	67	\N	1	t	\N	\N	\N	\N
330	2	29	13	Gi2/5	GigabitEthernet2/5	6	1000	58:8d:09:dd:57:04	2	2	\N	t	\N		69	\N	1	f	\N	\N	\N	\N
332	2	29	15	Gi2/7	GigabitEthernet2/7	6	1000	58:8d:09:dd:57:06	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay2-1, jatoba-bay2	71	\N	1	t	f	\N	\N	\N
335	2	29	18	Gi2/10	GigabitEthernet2/10	6	1000	58:8d:09:dd:57:09	2	2	\N	t	\N		74	\N	1	f	\N	\N	\N	\N
337	2	29	20	Gi2/12	GigabitEthernet2/12	6	1000	58:8d:09:dd:57:0b	2	2	\N	t	\N		76	\N	1	f	\N	\N	\N	\N
339	2	29	22	Gi2/14	GigabitEthernet2/14	6	1000	58:8d:09:dd:57:0d	2	2	\N	t	\N		78	\N	1	f	\N	\N	\N	\N
341	2	29	24	Gi2/16	GigabitEthernet2/16	6	1000	58:8d:09:dd:57:0f	2	2	\N	t	\N		80	\N	1	f	\N	\N	\N	\N
343	2	29	26	Gi2/18	GigabitEthernet2/18	6	1000	58:8d:09:dd:57:11	2	2	\N	t	\N		82	\N	1	f	\N	\N	\N	\N
344	2	29	27	Gi2/19	GigabitEthernet2/19	6	100	58:8d:09:dd:57:12	1	1	\N	t	\N	backuppc-bs-01-ilo	83	\N	40	f	f	\N	\N	\N
346	2	29	29	Gi2/21	GigabitEthernet2/21	6	100	58:8d:09:dd:57:14	1	1	\N	t	\N	backuppc-bs-03-ilo	85	\N	40	f	f	\N	\N	\N
349	2	29	32	Gi2/24	GigabitEthernet2/24	6	1000	58:8d:09:dd:57:17	2	2	\N	t	\N		88	\N	1	f	\N	\N	\N	\N
351	2	29	34	Gi2/26	GigabitEthernet2/26	6	1000	58:8d:09:dd:57:19	2	2	\N	t	\N		90	\N	1	f	\N	\N	\N	\N
353	2	29	36	Gi2/28	GigabitEthernet2/28	6	1000	58:8d:09:dd:57:1b	2	2	\N	t	\N		92	\N	1	f	\N	\N	\N	\N
354	2	29	37	Gi2/29	GigabitEthernet2/29	6	1000	58:8d:09:dd:57:1c	1	1	\N	t	\N	backuppc-bs-02-port1	93	\N	8	f	f	\N	\N	\N
357	2	29	40	Gi2/32	GigabitEthernet2/32	6	1000	58:8d:09:dd:57:1f	2	2	\N	t	\N		96	\N	1	f	\N	\N	\N	\N
359	2	29	42	Gi2/34	GigabitEthernet2/34	6	1000	58:8d:09:dd:57:21	2	2	\N	t	\N		98	\N	1	f	\N	\N	\N	\N
361	2	29	44	Gi2/36	GigabitEthernet2/36	6	1000	58:8d:09:dd:57:23	1	1	\N	t	\N	lokal link, trd-sgw2-ilo	100	\N	6	f	f	\N	\N	\N
363	2	29	46	Gi2/38	GigabitEthernet2/38	6	100	58:8d:09:dd:57:25	1	1	\N	t	\N	direkte kablet, feide-mdb02-ilo.uninett.no	102	\N	40	f	f	\N	\N	\N
366	2	29	49	Gi2/41	GigabitEthernet2/41	6	100	58:8d:09:dd:57:28	1	1	\N	t	\N	pltrd002.oam-ilo.uninett.no	105	\N	40	f	f	\N	\N	\N
368	2	29	51	Gi2/43	GigabitEthernet2/43	6	1000	58:8d:09:dd:57:2a	1	1	\N	t	\N	midlertidig-vlan5	107	\N	5	f	f	\N	\N	\N
370	2	29	53	Gi2/45	GigabitEthernet2/45	6	1000	58:8d:09:dd:57:2c	2	2	\N	t	\N		109	\N	1	f	\N	\N	\N	\N
372	2	29	55	Gi2/47	GigabitEthernet2/47	6	1000	58:8d:09:dd:57:2e	2	2	\N	t	\N		111	\N	1	f	\N	\N	\N	\N
374	2	28	57	Gi3/1	GigabitEthernet3/1	6	100	58:8d:09:e1:a9:a0	1	1	\N	t	\N	HP-chassis.management1	129	\N	5	f	f	\N	\N	\N
376	2	28	59	Gi3/3	GigabitEthernet3/3	6	1000	58:8d:09:e1:a9:a2	1	1	\N	t	\N	jatoba-san1.uninett.no	131	\N	5	f	f	\N	\N	\N
379	2	28	62	Gi3/6	GigabitEthernet3/6	6	1000	58:8d:09:e1:a9:a5	1	1	\N	t	\N	jatoba-san3.uninett.no	134	\N	5	f	f	\N	\N	\N
381	2	28	64	Gi3/8	GigabitEthernet3/8	6	1000	58:8d:09:e1:a9:a7	2	2	\N	t	\N		136	\N	10	f	\N	\N	\N	\N
383	2	28	66	Gi3/10	GigabitEthernet3/10	6	1000	58:8d:09:e1:a9:a9	2	2	\N	t	\N		138	\N	11	f	\N	\N	\N	\N
385	2	28	68	Gi3/12	GigabitEthernet3/12	6	100	58:8d:09:e1:a9:ab	2	2	\N	t	\N		140	\N	11	f	h	\N	\N	\N
387	2	28	70	Gi3/14	GigabitEthernet3/14	6	100	58:8d:09:e1:a9:ad	1	1	\N	t	\N	sip-services-ilo.uninett.no	142	\N	40	f	f	\N	\N	\N
389	2	28	72	Gi3/16	GigabitEthernet3/16	6	1000	58:8d:09:e1:a9:af	1	2	\N	t	\N	lokal link for mgmt, qnap-bs.uninett.no	144	\N	40	f	\N	\N	\N	\N
391	2	28	74	Gi3/18	GigabitEthernet3/18	6	1000	58:8d:09:e1:a9:b1	2	2	\N	t	\N		146	\N	1	f	\N	\N	\N	\N
394	2	28	77	Gi3/21	GigabitEthernet3/21	6	1000	58:8d:09:e1:a9:b4	1	1	\N	t	\N	sip-services.uninett.no	149	\N	45	f	f	\N	\N	\N
396	2	28	79	Gi3/23	GigabitEthernet3/23	6	1000	58:8d:09:e1:a9:b6	1	1	\N	t	\N	trd-agw1.uninett.no	151	\N	45	f	f	\N	\N	\N
399	2	28	82	Gi3/26	GigabitEthernet3/26	6	1000	58:8d:09:e1:a9:b9	2	2	\N	t	\N		154	\N	1	f	\N	\N	\N	\N
400	2	28	83	Gi3/27	GigabitEthernet3/27	6	1000	58:8d:09:e1:a9:ba	1	1	\N	t	\N	trd-tgw1.tlf.uninett.no	155	\N	151	f	f	\N	\N	\N
403	2	28	86	Gi3/30	GigabitEthernet3/30	6	1000	58:8d:09:e1:a9:bd	2	2	\N	t	\N		158	\N	45	f	\N	\N	\N	\N
405	2	28	88	Gi3/32	GigabitEthernet3/32	6	1000	58:8d:09:e1:a9:bf	2	2	\N	t	\N		160	\N	45	f	\N	\N	\N	\N
406	2	28	89	Gi3/33	GigabitEthernet3/33	6	1000	58:8d:09:e1:a9:c0	2	2	\N	t	\N		161	\N	1	f	\N	\N	\N	\N
408	2	28	91	Gi3/35	GigabitEthernet3/35	6	1000	58:8d:09:e1:a9:c2	2	2	\N	t	\N		163	\N	1	f	\N	\N	\N	\N
410	2	28	93	Gi3/37	GigabitEthernet3/37	6	1000	58:8d:09:e1:a9:c4	2	2	\N	t	\N		165	\N	1	f	\N	\N	\N	\N
412	2	28	95	Gi3/39	GigabitEthernet3/39	6	1000	58:8d:09:e1:a9:c6	2	2	\N	t	\N		167	\N	1	f	\N	\N	\N	\N
414	2	28	97	Gi3/41	GigabitEthernet3/41	6	1000	58:8d:09:e1:a9:c8	2	2	\N	t	\N		169	\N	1	f	\N	\N	\N	\N
416	2	28	99	Gi3/43	GigabitEthernet3/43	6	1000	58:8d:09:e1:a9:ca	2	2	\N	t	\N		171	\N	1	f	\N	\N	\N	\N
418	2	28	101	Gi3/45	GigabitEthernet3/45	6	1000	58:8d:09:e1:a9:cc	2	2	\N	t	\N		173	\N	1	f	\N	\N	\N	\N
420	2	28	103	Gi3/47	GigabitEthernet3/47	6	1000	58:8d:09:e1:a9:ce	2	2	\N	t	\N		175	\N	1	f	\N	\N	\N	\N
422	2	31	105	Te4/1	TenGigabitEthernet4/1	6	10000	1c:df:0f:7e:36:8d	1	1	\N	t	\N	local fiber, blaasal-sw.trd-gw7	193	\N	1	t	f	\N	\N	\N
425	2	31	108	Te4/4	TenGigabitEthernet4/4	6	10000	1c:df:0f:7e:36:90	1	1	\N	t	\N	lokal link, blaasal-sw.jatoba-bay6-x1, jatoba-bay6	196	\N	1	t	f	\N	\N	\N
427	2	31	110	Te4/6	TenGigabitEthernet4/6	6	10000	1c:df:0f:7e:36:92	1	2	\N	t	\N	lokal link, blaasal-sw.blaasal-rack2-sw-2	198	\N	1	t	f	\N	\N	\N
429	2	\N	112	Gi4/8	GigabitEthernet4/8	6	1000	1c:df:0f:7e:36:94	2	2	\N	t	\N		200	\N	1	f	f	\N	\N	\N
431	2	\N	114	Gi4/10	GigabitEthernet4/10	6	1000	1c:df:0f:7e:36:96	2	2	\N	t	\N		202	\N	1	f	f	\N	\N	\N
433	2	\N	116	Gi4/12	GigabitEthernet4/12	6	1000	1c:df:0f:7e:36:98	2	2	\N	t	\N		204	\N	1	f	f	\N	\N	\N
435	2	\N	118	Gi4/14	GigabitEthernet4/14	6	1000	1c:df:0f:7e:36:9a	2	2	\N	t	\N		206	\N	1	f	f	\N	\N	\N
437	2	\N	120	Gi4/16	GigabitEthernet4/16	6	1000	1c:df:0f:7e:36:9c	2	2	\N	t	\N		208	\N	1	f	f	\N	\N	\N
439	2	\N	122	Gi4/18	GigabitEthernet4/18	6	1000	1c:df:0f:7e:36:9e	2	2	\N	t	\N		210	\N	1	f	f	\N	\N	\N
319	2	30	2	Fa1	FastEthernet1	6	100	00:21:1c:7d:35:95	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
320	2	30	3	Te1/1	TenGigabitEthernet1/1	6	10000	58:8d:09:7e:19:40	1	1	\N	t	\N	fiber om Hovedbygget, blaasalen-hb-teknobyen, teknobyen-sw	1	\N	1	t	f	\N	\N	\N
321	2	30	4	Te1/2	TenGigabitEthernet1/2	6	10000	58:8d:09:7e:19:41	1	1	\N	t	\N	fiber om Realfagbygget, blaasal-teknobyen-rfb, teknobyen-sw	2	\N	1	t	f	\N	\N	\N
322	2	\N	5	Gi1/3	GigabitEthernet1/3	6	1000	58:8d:09:7e:19:42	2	2	\N	t	\N		3	\N	40	f	f	\N	\N	\N
323	2	\N	6	Gi1/4	GigabitEthernet1/4	6	1000	58:8d:09:7e:19:43	2	2	\N	t	\N		4	\N	40	f	f	\N	\N	\N
324	2	\N	7	Gi1/5	GigabitEthernet1/5	6	1000	58:8d:09:7e:19:44	2	2	\N	t	\N		5	\N	1	f	f	\N	\N	\N
325	2	\N	8	Gi1/6	GigabitEthernet1/6	6	1000	58:8d:09:7e:19:45	2	2	\N	t	\N		6	\N	1	f	f	\N	\N	\N
331	2	29	14	Gi2/6	GigabitEthernet2/6	6	1000	58:8d:09:dd:57:05	2	2	\N	t	\N		70	\N	1	f	\N	\N	\N	\N
333	2	29	16	Gi2/8	GigabitEthernet2/8	6	1000	58:8d:09:dd:57:07	2	2	\N	t	\N		72	\N	1	f	\N	\N	\N	\N
334	2	29	17	Gi2/9	GigabitEthernet2/9	6	1000	58:8d:09:dd:57:08	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay2-2, jatoba-bay2	73	\N	1	t	f	\N	\N	\N
336	2	29	19	Gi2/11	GigabitEthernet2/11	6	1000	58:8d:09:dd:57:0a	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay2-3, jatoba-bay2	75	\N	1	t	f	\N	\N	\N
338	2	29	21	Gi2/13	GigabitEthernet2/13	6	1000	58:8d:09:dd:57:0c	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay5-1, jatoba-bay5	77	\N	1	t	f	\N	\N	\N
340	2	29	23	Gi2/15	GigabitEthernet2/15	6	1000	58:8d:09:dd:57:0e	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay5-2, jatoba-bay5	79	\N	1	t	f	\N	\N	\N
342	2	29	25	Gi2/17	GigabitEthernet2/17	6	1000	58:8d:09:dd:57:10	1	1	\N	t	\N	local link, blaasal-sw.jatoba-bay5-3, jatoba-bay5	81	\N	1	t	f	\N	\N	\N
345	2	29	28	Gi2/20	GigabitEthernet2/20	6	100	58:8d:09:dd:57:13	1	1	\N	t	\N	backuppc-bs-02-ilo	84	\N	40	f	f	\N	\N	\N
347	2	29	30	Gi2/22	GigabitEthernet2/22	6	1000	58:8d:09:dd:57:15	2	2	\N	t	\N		86	\N	1	f	\N	\N	\N	\N
348	2	29	31	Gi2/23	GigabitEthernet2/23	6	1000	58:8d:09:dd:57:16	1	1	\N	t	\N	backuppc-bs-01-port0	87	\N	8	f	f	\N	\N	\N
350	2	29	33	Gi2/25	GigabitEthernet2/25	6	1000	58:8d:09:dd:57:18	1	1	\N	t	\N	backuppc-bs-01-port1	89	\N	8	f	f	\N	\N	\N
352	2	29	35	Gi2/27	GigabitEthernet2/27	6	1000	58:8d:09:dd:57:1a	1	1	\N	t	\N	backuppc-bs-02-port0	91	\N	8	f	f	\N	\N	\N
355	2	29	38	Gi2/30	GigabitEthernet2/30	6	1000	58:8d:09:dd:57:1d	2	2	\N	t	\N		94	\N	1	f	\N	\N	\N	\N
356	2	29	39	Gi2/31	GigabitEthernet2/31	6	1000	58:8d:09:dd:57:1e	1	1	\N	t	\N	backuppc-bs-03-port0	95	\N	8	f	f	\N	\N	\N
358	2	29	41	Gi2/33	GigabitEthernet2/33	6	1000	58:8d:09:dd:57:20	1	1	\N	t	\N	backuppc-bs-03-port1	97	\N	8	f	f	\N	\N	\N
360	2	29	43	Gi2/35	GigabitEthernet2/35	6	1000	58:8d:09:dd:57:22	1	1	\N	t	\N	lokal link, trd-sgw2.uninett.no	99	\N	131	f	f	\N	\N	\N
362	2	29	45	Gi2/37	GigabitEthernet2/37	6	1000	58:8d:09:dd:57:24	1	1	\N	t	\N	direkte kablet, feide-mdb02.uninett.no	101	\N	45	f	f	\N	\N	\N
364	2	29	47	Gi2/39	GigabitEthernet2/39	6	1000	58:8d:09:dd:57:26	2	2	\N	t	\N		103	\N	1	f	\N	\N	\N	\N
365	2	29	48	Gi2/40	GigabitEthernet2/40	6	1000	58:8d:09:dd:57:27	1	1	\N	t	\N	pltrd002.oam.uninett.no	104	\N	8	f	f	\N	\N	\N
367	2	29	50	Gi2/42	GigabitEthernet2/42	6	1000	58:8d:09:dd:57:29	1	2	\N	t	\N	pwtrd001.oam.uninett.no	106	\N	8	f	\N	\N	\N	\N
369	2	29	52	Gi2/44	GigabitEthernet2/44	6	1000	58:8d:09:dd:57:2b	2	2	\N	t	\N		108	\N	1	f	\N	\N	\N	\N
371	2	29	54	Gi2/46	GigabitEthernet2/46	6	1000	58:8d:09:dd:57:2d	2	2	\N	t	\N		110	\N	1	f	\N	\N	\N	\N
373	2	29	56	Gi2/48	GigabitEthernet2/48	6	1000	58:8d:09:dd:57:2f	1	2	\N	t	\N	midlertidig for arbeid lokalt	112	\N	109	f	\N	\N	\N	\N
375	2	28	58	Gi3/2	GigabitEthernet3/2	6	100	58:8d:09:e1:a9:a1	1	1	\N	t	\N	HP-chassis.management2	130	\N	5	f	f	\N	\N	\N
377	2	28	60	Gi3/4	GigabitEthernet3/4	6	1000	58:8d:09:e1:a9:a3	1	1	\N	t	\N	trd-lgw1.uninett.no	132	\N	45	f	f	\N	\N	\N
442	2	\N	125	VLAN-1	unrouted VLAN 1	53	0	58:8d:09:7e:19:40	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
444	2	\N	127	VLAN-1004	unrouted VLAN 1004	53	0	58:8d:09:7e:19:6b	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
445	2	\N	128	VLAN-1005	unrouted VLAN 1005	53	0	58:8d:09:7e:19:6c	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
448	2	\N	131	Po3	Port-channel3	53	3000	58:8d:09:dd:57:0a	1	1	\N	f	\N	lokal link, blaasal-sw.jatoba-bay2, jatoba-bay2	643	\N	1	t	\N	\N	\N	\N
452	2	\N	135	VLAN-5	unrouted VLAN 5	53	0	58:8d:09:7e:19:44	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
454	2	\N	137	VLAN-8	unrouted VLAN 8	53	0	58:8d:09:7e:19:47	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
455	2	\N	140	VLAN-15	unrouted VLAN 15	53	0	58:8d:09:7e:19:4e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
457	2	\N	143	VLAN-40	unrouted VLAN 40	53	0	58:8d:09:7e:19:67	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
459	2	\N	145	VLAN-45	unrouted VLAN 45	53	0	58:8d:09:7e:19:6c	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
460	2	\N	146	VLAN-66	unrouted VLAN 66	53	0	58:8d:09:7e:19:41	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
462	2	\N	148	VLAN-95	unrouted VLAN 95	53	0	58:8d:09:7e:19:5e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
464	2	\N	150	VLAN-109	unrouted VLAN 109	53	0	58:8d:09:7e:19:6c	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
465	2	\N	151	VLAN-150	unrouted VLAN 150	53	0	58:8d:09:7e:19:55	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
467	2	\N	154	VLAN-190	unrouted VLAN 190	53	0	58:8d:09:7e:19:7d	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
468	2	\N	155	VLAN-444	unrouted VLAN 444	53	0	58:8d:09:7e:19:7b	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
470	2	\N	157	VLAN-64	unrouted VLAN 64	53	0	58:8d:09:7e:19:7f	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
472	2	\N	159	VLAN-51	unrouted VLAN 51	53	0	58:8d:09:7e:19:72	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
473	2	\N	160	VLAN-52	unrouted VLAN 52	53	0	58:8d:09:7e:19:73	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
475	2	\N	162	VLAN-130	unrouted VLAN 130	53	0	58:8d:09:7e:19:41	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
476	2	\N	163	VLAN-80	unrouted VLAN 80	53	0	58:8d:09:7e:19:4f	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
479	2	\N	166	VLAN-131	unrouted VLAN 131	53	0	58:8d:09:7e:19:42	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
480	2	\N	167	VLAN-98	unrouted VLAN 98	53	0	58:8d:09:7e:19:61	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
378	2	28	61	Gi3/5	GigabitEthernet3/5	6	1000	58:8d:09:e1:a9:a4	2	2	\N	t	\N	var jatoba-san2.uninett.no	133	\N	5	f	\N	\N	\N	\N
380	2	28	63	Gi3/7	GigabitEthernet3/7	6	100	58:8d:09:e1:a9:a6	2	2	\N	t	\N		135	\N	11	f	\N	\N	\N	\N
382	2	28	65	Gi3/9	GigabitEthernet3/9	6	1000	58:8d:09:e1:a9:a8	2	2	\N	t	\N		137	\N	1	f	\N	\N	\N	\N
384	2	28	67	Gi3/11	GigabitEthernet3/11	6	1000	58:8d:09:e1:a9:aa	1	2	\N	t	\N	antarcdisk	139	\N	20	f	\N	\N	\N	\N
386	2	28	69	Gi3/13	GigabitEthernet3/13	6	100	58:8d:09:e1:a9:ac	1	1	\N	t	\N	trd-tgw1-ilo	141	\N	40	f	f	\N	\N	\N
388	2	28	71	Gi3/15	GigabitEthernet3/15	6	1000	58:8d:09:e1:a9:ae	1	2	\N	t	\N	antarcdisc-ilo	143	\N	40	f	\N	\N	\N	\N
390	2	28	73	Gi3/17	GigabitEthernet3/17	6	100	58:8d:09:e1:a9:b0	1	1	\N	t	\N	trd-lgw1-ilo.uninett.no	145	\N	40	f	f	\N	\N	\N
392	2	28	75	Gi3/19	GigabitEthernet3/19	6	100	58:8d:09:e1:a9:b2	1	1	\N	t	\N	trd-agw1-ilo	147	\N	40	f	f	\N	\N	\N
393	2	28	76	Gi3/20	GigabitEthernet3/20	6	1000	58:8d:09:e1:a9:b3	2	2	\N	t	\N	skal ikke brukes pga overbooking	148	\N	45	f	\N	\N	\N	\N
395	2	28	78	Gi3/22	GigabitEthernet3/22	6	1000	58:8d:09:e1:a9:b5	2	2	\N	t	\N	skal ikke brukes pga overbooking	150	\N	45	f	\N	\N	\N	\N
397	2	28	80	Gi3/24	GigabitEthernet3/24	6	1000	58:8d:09:e1:a9:b7	2	2	\N	t	\N	skal ikke brukes pga overbooking	152	\N	45	f	\N	\N	\N	\N
398	2	28	81	Gi3/25	GigabitEthernet3/25	6	1000	58:8d:09:e1:a9:b8	1	2	\N	t	\N	lokal link for replisering, antarcdisc.uninett.no	153	\N	444	f	\N	\N	\N	\N
401	2	28	84	Gi3/28	GigabitEthernet3/28	6	1000	58:8d:09:e1:a9:bb	2	2	\N	t	\N		156	\N	1	f	\N	\N	\N	\N
402	2	28	85	Gi3/29	GigabitEthernet3/29	6	1000	58:8d:09:e1:a9:bc	1	1	\N	t	\N	trd-tgw1.uh.uninett.no.	157	\N	150	f	f	\N	\N	\N
404	2	28	87	Gi3/31	GigabitEthernet3/31	6	1000	58:8d:09:e1:a9:be	2	2	\N	t	\N	lokal link for replisering, qnap.uninett.no	159	\N	444	f	\N	\N	\N	\N
407	2	28	90	Gi3/34	GigabitEthernet3/34	6	1000	58:8d:09:e1:a9:c1	1	1	\N	t	\N	lokal link, blaasal-sw.nova-sw-1	162	\N	1	t	f	\N	\N	\N
409	2	28	92	Gi3/36	GigabitEthernet3/36	6	1000	58:8d:09:e1:a9:c3	1	1	\N	t	\N	lokal link, blaasal-sw.nova-sw-2	164	\N	1	t	f	\N	\N	\N
411	2	28	94	Gi3/38	GigabitEthernet3/38	6	1000	58:8d:09:e1:a9:c5	2	2	\N	t	\N		166	\N	1	f	\N	\N	\N	\N
413	2	28	96	Gi3/40	GigabitEthernet3/40	6	1000	58:8d:09:e1:a9:c7	2	2	\N	t	\N		168	\N	1	f	\N	\N	\N	\N
415	2	28	98	Gi3/42	GigabitEthernet3/42	6	1000	58:8d:09:e1:a9:c9	2	2	\N	t	\N		170	\N	1	f	\N	\N	\N	\N
417	2	28	100	Gi3/44	GigabitEthernet3/44	6	1000	58:8d:09:e1:a9:cb	2	2	\N	t	\N		172	\N	1	f	\N	\N	\N	\N
419	2	28	102	Gi3/46	GigabitEthernet3/46	6	1000	58:8d:09:e1:a9:cd	2	2	\N	t	\N		174	\N	1	f	\N	\N	\N	\N
421	2	28	104	Gi3/48	GigabitEthernet3/48	6	1000	58:8d:09:e1:a9:cf	2	2	\N	t	\N		176	\N	1	f	\N	\N	\N	\N
423	2	\N	106	Te4/2	TenGigabitEthernet4/2	6	10000	1c:df:0f:7e:36:8e	2	2	\N	t	\N	blaasal-sw.blaasalarkiv-sw	194	\N	1	t	f	\N	\N	\N
424	2	31	107	Te4/3	TenGigabitEthernet4/3	6	10000	1c:df:0f:7e:36:8f	1	1	\N	t	\N	lokal link, blaasal-sw.jatoba-bay1-x2, jatoba-bay1	195	\N	1	t	f	\N	\N	\N
426	2	31	109	Te4/5	TenGigabitEthernet4/5	6	10000	1c:df:0f:7e:36:91	1	2	\N	t	\N	lokal link, blaasal-sw.blaasal-rack2-sw-1	197	\N	1	t	f	\N	\N	\N
428	2	\N	111	Gi4/7	GigabitEthernet4/7	6	1000	1c:df:0f:7e:36:93	2	2	\N	t	\N		199	\N	1	f	f	\N	\N	\N
430	2	\N	113	Gi4/9	GigabitEthernet4/9	6	1000	1c:df:0f:7e:36:95	2	2	\N	t	\N		201	\N	1	f	f	\N	\N	\N
432	2	\N	115	Gi4/11	GigabitEthernet4/11	6	1000	1c:df:0f:7e:36:97	2	2	\N	t	\N		203	\N	1	f	f	\N	\N	\N
434	2	\N	117	Gi4/13	GigabitEthernet4/13	6	1000	1c:df:0f:7e:36:99	2	2	\N	t	\N		205	\N	1	f	f	\N	\N	\N
436	2	\N	119	Gi4/15	GigabitEthernet4/15	6	1000	1c:df:0f:7e:36:9b	2	2	\N	t	\N		207	\N	1	f	f	\N	\N	\N
438	2	\N	121	Gi4/17	GigabitEthernet4/17	6	1000	1c:df:0f:7e:36:9d	2	2	\N	t	\N		209	\N	1	f	f	\N	\N	\N
440	2	\N	123	Nu0	Null0	1	10000	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
441	2	\N	124	Vl1	Vlan1	53	1000	58:8d:09:7e:19:7f	2	2	\N	f	\N		\N	\N	1	\N	\N	\N	\N	\N
443	2	\N	126	VLAN-1002	unrouted VLAN 1002	53	0	58:8d:09:7e:19:69	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
446	2	\N	129	VLAN-1003	unrouted VLAN 1003	53	0	58:8d:09:7e:19:6a	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
449	2	\N	132	Po4	Port-channel4	53	3000	58:8d:09:dd:57:0c	1	1	\N	f	\N	lokal link, blaasal-sw.jatoba-bay5, jatoba-bay5	644	\N	1	t	\N	\N	\N	\N
451	2	\N	134	Vl5	Vlan5	53	1000	58:8d:09:7e:19:7f	1	1	\N	f	\N		\N	\N	5	\N	\N	\N	\N	\N
453	2	\N	136	VLAN-6	unrouted VLAN 6	53	0	58:8d:09:7e:19:45	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
456	2	\N	142	VLAN-20	unrouted VLAN 20	53	0	58:8d:09:7e:19:53	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
458	2	\N	144	VLAN-42	unrouted VLAN 42	53	0	58:8d:09:7e:19:69	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
461	2	\N	147	VLAN-70	unrouted VLAN 70	53	0	58:8d:09:7e:19:45	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
463	2	\N	149	VLAN-96	unrouted VLAN 96	53	0	58:8d:09:7e:19:5f	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
466	2	\N	152	VLAN-151	unrouted VLAN 151	53	0	58:8d:09:7e:19:56	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
469	2	\N	156	VLAN-22	unrouted VLAN 22	53	0	58:8d:09:7e:19:55	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
471	2	\N	158	VLAN-50	unrouted VLAN 50	53	0	58:8d:09:7e:19:71	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
474	2	\N	161	VLAN-195	unrouted VLAN 195	53	0	58:8d:09:7e:19:42	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
477	2	\N	164	VLAN-81	unrouted VLAN 81	53	0	58:8d:09:7e:19:50	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
478	2	\N	165	Po6	Port-channel6	53	100	00:00:00:00:00:00	1	2	\N	f	\N	local link, blaasal-sw.blaasal-rack2-sw	646	\N	1	t	\N	\N	\N	\N
483	3	34	3	Gi1/3	GigabitEthernet1/3	6	1000	00:22:55:f8:9b:0e	1	2	\N	t	\N	lokal link, uninett-gsw2.blaasal-sw-3	3	\N	1	t	\N	\N	\N	\N
485	3	34	5	Gi1/5	GigabitEthernet1/5	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
487	3	34	7	Gi1/7	GigabitEthernet1/7	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
489	3	34	9	Gi1/9	GigabitEthernet1/9	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
490	3	34	10	Gi1/10	GigabitEthernet1/10	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
492	3	34	12	Gi1/12	GigabitEthernet1/12	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
494	3	34	14	Gi1/14	GigabitEthernet1/14	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
496	3	34	16	Gi1/16	GigabitEthernet1/16	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
498	3	34	18	Gi1/18	GigabitEthernet1/18	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
499	3	34	19	Gi1/19	GigabitEthernet1/19	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
501	3	34	21	Gi1/21	GigabitEthernet1/21	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
505	3	34	25	Gi1/25	GigabitEthernet1/25	6	1000	00:22:55:f8:9b:24	2	2	\N	t	\N	test RA-guard	25	\N	1	f	\N	\N	\N	\N
507	3	34	27	Gi1/27	GigabitEthernet1/27	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
510	3	34	30	Gi1/30	GigabitEthernet1/30	6	1000	00:22:55:f8:9b:2e	1	1	\N	t	\N	lokal lacp, uninett-gsw2.uninett-gsw1-phy1	\N	\N	\N	\N	f	\N	\N	\N
512	3	34	32	Gi1/32	GigabitEthernet1/32	6	1000	00:22:55:f8:9b:2e	1	1	\N	t	\N	lokal fiber, blaasal-trd2, trd-gw7	\N	\N	\N	\N	f	\N	\N	\N
514	3	\N	34	EO0/0	EOBC0/0	53	100	00:00:21:00:00:00	1	1	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
515	3	\N	35	Nu0	Null0	1	10000	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
517	3	\N	37	SPAN SP	SPAN SP Interface	1	10000	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
518	3	\N	38	Lo0	Loopback0	24	8000	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
520	3	\N	40	Po3	Port-channel3	53	1000	00:22:55:f8:9b:2e	1	1	\N	f	\N	lokal lacp, uninett-gsw2.uninett-gsw1	\N	\N	\N	\N	\N	\N	\N	\N
522	3	\N	42	Vl6	Vlan6	53	1000	00:22:55:f8:9b:2e	1	1	\N	f	\N	VRRP ethernet, uninett2.uninettbladserv-HostOSManagement	\N	\N	6	\N	\N	\N	\N	\N
524	3	\N	44	Vl11	Vlan11	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	11	\N	\N	\N	\N	\N
526	3	\N	46	Vl15	Vlan15	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	15	\N	\N	\N	\N	\N
527	3	\N	47	Vl20	Vlan20	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	20	\N	\N	\N	\N	\N
529	3	\N	49	Vl22	Vlan22	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N	vrrp ethernet, uninett.uninett2-labnett4etg	\N	\N	22	\N	\N	\N	\N	\N
531	3	\N	51	Vl30	Vlan30	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	30	\N	\N	\N	\N	\N
533	3	\N	53	Vl35	Vlan35	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	35	\N	\N	\N	\N	\N
535	3	\N	55	Vl45	Vlan45	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	45	\N	\N	\N	\N	\N
536	3	\N	56	Vl50	Vlan50	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	50	\N	\N	\N	\N	\N
537	3	\N	57	Vl51	Vlan51	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	51	\N	\N	\N	\N	\N
539	3	\N	59	Vl60	Vlan60	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	60	\N	\N	\N	\N	\N
540	3	\N	60	Vl61	Vlan61	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	61	\N	\N	\N	\N	\N
542	3	\N	62	Vl66	Vlan66	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	66	\N	\N	\N	\N	\N
544	3	\N	64	Vl85	Vlan85	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	85	\N	\N	\N	\N	\N
545	3	\N	65	Vl89	Vlan89	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	89	\N	\N	\N	\N	\N
547	3	\N	67	Vl102	Vlan102	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	102	\N	\N	\N	\N	\N
548	3	\N	68	Vl108	Vlan108	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	108	\N	\N	\N	\N	\N
550	3	\N	70	Vl130	Vlan130	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	130	\N	\N	\N	\N	\N
552	3	\N	72	Vl190	Vlan190	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	190	\N	\N	\N	\N	\N
553	3	\N	73	Vl194	Vlan194	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	194	\N	\N	\N	\N	\N
554	3	\N	74	Vl195	Vlan195	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	195	\N	\N	\N	\N	\N
556	3	\N	76	Vl198	Vlan198	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	198	\N	\N	\N	\N	\N
558	3	\N	79	Vl333	Vlan333	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	333	\N	\N	\N	\N	\N
559	3	\N	80	Tu0	Tunnel0	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
561	3	\N	83	VLAN-1	unrouted VLAN 1	53	0	00:22:55:f8:9b:2f	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
563	3	\N	85	VLAN-1004	unrouted VLAN 1004	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
564	3	\N	86	VLAN-1005	unrouted VLAN 1005	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
566	3	\N	88	VLAN-5	unrouted VLAN 5	53	0	00:22:55:f8:9b:33	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
567	3	\N	89	VLAN-6	unrouted VLAN 6	53	0	00:22:55:f8:9b:34	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
569	3	\N	91	VLAN-15	unrouted VLAN 15	53	0	00:22:55:f8:9b:3d	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
571	3	\N	93	VLAN-17	unrouted VLAN 17	53	0	00:22:55:f8:9b:3f	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
572	3	\N	94	VLAN-20	unrouted VLAN 20	53	0	00:22:55:f8:9b:42	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
574	3	\N	96	VLAN-22	unrouted VLAN 22	53	0	00:22:55:f8:9b:44	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
576	3	\N	98	VLAN-30	unrouted VLAN 30	53	0	00:22:55:f8:9b:4c	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
577	3	\N	99	VLAN-31	unrouted VLAN 31	53	0	00:22:55:f8:9b:4d	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
579	3	\N	101	VLAN-40	unrouted VLAN 40	53	0	00:22:55:f8:9b:56	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
580	3	\N	102	VLAN-42	unrouted VLAN 42	53	0	00:22:55:f8:9b:58	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
582	3	\N	106	VLAN-60	unrouted VLAN 60	53	0	00:22:55:f8:9b:6a	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
584	3	\N	108	VLAN-62	unrouted VLAN 62	53	0	00:22:55:f8:9b:6c	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
585	3	\N	109	VLAN-64	unrouted VLAN 64	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
587	3	\N	111	VLAN-70	unrouted VLAN 70	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
588	3	\N	112	VLAN-83	unrouted VLAN 83	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
590	3	\N	114	VLAN-89	unrouted VLAN 89	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
592	3	\N	116	VLAN-95	unrouted VLAN 95	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
593	3	\N	117	VLAN-96	unrouted VLAN 96	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
595	3	\N	119	VLAN-102	unrouted VLAN 102	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
596	3	\N	120	VLAN-108	unrouted VLAN 108	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
598	3	\N	122	VLAN-130	unrouted VLAN 130	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
600	3	\N	124	VLAN-171	unrouted VLAN 171	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
601	3	\N	125	VLAN-190	unrouted VLAN 190	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
603	3	\N	127	VLAN-501	unrouted VLAN 501	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
605	3	\N	129	VLAN-504	unrouted VLAN 504	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
606	3	\N	130	VLAN-506	unrouted VLAN 506	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
608	3	\N	132	Tu1	Tunnel1	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
609	3	\N	133	Tu2	Tunnel2	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
610	3	\N	134	Tu3	Tunnel3	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
612	3	\N	136	Tu5	Tunnel5	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
486	3	34	6	Gi1/6	GigabitEthernet1/6	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
488	3	34	8	Gi1/8	GigabitEthernet1/8	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
491	3	34	11	Gi1/11	GigabitEthernet1/11	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
493	3	34	13	Gi1/13	GigabitEthernet1/13	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
495	3	34	15	Gi1/15	GigabitEthernet1/15	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
497	3	34	17	Gi1/17	GigabitEthernet1/17	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
500	3	34	20	Gi1/20	GigabitEthernet1/20	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
502	3	34	22	Gi1/22	GigabitEthernet1/22	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
503	3	34	23	Gi1/23	GigabitEthernet1/23	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
504	3	34	24	Gi1/24	GigabitEthernet1/24	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
506	3	34	26	Gi1/26	GigabitEthernet1/26	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
508	3	34	28	Gi1/28	GigabitEthernet1/28	6	1000	00:22:55:f8:9b:2e	2	2	\N	t	\N		\N	\N	\N	\N	\N	\N	\N	\N
509	3	34	29	Gi1/29	GigabitEthernet1/29	6	1000	00:22:55:f8:9b:2e	1	2	\N	t	\N	lokal lacp, uninett-gsw2.uninett-gsw1-phy2	\N	\N	\N	\N	f	\N	\N	\N
513	3	\N	33	Vl1	Vlan1	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	1	\N	\N	\N	\N	\N
516	3	\N	36	SPAN RP	SPAN RP Interface	1	10000	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
521	3	\N	41	Vl5	Vlan5	53	1000	00:22:55:f8:9b:2e	1	1	\N	f	\N	VRRP ethernet, uninett2.uninettbladserv-management	\N	\N	5	\N	\N	\N	\N	\N
523	3	\N	43	Vl8	Vlan8	53	1000	00:22:55:f8:9b:2e	1	1	\N	f	\N	VRRP ethernet, uninett2.uninettbladserv-GuestOS	\N	\N	8	\N	\N	\N	\N	\N
525	3	\N	45	Vl12	Vlan12	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	12	\N	\N	\N	\N	\N
528	3	\N	48	Vl21	Vlan21	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	21	\N	\N	\N	\N	\N
530	3	\N	50	Vl25	Vlan25	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	25	\N	\N	\N	\N	\N
532	3	\N	52	Vl31	Vlan31	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	31	\N	\N	\N	\N	\N
534	3	\N	54	Vl40	Vlan40	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N	VRRP ethernet, uninett2.uninett-mgmt	\N	\N	40	\N	\N	\N	\N	\N
538	3	\N	58	Vl52	Vlan52	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	52	\N	\N	\N	\N	\N
541	3	\N	61	Vl64	Vlan64	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	64	\N	\N	\N	\N	\N
543	3	\N	63	Vl70	Vlan70	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	70	\N	\N	\N	\N	\N
546	3	\N	66	Vl99	Vlan99	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	99	\N	\N	\N	\N	\N
549	3	\N	69	Vl109	Vlan109	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N	lokal vlan, uninett2.uninett-halab	\N	\N	109	\N	\N	\N	\N	\N
551	3	\N	71	Vl131	Vlan131	53	1000	00:22:55:f8:9b:2e	1	1	\N	f	\N	lokal vlan, uninett2.uninett-sip-server	\N	\N	131	\N	\N	\N	\N	\N
555	3	\N	75	Vl197	Vlan197	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	197	\N	\N	\N	\N	\N
557	3	\N	78	Vl201	Vlan201	53	1000	00:22:55:f8:9b:2e	2	2	\N	f	\N		\N	\N	201	\N	\N	\N	\N	\N
560	3	\N	81	CPP	Control Plane Interface	1	10000	00:00:00:00:00:00	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
562	3	\N	84	VLAN-1002	unrouted VLAN 1002	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
565	3	\N	87	VLAN-1003	unrouted VLAN 1003	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
568	3	\N	90	VLAN-8	unrouted VLAN 8	53	0	00:22:55:f8:9b:36	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
570	3	\N	92	VLAN-16	unrouted VLAN 16	53	0	00:22:55:f8:9b:3e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
573	3	\N	95	VLAN-21	unrouted VLAN 21	53	0	00:22:55:f8:9b:43	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
575	3	\N	97	VLAN-25	unrouted VLAN 25	53	0	00:22:55:f8:9b:47	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
578	3	\N	100	VLAN-35	unrouted VLAN 35	53	0	00:22:55:f8:9b:51	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
581	3	\N	103	VLAN-45	unrouted VLAN 45	53	0	00:22:55:f8:9b:5b	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
583	3	\N	107	VLAN-61	unrouted VLAN 61	53	0	00:22:55:f8:9b:6b	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
586	3	\N	110	VLAN-66	unrouted VLAN 66	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
589	3	\N	113	VLAN-85	unrouted VLAN 85	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
591	3	\N	115	VLAN-90	unrouted VLAN 90	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
594	3	\N	118	VLAN-98	unrouted VLAN 98	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
597	3	\N	121	VLAN-109	unrouted VLAN 109	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
599	3	\N	123	VLAN-131	unrouted VLAN 131	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
602	3	\N	126	VLAN-500	unrouted VLAN 500	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
604	3	\N	128	VLAN-503	unrouted VLAN 503	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
607	3	\N	131	VLAN-555	unrouted VLAN 555	53	0	00:22:55:f8:9b:2e	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
611	3	\N	135	Tu4	Tunnel4	131	0.100000000000000006	\N	1	1	\N	f	\N		\N	\N	\N	\N	\N	\N	\N	\N
484	3	34	4	Gi1/4	GigabitEthernet1/4	6	1000	00:22:55:f8:9b:0f	1	1	\N	t	\N	lokal link, uninett-gsw2.blaasal-sw-4	\N	\N	1	t	f	2	329	\N
450	2	\N	133	Po5	Port-channel5	53	20000	58:8d:09:7e:19:41	1	1	\N	f	\N	Fiber, blaasalen-teknobyen-sw, teknobyen-sw	645	\N	1	t	\N	\N	\N	\N
511	3	34	31	Gi1/31	GigabitEthernet1/31	6	1000	00:22:55:f8:9b:2e	1	1	\N	t	\N	lokal fiber, blaasal-teknobyen2, uninett-gsw1	\N	\N	\N	\N	f	\N	\N	\N
\.


--
-- Name: interface_interfaceid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('interface_interfaceid_seq', 1104, true);


--
-- Data for Name: interface_stack; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY interface_stack (id, higher, lower) FROM stdin;
5	448	332
6	450	321
7	447	326
8	447	328
9	478	426
10	448	336
11	447	327
12	478	427
13	449	340
14	449	342
15	447	329
16	449	338
17	448	334
18	450	320
19	519	484
20	520	510
21	519	482
22	519	481
\.


--
-- Name: interface_stack_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('interface_stack_id_seq', 82, true);


--
-- Data for Name: ipdevpoll_job_log; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY ipdevpoll_job_log (id, netboxid, job_name, end_time, duration, success, "interval") FROM stdin;
176	3	1minstats	2015-05-06 11:25:20.695055	0.0969669999999999976	t	60
179	2	5minstats	2015-05-06 11:25:21.335469	0.760546999999999973	t	300
181	3	snmpcheck	2015-05-06 11:26:20.609675	0.0618770000000000014	t	1800
184	3	1minstats	2015-05-06 11:26:21.086637	0.535075999999999996	t	60
185	3	ip2mac	2015-05-06 11:26:21.192141	0.649252000000000051	t	1800
193	3	1minstats	2015-05-06 11:28:20.850072	0.298657999999999979	t	60
194	3	topo	2015-05-06 11:28:45.16659	5.88654600000000006	t	900
196	3	1minstats	2015-05-06 11:29:20.881224	0.329266000000000003	t	60
10	2	ip2mac	2015-05-06 10:38:20.488684	0.000173000000000000004	\N	1800
11	2	snmpcheck	2015-05-06 10:38:20.553732	0.0631000000000000033	t	1800
12	2	topo	2015-05-06 10:38:20.606067	0.0510460000000000011	\N	900
13	2	dns	2015-05-06 10:38:20.662659	0.176712000000000008	t	600
205	2	5minstats	2015-05-06 11:30:21.485623	0.889519999999999977	t	300
16	2	5minstats	2015-05-06 10:38:21.289152	0.796989999999999976	t	300
17	2	linkcheck	2015-05-06 10:38:21.48646	0.992945999999999995	t	300
18	2	inventory	2015-05-06 10:38:22.922235	2.43784799999999979	t	21600
21	2	ip2mac	2015-05-06 10:40:20.491514	0.000111999999999999998	\N	1800
22	2	snmpcheck	2015-05-06 10:40:20.569913	0.0667039999999999994	t	1800
23	2	dns	2015-05-06 10:40:20.631159	0.138584000000000013	t	600
25	2	linkcheck	2015-05-06 10:40:20.953542	0.459274000000000016	t	300
215	3	5minstats	2015-05-06 11:31:22.053957	1.48201200000000011	t	300
27	2	5minstats	2015-05-06 10:40:21.446643	0.944494999999999973	t	300
28	2	topo	2015-05-06 10:40:22.358162	1.72156900000000013	t	900
29	2	inventory	2015-05-06 10:40:23.012529	2.57293199999999977	t	21600
217	2	1minstats	2015-05-06 11:32:20.819155	0.0899319999999999981	t	60
221	3	1minstats	2015-05-06 11:33:20.903455	0.29281299999999999	t	60
226	2	1minstats	2015-05-06 11:34:20.81549	0.0860759999999999997	t	60
229	3	topo	2015-05-06 11:34:32.310082	6.11676299999999973	t	900
232	2	1minstats	2015-05-06 11:35:20.980023	0.170558999999999988	t	60
41	2	linkcheck	2015-05-06 10:45:20.772115	0.274494999999999989	t	300
42	2	5minstats	2015-05-06 10:45:21.057247	0.559420999999999946	t	300
237	3	dns	2015-05-06 11:36:20.681785	0.121586	t	600
239	3	1minstats	2015-05-06 11:36:21.097601	0.485572999999999977	t	60
258	2	1minstats	2015-05-06 11:39:20.845212	0.0867480000000000057	t	60
260	2	ip2mac	2015-05-06 11:40:20.56304	0.000110000000000000004	\N	1800
269	2	5minstats	2015-05-06 11:40:21.420309	0.655769000000000046	t	300
55	2	dns	2015-05-06 10:50:20.573387	0.0781870000000000065	t	600
57	2	linkcheck	2015-05-06 10:50:20.803321	0.304487000000000008	t	300
58	2	5minstats	2015-05-06 10:50:21.081802	0.583725999999999967	t	300
275	2	1minstats	2015-05-06 11:41:20.8528	0.0838409999999999989	t	60
277	3	1minstats	2015-05-06 11:41:21.232759	0.464220000000000022	t	60
284	2	1minstats	2015-05-06 11:44:20.859026	0.085768999999999998	t	60
286	2	1minstats	2015-05-06 11:45:20.87713	0.102532999999999999	t	60
288	3	1minstats	2015-05-06 11:45:21.113925	0.340088999999999975	t	60
295	3	topo	2015-05-06 11:46:34.731787	5.62960599999999989	t	900
297	3	1minstats	2015-05-06 11:47:21.064032	0.292827999999999977	t	60
72	2	linkcheck	2015-05-06 10:55:20.816843	0.318394999999999984	t	300
298	2	1minstats	2015-05-06 11:48:20.859385	0.0833200000000000052	t	60
74	2	5minstats	2015-05-06 10:55:21.29446	0.794417999999999958	t	300
75	2	topo	2015-05-06 10:55:21.81613	1.31009099999999989	t	900
300	2	topo	2015-05-06 11:48:35.590861	0.87964500000000001	t	900
302	3	1minstats	2015-05-06 11:49:21.107444	0.334986000000000006	t	60
304	2	1minstats	2015-05-06 11:50:20.925128	0.14760899999999999	t	60
312	2	1minstats	2015-05-06 11:52:20.860538	0.0828279999999999988	t	60
314	2	1minstats	2015-05-06 11:53:20.859551	0.0816640000000000005	t	60
317	3	1minstats	2015-05-06 11:54:21.059066	0.283445999999999976	t	60
319	2	linkcheck	2015-05-06 11:55:21.038881	0.271855999999999987	t	300
87	2	dns	2015-05-06 11:00:20.653904	0.138756999999999991	t	600
89	2	linkcheck	2015-05-06 11:00:20.850643	0.33463900000000002	t	300
90	2	5minstats	2015-05-06 11:00:21.160278	0.643592999999999971	t	300
328	3	5minstats	2015-05-06 11:56:22.068688	1.37854600000000005	t	300
330	3	1minstats	2015-05-06 11:57:21.07816	0.286250999999999978	t	60
332	3	1minstats	2015-05-06 11:58:21.077593	0.288777000000000006	t	60
334	3	1minstats	2015-05-06 11:59:21.068744	0.277388000000000023	t	60
339	2	5minstats	2015-05-06 12:00:21.400512	0.632938000000000001	t	300
341	3	1minstats	2015-05-06 12:01:21.247122	0.407785000000000009	t	60
342	3	linkcheck	2015-05-06 12:01:21.416124	0.727362999999999982	t	300
103	2	linkcheck	2015-05-06 11:05:20.788845	0.271851999999999983	t	300
104	2	5minstats	2015-05-06 11:05:21.046515	0.529364999999999974	t	300
349	2	topo	2015-05-06 12:03:35.621421	0.899116000000000026	t	900
355	2	5minstats	2015-05-06 12:05:21.334128	0.565616000000000008	t	300
361	2	1minstats	2015-05-06 12:07:20.9299	0.0870149999999999951	t	60
364	3	1minstats	2015-05-06 12:08:21.120753	0.281833	t	60
366	3	1minstats	2015-05-06 12:09:21.146872	0.307782	t	60
367	2	ip2mac	2015-05-06 12:10:20.564637	0.00020699999999999999	\N	1800
368	2	snmpcheck	2015-05-06 12:10:20.621414	0.0550889999999999991	t	1800
370	2	1minstats	2015-05-06 12:10:20.965533	0.113727999999999996	t	60
376	3	linkcheck	2015-05-06 12:11:21.419957	0.730160000000000031	t	300
177	2	1minstats	2015-05-06 11:25:20.815057	0.117371000000000003	t	60
182	3	dns	2015-05-06 11:26:20.670119	0.125919000000000003	t	600
187	3	5minstats	2015-05-06 11:26:25.291778	4.74441100000000038	t	300
195	2	1minstats	2015-05-06 11:29:20.790407	0.0893580000000000069	t	60
202	2	linkcheck	2015-05-06 11:30:21.083725	0.433740999999999988	t	300
210	2	topo	2015-05-06 11:30:48.265942	0.87362200000000001	t	900
216	3	topo	2015-05-06 11:31:35.012753	5.91364900000000038	t	900
230	2	linkcheck	2015-05-06 11:35:20.811825	0.215245999999999993	t	300
242	3	5minstats	2015-05-06 11:36:21.985668	1.41332400000000002	t	300
243	2	1minstats	2015-05-06 11:37:20.822897	0.0890790000000000054	t	60
259	3	1minstats	2015-05-06 11:39:20.99469	0.315367999999999982	t	60
263	2	snmpcheck	2015-05-06 11:40:20.761617	0.197930999999999996	t	1800
278	3	linkcheck	2015-05-06 11:41:21.400729	0.787221999999999977	t	300
280	2	1minstats	2015-05-06 11:42:20.846462	0.0756659999999999971	t	60
282	2	1minstats	2015-05-06 11:43:20.857454	0.084420999999999996	t	60
293	3	linkcheck	2015-05-06 11:46:21.369516	0.738847000000000032	t	300
294	3	5minstats	2015-05-06 11:46:21.959515	1.32724200000000003	t	300
299	3	1minstats	2015-05-06 11:48:21.064605	0.292879999999999974	t	60
303	2	dns	2015-05-06 11:50:20.844057	0.0802810000000000051	t	600
307	2	5minstats	2015-05-06 11:50:21.390859	0.624371000000000009	t	300
308	2	1minstats	2015-05-06 11:51:20.863442	0.0853229999999999961	t	60
309	3	1minstats	2015-05-06 11:51:21.201876	0.42417100000000002	t	60
320	3	1minstats	2015-05-06 11:55:21.115135	0.338563999999999976	t	60
322	3	snmpcheck	2015-05-06 11:56:20.60438	0.0561200000000000032	t	1800
323	3	dns	2015-05-06 11:56:20.688029	0.0822279999999999955	t	600
325	2	1minstats	2015-05-06 11:56:20.872227	0.0805529999999999996	t	60
337	2	linkcheck	2015-05-06 12:00:21.07415	0.305176999999999976	t	300
340	2	1minstats	2015-05-06 12:01:20.934066	0.0934809999999999947	t	60
343	3	5minstats	2015-05-06 12:01:22.015044	1.32498099999999996	t	300
346	3	1minstats	2015-05-06 12:02:21.123877	0.287059999999999982	t	60
351	3	1minstats	2015-05-06 12:04:21.123135	0.284835999999999978	t	60
360	3	5minstats	2015-05-06 12:06:21.988141	1.29783800000000005	t	300
362	3	1minstats	2015-05-06 12:07:21.130344	0.291358999999999979	t	60
363	2	1minstats	2015-05-06 12:08:20.925712	0.0831149999999999944	t	60
365	2	1minstats	2015-05-06 12:09:20.930514	0.0874619999999999981	t	60
371	2	linkcheck	2015-05-06 12:10:21.082929	0.31643300000000002	t	300
378	2	1minstats	2015-05-06 12:12:20.940661	0.0863880000000000065	t	60
380	2	1minstats	2015-05-06 12:13:20.939437	0.0840380000000000016	t	60
386	3	1minstats	2015-05-06 12:15:21.187548	0.32946700000000001	t	60
389	2	1minstats	2015-05-06 12:16:20.933545	0.078453999999999996	t	60
394	2	1minstats	2015-05-06 12:17:20.942056	0.0864589999999999942	t	60
396	2	1minstats	2015-05-06 12:18:20.931834	0.076097999999999999	t	60
404	3	1minstats	2015-05-06 12:20:21.160238	0.300582999999999989	t	60
405	2	5minstats	2015-05-06 12:20:21.405606	0.636319999999999997	t	300
407	3	1minstats	2015-05-06 12:21:21.248746	0.391826000000000008	t	60
418	2	5minstats	2015-05-06 12:25:21.270941	0.501066000000000011	t	300
421	3	dns	2015-05-06 12:26:20.678833	0.0722499999999999948	t	600
423	2	1minstats	2015-05-06 12:26:20.952367	0.0875129999999999936	t	60
427	2	1minstats	2015-05-06 12:27:20.952577	0.0865960000000000063	t	60
429	2	1minstats	2015-05-06 12:28:20.951964	0.0852989999999999998	t	60
431	2	1minstats	2015-05-06 12:29:20.95102	0.0842790000000000067	t	60
433	2	dns	2015-05-06 12:30:20.846093	0.0801820000000000033	t	600
436	3	1minstats	2015-05-06 12:30:21.145042	0.286507999999999985	t	60
437	2	5minstats	2015-05-06 12:30:21.38204	0.612048000000000036	t	300
439	3	1minstats	2015-05-06 12:31:21.268471	0.410073000000000021	t	60
440	3	linkcheck	2015-05-06 12:31:21.418773	0.718771000000000049	t	300
442	3	topo	2015-05-06 12:31:35.077462	5.95840899999999962	t	900
444	3	1minstats	2015-05-06 12:32:21.151592	0.291907000000000028	t	60
446	3	1minstats	2015-05-06 12:33:21.156163	0.296246999999999983	t	60
447	2	topo	2015-05-06 12:33:35.690753	0.943004999999999982	t	900
450	2	linkcheck	2015-05-06 12:35:20.984968	0.216400000000000009	t	300
451	2	1minstats	2015-05-06 12:35:21.05379	0.182683000000000012	t	60
455	2	1minstats	2015-05-06 12:36:20.955895	0.0876929999999999932	t	60
459	2	1minstats	2015-05-06 12:37:20.955679	0.0864909999999999984	t	60
467	2	dns	2015-05-06 12:40:20.83956	0.0734729999999999966	t	600
472	2	1minstats	2015-05-06 12:41:20.955142	0.0856159999999999977	t	60
474	3	linkcheck	2015-05-06 12:41:21.406099	0.706035999999999997	t	300
475	3	5minstats	2015-05-06 12:41:21.986131	1.28434699999999991	t	300
476	2	1minstats	2015-05-06 12:42:20.956818	0.085883000000000001	t	60
478	2	1minstats	2015-05-06 12:43:20.953386	0.082511000000000001	t	60
482	2	linkcheck	2015-05-06 12:45:20.959507	0.190350999999999992	t	300
484	3	1minstats	2015-05-06 12:45:21.246931	0.381819999999999993	t	60
487	2	1minstats	2015-05-06 12:46:20.953698	0.083406999999999995	t	60
489	3	linkcheck	2015-05-06 12:46:21.42982	0.729060999999999959	t	300
490	3	5minstats	2015-05-06 12:46:22.022579	1.3207040000000001	t	300
494	2	1minstats	2015-05-06 12:48:20.955789	0.0847409999999999969	t	60
495	3	1minstats	2015-05-06 12:48:21.195849	0.328890999999999989	t	60
497	2	1minstats	2015-05-06 12:49:20.962719	0.0908989999999999937	t	60
499	2	dns	2015-05-06 12:50:20.849249	0.0829799999999999982	t	600
502	3	1minstats	2015-05-06 12:50:21.171396	0.304756000000000027	t	60
503	2	5minstats	2015-05-06 12:50:21.408409	0.636987999999999999	t	300
504	2	1minstats	2015-05-06 12:51:20.962756	0.0907540000000000013	t	60
505	3	1minstats	2015-05-06 12:51:21.288739	0.421144000000000018	t	60
508	2	1minstats	2015-05-06 12:52:20.955247	0.0825980000000000047	t	60
510	2	1minstats	2015-05-06 12:53:20.957069	0.0842849999999999988	t	60
512	2	1minstats	2015-05-06 12:54:20.96032	0.0873239999999999988	t	60
515	2	1minstats	2015-05-06 12:55:21.06087	0.186497999999999997	t	60
517	2	5minstats	2015-05-06 12:55:21.37898	0.607257000000000047	t	300
519	3	ip2mac	2015-05-06 12:56:20.708084	0.162781000000000009	t	1800
521	2	1minstats	2015-05-06 12:56:20.96811	0.093864000000000003	t	60
523	3	linkcheck	2015-05-06 12:56:21.491493	0.780545000000000044	t	300
525	2	1minstats	2015-05-06 12:57:20.958439	0.0836859999999999965	t	60
527	2	1minstats	2015-05-06 12:58:20.956111	0.0809060000000000057	t	60
528	3	1minstats	2015-05-06 12:58:21.154378	0.284069999999999989	t	60
529	2	1minstats	2015-05-06 12:59:20.959143	0.0836999999999999966	t	60
530	3	1minstats	2015-05-06 12:59:21.18302	0.312545000000000017	t	60
533	2	linkcheck	2015-05-06 13:00:21.069278	0.299051000000000011	t	300
535	2	5minstats	2015-05-06 13:00:21.408264	0.636634999999999951	t	300
536	2	1minstats	2015-05-06 13:01:20.962913	0.0870630000000000015	t	60
538	3	linkcheck	2015-05-06 13:01:21.627855	0.91889299999999996	t	300
539	3	5minstats	2015-05-06 13:01:22.264981	1.50115100000000012	t	300
543	2	1minstats	2015-05-06 13:03:20.964907	0.089037000000000005	t	60
544	3	1minstats	2015-05-06 13:03:21.1669	0.294760000000000022	t	60
545	2	topo	2015-05-06 13:03:35.716065	0.946922999999999959	t	900
546	2	1minstats	2015-05-06 13:04:20.979926	0.103235999999999994	t	60
547	3	1minstats	2015-05-06 13:04:21.31486	0.442678000000000016	t	60
548	2	linkcheck	2015-05-06 13:05:21.00474	0.233797000000000005	t	300
178	2	linkcheck	2015-05-06 11:25:20.943455	0.369950000000000001	t	300
183	2	1minstats	2015-05-06 11:26:20.799158	0.0983210000000000056	t	60
186	3	linkcheck	2015-05-06 11:26:22.078078	1.53225599999999984	t	300
190	2	1minstats	2015-05-06 11:27:20.787933	0.0870739999999999986	t	60
201	2	1minstats	2015-05-06 11:30:20.838181	0.108560000000000004	t	60
211	2	1minstats	2015-05-06 11:31:20.817573	0.0893329999999999957	t	60
213	3	1minstats	2015-05-06 11:31:21.096122	0.501812999999999954	t	60
218	3	1minstats	2015-05-06 11:32:20.898059	0.303422000000000025	t	60
220	2	1minstats	2015-05-06 11:33:20.817582	0.0883239999999999997	t	60
224	2	topo	2015-05-06 11:33:57.709852	0.869107999999999992	t	900
228	3	1minstats	2015-05-06 11:34:21.072762	0.461867000000000028	t	60
231	3	1minstats	2015-05-06 11:35:20.897193	0.28562700000000002	t	60
234	2	5minstats	2015-05-06 11:35:21.295256	0.697845999999999966	t	300
244	3	1minstats	2015-05-06 11:37:20.914021	0.262448000000000015	t	60
251	2	1minstats	2015-05-06 11:38:20.839995	0.0809010000000000007	t	60
266	2	1minstats	2015-05-06 11:40:20.936852	0.167266999999999999	t	60
281	3	1minstats	2015-05-06 11:42:21.044444	0.274702999999999975	t	60
283	3	1minstats	2015-05-06 11:43:21.05036	0.279295999999999989	t	60
285	3	1minstats	2015-05-06 11:44:21.250113	0.478215000000000001	t	60
287	2	linkcheck	2015-05-06 11:45:21.047359	0.282133000000000023	t	300
289	2	5minstats	2015-05-06 11:45:21.364447	0.598122000000000043	t	300
291	2	1minstats	2015-05-06 11:46:20.874113	0.0986120000000000052	t	60
301	2	1minstats	2015-05-06 11:49:20.866879	0.0902339999999999948	t	60
306	3	1minstats	2015-05-06 11:50:21.155538	0.381601000000000024	t	60
310	3	linkcheck	2015-05-06 11:51:21.382923	0.705856999999999957	t	300
316	2	1minstats	2015-05-06 11:54:20.862586	0.0834740000000000065	t	60
318	2	1minstats	2015-05-06 11:55:20.881081	0.101698999999999998	t	60
321	2	5minstats	2015-05-06 11:55:21.351853	0.584180000000000033	t	300
326	3	1minstats	2015-05-06 11:56:21.219957	0.429205999999999976	t	60
338	3	1minstats	2015-05-06 12:00:21.165466	0.329249999999999987	t	60
344	3	topo	2015-05-06 12:01:34.878678	5.77087899999999987	t	900
345	2	1minstats	2015-05-06 12:02:20.925952	0.0863990000000000036	t	60
347	2	1minstats	2015-05-06 12:03:20.929065	0.0877229999999999954	t	60
350	2	1minstats	2015-05-06 12:04:20.925316	0.0832610000000000017	t	60
352	2	linkcheck	2015-05-06 12:05:20.960167	0.193543999999999994	t	300
353	2	1minstats	2015-05-06 12:05:21.0201	0.178463000000000011	t	60
356	3	dns	2015-05-06 12:06:20.687254	0.0814249999999999974	t	600
358	3	1minstats	2015-05-06 12:06:21.229151	0.392048000000000008	t	60
369	2	dns	2015-05-06 12:10:20.846611	0.0819089999999999957	t	600
372	3	1minstats	2015-05-06 12:10:21.170504	0.319155000000000022	t	60
374	2	1minstats	2015-05-06 12:11:20.942524	0.0872710000000000014	t	60
382	2	1minstats	2015-05-06 12:14:20.943136	0.0869579999999999936	t	60
384	2	linkcheck	2015-05-06 12:15:20.967735	0.200331000000000009	t	300
387	2	5minstats	2015-05-06 12:15:21.358023	0.589041000000000037	t	300
388	3	dns	2015-05-06 12:16:20.690745	0.0835660000000000014	t	600
390	3	1minstats	2015-05-06 12:16:21.296759	0.442363000000000006	t	60
392	3	5minstats	2015-05-06 12:16:22.118455	1.42539300000000013	t	300
397	3	1minstats	2015-05-06 12:18:21.137306	0.285131000000000023	t	60
398	2	topo	2015-05-06 12:18:35.659052	0.924092000000000025	t	900
400	3	1minstats	2015-05-06 12:19:21.153295	0.299980000000000024	t	60
406	2	1minstats	2015-05-06 12:21:20.949059	0.0854199999999999959	t	60
408	3	linkcheck	2015-05-06 12:21:21.409118	0.716940000000000022	t	300
410	2	1minstats	2015-05-06 12:22:20.947123	0.0835359999999999991	t	60
412	2	1minstats	2015-05-06 12:23:20.951761	0.0872750000000000054	t	60
415	3	1minstats	2015-05-06 12:24:21.150526	0.293387999999999982	t	60
417	2	1minstats	2015-05-06 12:25:21.046568	0.182740000000000014	t	60
422	3	ip2mac	2015-05-06 12:26:20.759135	0.215552999999999995	t	1800
424	3	1minstats	2015-05-06 12:26:21.287632	0.429559000000000024	t	60
428	3	1minstats	2015-05-06 12:27:21.151909	0.293534000000000017	t	60
434	2	1minstats	2015-05-06 12:30:20.969634	0.104185	t	60
441	3	5minstats	2015-05-06 12:31:22.008068	1.30699100000000001	t	300
443	2	1minstats	2015-05-06 12:32:20.954953	0.087451000000000001	t	60
445	2	1minstats	2015-05-06 12:33:20.952983	0.0847350000000000048	t	60
449	3	1minstats	2015-05-06 12:34:21.157904	0.297833999999999988	t	60
454	3	dns	2015-05-06 12:36:20.689196	0.0819980000000000014	t	600
456	3	1minstats	2015-05-06 12:36:21.264707	0.403648000000000007	t	60
458	3	5minstats	2015-05-06 12:36:22.018925	1.31783000000000006	t	300
460	3	1minstats	2015-05-06 12:37:21.159003	0.297735000000000027	t	60
465	2	ip2mac	2015-05-06 12:40:20.563441	0.000101000000000000002	\N	1800
468	2	1minstats	2015-05-06 12:40:20.968388	0.100415000000000004	t	60
470	3	1minstats	2015-05-06 12:40:21.16007	0.297103999999999979	t	60
471	2	5minstats	2015-05-06 12:40:21.407869	0.637379999999999947	t	300
473	3	1minstats	2015-05-06 12:41:21.247134	0.382728999999999986	t	60
477	3	1minstats	2015-05-06 12:42:21.159201	0.294634000000000007	t	60
479	3	1minstats	2015-05-06 12:43:21.157398	0.292547000000000001	t	60
480	2	1minstats	2015-05-06 12:44:20.952054	0.0815789999999999987	t	60
481	3	1minstats	2015-05-06 12:44:21.156729	0.291486999999999996	t	60
483	2	1minstats	2015-05-06 12:45:21.048	0.178259000000000001	t	60
485	2	5minstats	2015-05-06 12:45:21.359008	0.587861999999999996	t	300
486	3	dns	2015-05-06 12:46:20.689329	0.0824369999999999964	t	600
488	3	1minstats	2015-05-06 12:46:21.249272	0.383180999999999994	t	60
491	3	topo	2015-05-06 12:46:35.079392	5.95516600000000018	t	900
492	2	1minstats	2015-05-06 12:47:20.956179	0.0849179999999999935	t	60
493	3	1minstats	2015-05-06 12:47:21.151518	0.285144999999999982	t	60
496	2	topo	2015-05-06 12:48:35.792481	1.03270499999999998	t	900
498	3	1minstats	2015-05-06 12:49:21.15902	0.291795000000000027	t	60
500	2	1minstats	2015-05-06 12:50:20.975113	0.104717000000000005	t	60
501	2	linkcheck	2015-05-06 12:50:21.090301	0.319012999999999991	t	300
506	3	linkcheck	2015-05-06 12:51:21.459288	0.758349999999999969	t	300
507	3	5minstats	2015-05-06 12:51:22.044649	1.34194999999999998	t	300
509	3	1minstats	2015-05-06 12:52:21.155314	0.287596000000000018	t	60
511	3	1minstats	2015-05-06 12:53:21.158133	0.289773000000000003	t	60
513	3	1minstats	2015-05-06 12:54:21.156694	0.288038000000000016	t	60
514	2	linkcheck	2015-05-06 12:55:20.977277	0.207272000000000012	t	300
516	3	1minstats	2015-05-06 12:55:21.214324	0.34412100000000001	t	60
518	3	snmpcheck	2015-05-06 12:56:20.607115	0.0582179999999999989	t	1800
520	3	dns	2015-05-06 12:56:20.764426	0.156415999999999999	t	600
522	3	1minstats	2015-05-06 12:56:21.310218	0.440612999999999977	t	60
524	3	5minstats	2015-05-06 12:56:22.067265	1.30329800000000007	t	300
526	3	1minstats	2015-05-06 12:57:21.156515	0.28654099999999999	t	60
531	2	dns	2015-05-06 13:00:20.851588	0.0844359999999999972	t	600
532	2	1minstats	2015-05-06 13:00:20.967713	0.093972	t	60
534	3	1minstats	2015-05-06 13:00:21.153266	0.283411000000000024	t	60
537	3	1minstats	2015-05-06 13:01:21.543879	0.672178000000000053	t	60
540	3	topo	2015-05-06 13:01:35.416482	6.2886829999999998	t	900
541	2	1minstats	2015-05-06 13:02:20.966696	0.0895959999999999951	t	60
542	3	1minstats	2015-05-06 13:02:21.168072	0.296140999999999988	t	60
180	2	topo	2015-05-06 11:25:21.679744	1.16399699999999995	f	900
188	3	topo	2015-05-06 11:26:29.083409	8.41643900000000045	f	900
189	3	inventory	2015-05-06 11:26:29.999442	9.45710399999999929	t	21600
191	3	1minstats	2015-05-06 11:27:20.888809	0.337594999999999978	t	60
192	2	1minstats	2015-05-06 11:28:20.785401	0.0852750000000000036	t	60
120	2	ip2mac	2015-05-06 11:10:20.507276	0.000100000000000000005	\N	1800
121	2	snmpcheck	2015-05-06 11:10:20.568387	0.0593240000000000017	t	1800
122	2	dns	2015-05-06 11:10:20.653468	0.0832149999999999973	t	600
124	2	linkcheck	2015-05-06 11:10:20.936633	0.365124000000000004	t	300
125	2	5minstats	2015-05-06 11:10:21.350334	0.778020000000000045	t	300
200	2	dns	2015-05-06 11:30:20.722798	0.12937499999999999	t	600
127	2	topo	2015-05-06 11:10:21.855755	1.34231199999999995	t	900
203	3	1minstats	2015-05-06 11:30:21.086418	0.485594999999999999	t	60
214	3	linkcheck	2015-05-06 11:31:21.442216	0.871255000000000002	t	300
223	2	topo	2015-05-06 11:33:35.511087	0.812312999999999952	t	900
238	2	1minstats	2015-05-06 11:36:20.825131	0.0919159999999999977	t	60
138	2	linkcheck	2015-05-06 11:15:20.782405	0.208668999999999993	t	300
140	2	5minstats	2015-05-06 11:15:21.158056	0.58353900000000003	t	300
241	3	linkcheck	2015-05-06 11:36:21.391175	0.820980000000000043	t	300
252	3	1minstats	2015-05-06 11:38:21.041939	0.283169999999999977	t	60
265	2	dns	2015-05-06 11:40:20.838183	0.0751369999999999955	t	600
267	2	linkcheck	2015-05-06 11:40:21.092223	0.328347	t	300
268	3	1minstats	2015-05-06 11:40:21.178856	0.409685000000000021	t	60
279	3	5minstats	2015-05-06 11:41:22.001032	1.38586000000000009	t	300
290	3	dns	2015-05-06 11:46:20.62883	0.0683050000000000046	t	600
153	2	dns	2015-05-06 11:20:20.655743	0.0847689999999999971	t	600
155	2	linkcheck	2015-05-06 11:20:20.919281	0.346331999999999973	t	300
156	2	5minstats	2015-05-06 11:20:21.218818	0.643900000000000028	t	300
292	3	1minstats	2015-05-06 11:46:21.185761	0.414308999999999983	t	60
296	2	1minstats	2015-05-06 11:47:20.860078	0.0845869999999999955	t	60
305	2	linkcheck	2015-05-06 11:50:21.067181	0.30187799999999998	t	300
311	3	5minstats	2015-05-06 11:51:21.962847	1.284972	t	300
313	3	1minstats	2015-05-06 11:52:21.059176	0.286138999999999977	t	60
315	3	1minstats	2015-05-06 11:53:21.053007	0.279038999999999981	t	60
165	2	1minstats	2015-05-06 11:23:20.747845	0.0847220000000000056	t	60
324	3	ip2mac	2015-05-06 11:56:20.78546	0.241373000000000004	t	1800
167	3	snmpcheck	2015-05-06 11:24:20.670247	0.0792650000000000021	t	1800
168	3	topo	2015-05-06 11:24:20.728242	0.000255999999999999988	\N	900
169	3	dns	2015-05-06 11:24:20.733005	0.140314999999999995	t	600
170	3	1minstats	2015-05-06 11:24:20.791306	0.120090000000000002	t	60
171	2	1minstats	2015-05-06 11:24:20.876035	0.148147000000000001	t	60
172	3	ip2mac	2015-05-06 11:24:21.566622	1.03326800000000008	t	1800
173	3	linkcheck	2015-05-06 11:24:21.809827	1.21316599999999997	t	300
174	3	5minstats	2015-05-06 11:24:22.135717	1.53752399999999989	t	300
175	3	inventory	2015-05-06 11:24:25.427605	4.83042299999999969	t	21600
327	3	linkcheck	2015-05-06 11:56:21.486382	0.79734499999999997	t	300
329	2	1minstats	2015-05-06 11:57:20.881209	0.0877639999999999948	t	60
331	2	1minstats	2015-05-06 11:58:20.86672	0.0759019999999999972	t	60
333	2	1minstats	2015-05-06 11:59:20.86423	0.0722629999999999939	t	60
335	2	dns	2015-05-06 12:00:20.832677	0.0691200000000000009	t	600
336	2	1minstats	2015-05-06 12:00:20.932334	0.0955389999999999989	t	60
348	3	1minstats	2015-05-06 12:03:21.242091	0.402119000000000004	t	60
354	3	1minstats	2015-05-06 12:05:21.194224	0.356447000000000014	t	60
357	2	1minstats	2015-05-06 12:06:20.926929	0.0860609999999999986	t	60
359	3	linkcheck	2015-05-06 12:06:21.394682	0.705894000000000021	t	300
373	2	5minstats	2015-05-06 12:10:21.409575	0.640651999999999999	t	300
375	3	1minstats	2015-05-06 12:11:21.273617	0.421217000000000008	t	60
377	3	5minstats	2015-05-06 12:11:21.994513	1.30334299999999992	t	300
379	3	1minstats	2015-05-06 12:12:21.199192	0.345760999999999985	t	60
381	3	1minstats	2015-05-06 12:13:21.144083	0.290005000000000013	t	60
383	3	1minstats	2015-05-06 12:14:21.151622	0.297304999999999986	t	60
385	2	1minstats	2015-05-06 12:15:21.042066	0.183203000000000005	t	60
391	3	linkcheck	2015-05-06 12:16:21.521479	0.829524000000000039	t	300
393	3	topo	2015-05-06 12:16:35.259097	6.14574399999999965	t	900
395	3	1minstats	2015-05-06 12:17:21.156823	0.303931000000000007	t	60
399	2	1minstats	2015-05-06 12:19:20.947594	0.0914910000000000029	t	60
401	2	dns	2015-05-06 12:20:20.848135	0.0825300000000000061	t	600
402	2	1minstats	2015-05-06 12:20:20.964603	0.101467000000000002	t	60
403	2	linkcheck	2015-05-06 12:20:21.076935	0.305912000000000017	t	300
409	3	5minstats	2015-05-06 12:21:21.996868	1.30308099999999993	t	300
411	3	1minstats	2015-05-06 12:22:21.142089	0.285362999999999978	t	60
413	3	1minstats	2015-05-06 12:23:21.157903	0.300775999999999988	t	60
414	2	1minstats	2015-05-06 12:24:20.951714	0.0860149999999999942	t	60
416	2	linkcheck	2015-05-06 12:25:20.961764	0.193624999999999992	t	300
419	3	1minstats	2015-05-06 12:25:21.351868	0.493736000000000008	t	60
420	3	snmpcheck	2015-05-06 12:26:20.601469	0.0530009999999999995	t	1800
425	3	linkcheck	2015-05-06 12:26:21.465767	0.765685999999999978	t	300
426	3	5minstats	2015-05-06 12:26:22.091901	1.39102799999999993	t	300
430	3	1minstats	2015-05-06 12:28:21.370892	0.512492999999999976	t	60
432	3	1minstats	2015-05-06 12:29:21.147614	0.288540000000000019	t	60
435	2	linkcheck	2015-05-06 12:30:21.068444	0.298742000000000008	t	300
438	2	1minstats	2015-05-06 12:31:20.952317	0.0854950000000000015	t	60
448	2	1minstats	2015-05-06 12:34:20.953607	0.0851510000000000045	t	60
452	3	1minstats	2015-05-06 12:35:21.200313	0.340355000000000019	t	60
453	2	5minstats	2015-05-06 12:35:21.365375	0.594953999999999983	t	300
457	3	linkcheck	2015-05-06 12:36:21.431683	0.732407999999999948	t	300
461	2	1minstats	2015-05-06 12:38:20.966017	0.0983720000000000011	t	60
462	3	1minstats	2015-05-06 12:38:21.16668	0.306493999999999989	t	60
463	2	1minstats	2015-05-06 12:39:20.956677	0.0878970000000000029	t	60
464	3	1minstats	2015-05-06 12:39:21.193961	0.332008999999999999	t	60
466	2	snmpcheck	2015-05-06 12:40:20.61886	0.0538620000000000002	t	1800
469	2	linkcheck	2015-05-06 12:40:21.079294	0.30910399999999999	t	300
549	2	1minstats	2015-05-06 13:05:21.10656	0.228477999999999987	t	60
552	3	dns	2015-05-06 13:06:20.734271	0.0964249999999999968	t	600
554	3	1minstats	2015-05-06 13:06:21.338827	0.462303999999999993	t	60
550	3	1minstats	2015-05-06 13:05:21.34023	0.466886999999999996	t	60
556	3	5minstats	2015-05-06 13:06:22.112763	1.34825200000000001	t	300
551	2	5minstats	2015-05-06 13:05:21.434145	0.661753999999999953	t	300
555	3	linkcheck	2015-05-06 13:06:21.475113	0.739124000000000003	t	300
553	2	1minstats	2015-05-06 13:06:20.975216	0.0981250000000000039	t	60
557	2	1minstats	2015-05-06 13:07:20.978021	0.0983809999999999962	t	60
558	3	1minstats	2015-05-06 13:07:21.188067	0.310037000000000007	t	60
559	2	1minstats	2015-05-06 13:08:20.960197	0.0831530000000000047	t	60
560	3	1minstats	2015-05-06 13:08:21.152004	0.277666000000000024	t	60
561	2	1minstats	2015-05-06 13:09:20.956427	0.0785369999999999957	t	60
562	3	1minstats	2015-05-06 13:09:21.154547	0.27917900000000001	t	60
563	2	ip2mac	2015-05-06 13:10:20.564756	0.000207999999999999987	\N	1800
564	2	snmpcheck	2015-05-06 13:10:20.62336	0.0571359999999999993	t	1800
565	2	dns	2015-05-06 13:10:20.84074	0.0734390000000000043	t	600
566	2	1minstats	2015-05-06 13:10:20.98418	0.105654999999999999	t	60
567	2	linkcheck	2015-05-06 13:10:21.099351	0.328438999999999981	t	300
568	3	1minstats	2015-05-06 13:10:21.201807	0.325853000000000004	t	60
569	2	5minstats	2015-05-06 13:10:21.418399	0.645622999999999947	t	300
570	2	1minstats	2015-05-06 13:11:20.967693	0.0823709999999999998	t	60
571	3	1minstats	2015-05-06 13:11:21.30413	0.427256999999999998	t	60
572	3	linkcheck	2015-05-06 13:11:21.411573	0.676486999999999949	t	300
573	3	5minstats	2015-05-06 13:11:22.054236	1.28916300000000006	t	300
574	2	1minstats	2015-05-06 13:12:20.977523	0.0953169999999999989	t	60
575	3	1minstats	2015-05-06 13:12:21.187899	0.310601000000000016	t	60
576	2	1minstats	2015-05-06 13:13:20.979	0.0942889999999999978	t	60
577	3	1minstats	2015-05-06 13:13:21.18268	0.304211999999999982	t	60
578	2	1minstats	2015-05-06 13:14:20.980451	0.0972240000000000049	t	60
579	3	1minstats	2015-05-06 13:14:21.197605	0.320435000000000025	t	60
580	2	linkcheck	2015-05-06 13:15:20.999295	0.227944000000000008	t	300
581	2	1minstats	2015-05-06 13:15:21.108862	0.173128000000000004	t	60
582	3	1minstats	2015-05-06 13:15:21.328677	0.432950999999999975	t	60
583	2	5minstats	2015-05-06 13:15:21.442379	0.669799000000000033	t	300
584	3	dns	2015-05-06 13:16:20.733019	0.0956459999999999949	t	600
585	2	1minstats	2015-05-06 13:16:20.988634	0.0972240000000000049	t	60
586	3	1minstats	2015-05-06 13:16:21.320802	0.433010000000000006	t	60
587	3	linkcheck	2015-05-06 13:16:21.423358	0.687995000000000023	t	300
588	3	5minstats	2015-05-06 13:16:22.071989	1.30676400000000004	t	300
589	3	topo	2015-05-06 13:16:35.035192	5.89909999999999979	t	900
590	2	1minstats	2015-05-06 13:17:20.989978	0.0967269999999999935	t	60
591	3	1minstats	2015-05-06 13:17:21.211897	0.324467999999999979	t	60
592	2	1minstats	2015-05-06 13:18:20.996402	0.103600999999999999	t	60
593	3	1minstats	2015-05-06 13:18:21.219296	0.33168700000000001	t	60
594	2	topo	2015-05-06 13:18:35.821871	1.03993200000000008	t	900
595	2	1minstats	2015-05-06 13:19:21.000926	0.106670000000000001	t	60
596	3	1minstats	2015-05-06 13:19:21.227145	0.33828999999999998	t	60
597	2	dns	2015-05-06 13:20:20.907118	0.139988000000000001	t	600
598	2	linkcheck	2015-05-06 13:20:21.050956	0.279631000000000018	t	300
599	2	1minstats	2015-05-06 13:20:21.11815	0.203768000000000005	t	60
600	3	1minstats	2015-05-06 13:20:21.28707	0.375873000000000013	t	60
601	2	5minstats	2015-05-06 13:20:21.480511	0.707694000000000045	t	300
602	2	1minstats	2015-05-06 13:21:21.023662	0.105951000000000004	t	60
603	3	linkcheck	2015-05-06 13:21:21.478472	0.741531000000000051	t	300
604	3	1minstats	2015-05-06 13:21:21.479856	0.562769999999999992	t	60
605	3	5minstats	2015-05-06 13:21:22.145368	1.37943199999999999	t	300
606	2	1minstats	2015-05-06 13:22:21.011754	0.0977330000000000004	t	60
607	3	1minstats	2015-05-06 13:22:21.22424	0.312883000000000022	t	60
608	2	1minstats	2015-05-06 13:23:20.998856	0.0830199999999999966	t	60
609	3	1minstats	2015-05-06 13:23:21.202859	0.290424999999999989	t	60
610	2	1minstats	2015-05-06 13:24:21.000231	0.0832409999999999956	t	60
611	3	1minstats	2015-05-06 13:24:21.195659	0.282806999999999975	t	60
612	2	linkcheck	2015-05-06 13:25:20.983413	0.210986000000000007	t	300
613	2	1minstats	2015-05-06 13:25:21.077525	0.090594999999999995	t	60
614	3	1minstats	2015-05-06 13:25:21.275541	0.291710999999999998	t	60
615	2	5minstats	2015-05-06 13:25:21.378375	0.604905000000000026	t	300
616	3	snmpcheck	2015-05-06 13:26:20.605501	0.0571860000000000007	t	1800
617	3	ip2mac	2015-05-06 13:26:20.703022	0.157678000000000013	t	1800
618	3	dns	2015-05-06 13:26:20.757827	0.115420999999999996	t	600
619	2	1minstats	2015-05-06 13:26:21.077004	0.0885319999999999996	t	60
620	3	1minstats	2015-05-06 13:26:21.367393	0.437587999999999977	t	60
621	3	linkcheck	2015-05-06 13:26:21.426421	0.667381000000000002	t	300
622	3	5minstats	2015-05-06 13:26:22.066649	1.30059499999999995	t	300
623	2	1minstats	2015-05-06 13:27:21.077246	0.0888000000000000039	t	60
624	3	1minstats	2015-05-06 13:27:21.221618	0.29160999999999998	t	60
625	2	1minstats	2015-05-06 13:28:21.072496	0.0833979999999999999	t	60
626	3	1minstats	2015-05-06 13:28:21.219691	0.290964999999999974	t	60
627	2	1minstats	2015-05-06 13:29:21.074101	0.0857549999999999979	t	60
628	3	1minstats	2015-05-06 13:29:21.214351	0.283911999999999998	t	60
629	2	dns	2015-05-06 13:30:20.849625	0.0813719999999999999	t	600
630	2	linkcheck	2015-05-06 13:30:21.032518	0.26017499999999999	t	300
631	2	1minstats	2015-05-06 13:30:21.132139	0.0950130000000000002	t	60
632	3	1minstats	2015-05-06 13:30:21.277542	0.346003999999999978	t	60
633	2	5minstats	2015-05-06 13:30:21.431158	0.657255999999999951	t	300
634	2	1minstats	2015-05-06 13:31:21.123771	0.0875039999999999984	t	60
635	3	1minstats	2015-05-06 13:31:21.348569	0.417356000000000005	t	60
636	3	linkcheck	2015-05-06 13:31:21.40539	0.647104000000000013	t	300
637	3	5minstats	2015-05-06 13:31:22.100765	1.33466899999999988	t	300
638	3	topo	2015-05-06 13:31:34.996271	5.85376799999999964	t	900
639	2	1minstats	2015-05-06 13:32:21.148278	0.0975300000000000056	t	60
640	3	1minstats	2015-05-06 13:32:21.217447	0.287185999999999997	t	60
641	2	1minstats	2015-05-06 13:33:21.121418	0.0845110000000000028	t	60
642	3	1minstats	2015-05-06 13:33:21.204965	0.273104000000000013	t	60
643	2	topo	2015-05-06 13:33:35.77895	0.985572000000000004	t	900
644	2	1minstats	2015-05-06 13:34:21.121468	0.0845469999999999972	t	60
645	3	1minstats	2015-05-06 13:34:21.202611	0.27040900000000001	t	60
646	2	linkcheck	2015-05-06 13:35:20.971691	0.19897999999999999	t	300
647	2	1minstats	2015-05-06 13:35:21.127944	0.0887809999999999988	t	60
648	2	5minstats	2015-05-06 13:35:21.326619	0.552000999999999964	t	300
649	3	1minstats	2015-05-06 13:35:21.394019	0.418933	t	60
650	3	dns	2015-05-06 13:36:20.724688	0.0830589999999999939	t	600
651	2	1minstats	2015-05-06 13:36:21.118041	0.0787370000000000014	t	60
652	3	linkcheck	2015-05-06 13:36:21.211797	0.453259999999999996	t	300
653	3	1minstats	2015-05-06 13:36:21.482214	0.501538000000000039	t	60
654	3	5minstats	2015-05-06 13:36:22.122773	1.35670599999999997	t	300
655	2	1minstats	2015-05-06 13:37:21.122959	0.0838210000000000066	t	60
656	3	1minstats	2015-05-06 13:37:21.265856	0.289629000000000025	t	60
657	2	1minstats	2015-05-06 13:38:21.125063	0.0848840000000000011	t	60
658	3	1minstats	2015-05-06 13:38:21.274256	0.298817999999999973	t	60
659	2	1minstats	2015-05-06 13:39:21.124978	0.0848949999999999982	t	60
660	3	1minstats	2015-05-06 13:39:21.49272	0.515629000000000004	t	60
661	2	ip2mac	2015-05-06 13:40:20.56507	0.000207999999999999987	\N	1800
662	2	snmpcheck	2015-05-06 13:40:20.622467	0.0558359999999999967	t	1800
663	2	dns	2015-05-06 13:40:20.849654	0.0809939999999999966	t	600
664	2	linkcheck	2015-05-06 13:40:21.018953	0.246339000000000002	t	300
665	2	1minstats	2015-05-06 13:40:21.131268	0.0915220000000000061	t	60
668	3	linkcheck	2015-05-06 13:41:21.146627	0.386952999999999991	t	300
676	2	1minstats	2015-05-06 13:44:21.161383	0.120008000000000004	t	60
666	3	1minstats	2015-05-06 13:40:21.27992	0.257815000000000016	t	60
673	3	1minstats	2015-05-06 13:42:21.274092	0.251672000000000007	t	60
667	2	5minstats	2015-05-06 13:40:21.415777	0.641113999999999962	t	300
670	3	1minstats	2015-05-06 13:41:21.42189	0.397351999999999983	t	60
674	2	1minstats	2015-05-06 13:43:21.136559	0.0949369999999999936	t	60
669	2	1minstats	2015-05-06 13:41:21.21645	0.175523000000000012	t	60
677	3	1minstats	2015-05-06 13:44:21.304138	0.280293999999999988	t	60
671	3	5minstats	2015-05-06 13:41:21.951364	1.18458400000000008	t	300
672	2	1minstats	2015-05-06 13:42:21.123268	0.0824140000000000011	t	60
675	3	1minstats	2015-05-06 13:43:21.279163	0.255108999999999975	t	60
\.


--
-- Name: ipdevpoll_job_log_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('ipdevpoll_job_log_id_seq', 677, true);


--
-- Data for Name: location; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY location (locationid, descr, data) FROM stdin;
mylocation	Example location	
Iceland	The land of ice and fire	"Currency"=>"ISK"
\.


--
-- Data for Name: macwatch; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY macwatch (id, mac, userid, description, created, prefix_length) FROM stdin;
\.


--
-- Name: macwatch_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('macwatch_id_seq', 1, false);


--
-- Data for Name: macwatch_match; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY macwatch_match (id, macwatch, cam, posted) FROM stdin;
\.


--
-- Name: macwatch_match_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('macwatch_match_id_seq', 1, false);


--
-- Data for Name: maint_component; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY maint_component (id, maint_taskid, key, value) FROM stdin;
\.


--
-- Name: maint_component_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('maint_component_id_seq', 1, false);


--
-- Data for Name: maint_task; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY maint_task (maint_taskid, maint_start, maint_end, description, author, state) FROM stdin;
\.


--
-- Name: maint_task_maint_taskid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('maint_task_maint_taskid_seq', 1, false);


--
-- Data for Name: mem; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY mem (memid, netboxid, memtype, device, size, used) FROM stdin;
\.


--
-- Name: mem_memid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('mem_memid_seq', 1, false);


--
-- Data for Name: message; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY message (messageid, title, description, tech_description, publish_start, publish_end, author, last_changed, replaces_message, replaced_by) FROM stdin;
\.


--
-- Name: message_messageid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('message_messageid_seq', 1, false);


--
-- Data for Name: message_to_maint_task; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY message_to_maint_task (id, messageid, maint_taskid) FROM stdin;
\.


--
-- Name: message_to_maint_task_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('message_to_maint_task_id_seq', 1, false);


--
-- Data for Name: module; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY module (moduleid, deviceid, netboxid, module, name, model, descr, up, downsince) FROM stdin;
28	36	2	\N	Linecard(slot 3)	WS-X4648-RJ45V+E	10/100/1000BaseT (RJ45)+V E Series with 48 10/100/1000 baseT Premium PoE ports (Cisco/IEEE)	y	\N
29	34	2	\N	Linecard(slot 2)	WS-X4648-RJ45V+E	10/100/1000BaseT (RJ45)+V E Series with 48 10/100/1000 baseT Premium PoE ports (Cisco/IEEE)	y	\N
30	33	2	\N	Linecard(slot 1)	WS-X45-SUP6L-E	Supervisor 6L-E 10GE (X2), 1000BaseX (SFP) with 2 10GE X2 ports	y	\N
31	35	2	\N	Linecard(slot 4)	WS-X4606-X2-E	10GE (X2), 1000BaseX (SFP) with 6 10GE X2 ports	y	\N
32	42	3	\N	Transceiver Gi1/31		SFP Transceiver 1000BaseLH Gi1/31	y	\N
33	43	3	\N	Transceiver Gi1/32		SFP Transceiver 1000BaseLH Gi1/32	y	\N
34	41	3	1	1	ME-C6524GT-8S	ME-C6524GT-8S 32 ports Cisco ME 6524 Ethernet Switch Rev. 1.6	y	\N
35	44	3	\N	ME-C6524-PFC3C Policy Feature Card 3C sub-module of 1	ME-C6524-PFC3C	ME-C6524-PFC3C Policy Feature Card 3C Rev. 1.4	y	\N
36	45	3	\N	msfc sub-module of 1	ME-C6524-MSFC2A	ME-C6524-MSFC2A MSFC2A C6524 submodule Rev. 1.2	y	\N
37	46	3	\N	Transceiver Gi1/30		SFP Transceiver 1000BaseLH Gi1/30	y	\N
38	47	3	\N	Transceiver Gi1/29		SFP Transceiver 1000BaseLH Gi1/29	y	\N
\.


--
-- Name: module_moduleid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('module_moduleid_seq', 65, true);


--
-- Data for Name: netbios; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netbios (netbiosid, ip, mac, name, server, username, start_time, end_time) FROM stdin;
\.


--
-- Name: netbios_netbiosid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netbios_netbiosid_seq', 1, false);


--
-- Data for Name: netbox; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netbox (netboxid, ip, roomid, typeid, deviceid, sysname, catid, orgid, ro, rw, up, snmp_version, upsince, uptodate, discovered, data) FROM stdin;
2	158.38.0.2	Dimmuborgir	81	32	test-sw.testorg.com	SW	Snakeswitch	public		y	2	2015-05-06 10:36:55.359596	f	2015-05-06 10:36:55.359638	
3	158.38.0.1	Dimmuborgir	82	41	test-gsw.testorg.com	GSW	Snakeswitch	public		y	2	2015-05-06 11:22:31.147993	f	2015-05-06 11:22:31.148034	
\.


--
-- Name: netbox_netboxid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netbox_netboxid_seq', 5, true);


--
-- Data for Name: netbox_vtpvlan; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netbox_vtpvlan (id, netboxid, vtpvlan) FROM stdin;
\.


--
-- Name: netbox_vtpvlan_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netbox_vtpvlan_id_seq', 1, false);


--
-- Data for Name: netboxcategory; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netboxcategory (id, netboxid, category) FROM stdin;
\.


--
-- Name: netboxcategory_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netboxcategory_id_seq', 1, false);


--
-- Data for Name: netboxgroup; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netboxgroup (netboxgroupid, descr) FROM stdin;
AD	Description
ADC	Description
BACKUP	Description
DNS	Description
FS	Description
LDAP	Description
MAIL	Description
NOTES	Description
STORE	Description
TEST	Description
UNIX	Description
UNIX-STUD	Description
WEB	Description
WIN	Description
WIN-STUD	Description
\.


--
-- Data for Name: netboxinfo; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netboxinfo (netboxinfoid, netboxid, key, var, val) FROM stdin;
3	2	poll_times	modules	((F1430901620\nL4055704403L\ntp1\nL988915437L\ntp2\n.
4	2	poll_times	uptime	((F1430901620\nL4055704391L\ntp1\ntp2\n.
11	3	poll_times	cdp	((F1430911894\nL3090091048L\ntNtp1\n.
12	3	poll_times	lldp	((F1430911894\nL3090091033L\ntNtp1\n.
5	2	poll_times	cdp	((F1430912015\nL4056743869L\ntL40567423L\ntp1\n.
6	2	poll_times	lldp	((F1430912015\nL4056743852L\ntNtp1\n.
9	3	poll_times	modules	((F1430904380\nL3089339632L\ntp1\nL2502743579L\ntp2\n.
10	3	poll_times	uptime	((F1430904380\nL3089339631L\ntp1\ntp2\n.
\.


--
-- Name: netboxinfo_netboxinfoid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netboxinfo_netboxinfoid_seq', 20, true);


--
-- Data for Name: netboxsnmpoid; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY netboxsnmpoid (id, netboxid, snmpoidid, frequency) FROM stdin;
\.


--
-- Name: netboxsnmpoid_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('netboxsnmpoid_id_seq', 1, false);


--
-- Data for Name: nettype; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY nettype (nettypeid, descr, edit) FROM stdin;
core	core	f
dummy	dummy	f
elink	elink	f
lan	lan	f
link	link	f
loopback	loopbcak	f
reserved	reserved	t
private	private	f
scope	scope	t
static	static	f
unknown	unknow	f
\.


--
-- Data for Name: org; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY org (orgid, parent, descr, contact, data) FROM stdin;
myorg	\N	Example organization unit	nobody	
Snakeswitch	\N			
\.


--
-- Data for Name: patch; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY patch (patchid, interfaceid, cablingid, split) FROM stdin;
\.


--
-- Name: patch_patchid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('patch_patchid_seq', 1, false);


--
-- Data for Name: powersupply_or_fan; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY powersupply_or_fan (powersupplyid, netboxid, deviceid, name, model, descr, physical_class, downsince, sensor_oid, up) FROM stdin;
4	2	37	Fan	WS-X4596-E	FanTray	fan	\N	.1.3.6.1.4.1.9.9.117.1.4.1.1.1.10	y
5	2	39	Power Supply 2	PWR-C45-2800ACV	Power Supply ( AC 2800W )	powerSupply	\N	.1.3.6.1.4.1.9.9.117.1.1.2.1.2.16	y
6	2	38	Power Supply 1	PWR-C45-2800ACV	Power Supply ( AC 2800W )	powerSupply	\N	.1.3.6.1.4.1.9.9.117.1.1.2.1.2.13	y
7	3	50	FAN-C6524 1	FAN-C6524	Fan Tray for 1.5 RU Catalyst Switches 1	fan	\N	\N	u
8	3	48	PS 2 PWR-400W-AC	PWR-400W-AC	400W AC supply for Catalyst 1.5 RU switches 2	powerSupply	\N	.1.3.6.1.4.1.9.9.117.1.1.2.1.2.19	y
9	3	49	PS 1 PWR-400W-AC	PWR-400W-AC	400W AC supply for Catalyst 1.5 RU switches 1	powerSupply	\N	.1.3.6.1.4.1.9.9.117.1.1.2.1.2.8	y
\.


--
-- Name: powersupply_or_fan_powersupplyid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('powersupply_or_fan_powersupplyid_seq', 12, true);


--
-- Data for Name: prefix; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY prefix (prefixid, netaddr, vlanid) FROM stdin;
24	158.38.234.4/30	15
25	128.39.103.25/32	14
26	128.39.70.8/30	13
27	2001:700:1:f03::/64	15
28	2001:700:1:f00::2/128	14
29	2001:700:0:8000::/64	13
2	2001:700:0:4529::/64	7
3	2001:700:0:4528::/64	6
6	2001:700:1:8::/64	8
8	2001:700:1:f01::/64	2
16	158.38.38.0/28	12
17	158.38.179.128/25	7
18	158.38.179.0/25	6
19	158.38.180.0/24	8
22	158.38.1.144/30	2
\.


--
-- Name: prefix_prefixid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('prefix_prefixid_seq', 30, true);


--
-- Data for Name: room; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY room (roomid, locationid, descr, "position", data) FROM stdin;
myroom	mylocation	Example wiring closet	\N	
Dimmuborgir	Iceland	Large area of unusually shaped lava fields	(65.5902779999999979,-16.899443999999999)	"Metal band"=>"No"
\.


--
-- Data for Name: rproto_attr; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY rproto_attr (id, interfaceid, protoname, metric) FROM stdin;
\.


--
-- Name: rproto_attr_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('rproto_attr_id_seq', 1, false);


--
-- Data for Name: rrd_datasource; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY rrd_datasource (rrd_datasourceid, rrd_fileid, name, descr, dstype, units, threshold, max, delimiter, thresholdstate) FROM stdin;
\.


--
-- Name: rrd_datasource_rrd_datasourceid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('rrd_datasource_rrd_datasourceid_seq', 1, false);


--
-- Data for Name: rrd_file; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY rrd_file (rrd_fileid, path, filename, step, subsystem, netboxid, key, value, category) FROM stdin;
\.


--
-- Name: rrd_file_rrd_fileid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('rrd_file_rrd_fileid_seq', 1, false);


--
-- Data for Name: schema_change_log; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY schema_change_log (id, major, minor, point, script_name, date_applied) FROM stdin;
1	3	8	0	initial install	2015-05-06 08:24:12.367833
2	3	8	1	sc.03.08.0001.sql	2015-05-06 08:24:14.361221
3	3	9	1	sc.03.09.0001.sql	2015-05-06 08:24:14.36897
4	3	9	2	sc.03.09.0002.sql	2015-05-06 08:24:14.39416
5	3	9	3	sc.03.09.0003.sql	2015-05-06 08:24:14.397001
6	3	9	4	sc.03.09.0004.sql	2015-05-06 08:24:14.399999
7	3	9	5	sc.03.09.0005.sql	2015-05-06 08:24:14.406604
8	3	9	6	sc.03.09.0006.sql	2015-05-06 08:24:14.411676
9	3	10	1	sc.03.10.0001.sql	2015-05-06 08:24:14.416207
10	3	10	2	sc.03.10.0002.sql	2015-05-06 08:24:14.433992
11	3	10	3	sc.03.10.0003.sql	2015-05-06 08:24:14.464463
12	3	10	4	sc.03.10.0004.sql	2015-05-06 08:24:14.468196
13	3	10	5	sc.03.10.0005.sql	2015-05-06 08:24:14.471068
14	3	10	6	sc.03.10.0006.sql	2015-05-06 08:24:14.483045
15	3	10	7	sc.03.10.0007.sql	2015-05-06 08:24:14.493895
16	3	11	1	sc.03.11.0001.sql	2015-05-06 08:24:14.498033
17	3	11	2	sc.03.11.0002.sql	2015-05-06 08:24:14.508044
18	3	11	3	sc.03.11.0003.sql	2015-05-06 08:24:14.528716
19	3	11	4	sc.03.11.0004.sql	2015-05-06 08:24:14.559958
20	3	11	5	sc.03.11.0005.sql	2015-05-06 08:24:14.605345
21	3	11	6	sc.03.11.0006.sql	2015-05-06 08:24:14.615289
22	3	11	7	sc.03.11.0007.sql	2015-05-06 08:24:14.617623
23	3	11	8	sc.03.11.0008.sql	2015-05-06 08:24:14.632317
24	3	11	9	sc.03.11.0009.sql	2015-05-06 08:24:14.635028
25	3	11	10	sc.03.11.0010.sql	2015-05-06 08:24:14.63721
26	3	11	11	sc.03.11.0011.sql	2015-05-06 08:24:14.644385
27	3	11	12	sc.03.11.0012.sql	2015-05-06 08:24:14.650938
28	3	11	13	sc.03.11.0013.sql	2015-05-06 08:24:14.654209
29	3	12	1	sc.03.12.0001.sql	2015-05-06 08:24:14.658048
30	3	12	2	sc.03.12.0002.sql	2015-05-06 08:24:14.714016
31	3	12	3	sc.03.12.0003.sql	2015-05-06 08:24:14.733325
32	3	12	4	sc.03.12.0004.sql	2015-05-06 08:24:14.771547
33	3	12	5	sc.03.12.0005.sql	2015-05-06 08:24:14.775122
34	3	12	25	sc.03.12.0025.sql	2015-05-06 08:24:14.796278
35	3	12	26	sc.03.12.0026.sql	2015-05-06 08:24:14.799461
36	3	12	27	sc.03.12.0027.sql	2015-05-06 08:24:14.823958
37	3	12	28	sc.03.12.0028.sql	2015-05-06 08:24:14.828473
38	3	12	50	sc.03.12.0050.sql	2015-05-06 08:24:14.832171
39	3	12	51	sc.03.12.0051.sql	2015-05-06 08:24:14.834939
40	3	12	52	sc.03.12.0052.sql	2015-05-06 08:24:14.83662
41	3	12	53	sc.03.12.0053.sql	2015-05-06 08:24:14.842414
42	3	12	54	sc.03.12.0054.sql	2015-05-06 08:24:14.844306
43	3	12	100	sc.03.12.0100.sql	2015-05-06 08:24:14.846468
44	3	12	101	sc.03.12.0101.sql	2015-05-06 08:24:14.848385
45	3	12	102	sc.03.12.0102.sql	2015-05-06 08:24:14.852472
46	3	12	103	sc.03.12.0103.sql	2015-05-06 08:24:14.855563
47	3	12	104	sc.03.12.0104.sql	2015-05-06 08:24:14.857115
48	3	12	105	sc.03.12.0105.sql	2015-05-06 08:24:14.861412
49	3	12	106	sc.03.12.0106.sql	2015-05-06 08:24:14.863342
50	3	12	107	sc.03.12.0107.sql	2015-05-06 08:24:14.895221
51	3	12	110	sc.03.12.0110.sql	2015-05-06 08:24:14.89933
52	3	12	111	sc.03.12.0111.sql	2015-05-06 08:24:14.902911
53	3	13	1	sc.03.13.0001.sql	2015-05-06 08:24:14.915691
54	3	13	2	sc.03.13.0002.sql	2015-05-06 08:24:14.947057
55	3	13	10	sc.03.13.0010.sql	2015-05-06 08:24:14.950377
56	3	13	11	sc.03.13.0011.sql	2015-05-06 08:24:14.961858
57	3	13	12	sc.03.13.0012.sql	2015-05-06 08:24:14.970701
58	3	13	13	sc.03.13.0013.sql	2015-05-06 08:24:14.973256
59	3	13	14	sc.03.13.0014.sql	2015-05-06 08:24:14.975633
60	3	13	15	sc.03.13.0015.sql	2015-05-06 08:24:14.97741
61	3	14	1	sc.03.14.0001.sql	2015-05-06 08:24:14.982894
62	3	14	2	sc.03.14.0002.sql	2015-05-06 08:24:14.995249
63	3	14	3	sc.03.14.0003.sql	2015-05-06 08:24:15.034149
64	3	14	4	sc.03.14.0004.sql	2015-05-06 08:24:15.068991
65	3	14	5	sc.03.14.0005.sql	2015-05-06 08:24:15.072583
66	3	14	6	sc.03.14.0006.sql	2015-05-06 08:24:15.076987
67	3	14	7	sc.03.14.0007.sql	2015-05-06 08:24:15.078683
68	3	15	1	sc.03.15.0001.sql	2015-05-06 08:24:15.094862
69	3	15	2	sc.03.15.0002.sql	2015-05-06 08:24:15.111642
70	3	15	3	sc.03.15.0003.sql	2015-05-06 08:24:15.141741
71	3	15	4	sc.03.15.0004.sql	2015-05-06 08:24:15.179256
72	3	15	50	sc.03.15.0050.sql	2015-05-06 08:24:15.182568
73	3	15	70	sc.03.15.0070.sql	2015-05-06 08:24:15.184505
74	3	15	71	sc.03.15.0071.sql	2015-05-06 08:24:15.197474
75	3	15	72	sc.03.15.0072.sql	2015-05-06 08:24:15.202619
76	3	15	100	sc.03.15.0100.sql	2015-05-06 08:24:15.211892
77	3	15	101	sc.03.15.0101.sql	2015-05-06 08:24:15.241126
78	3	15	102	sc.03.15.0102.sql	2015-05-06 08:24:15.246719
79	3	15	103	sc.03.15.0103.sql	2015-05-06 08:24:15.251161
80	3	15	104	sc.03.15.0104.sql	2015-05-06 08:24:15.255018
81	3	15	105	sc.03.15.0105.sql	2015-05-06 08:24:15.267163
82	3	15	200	sc.03.15.0200.sql	2015-05-06 08:24:15.278187
83	3	15	201	sc.03.15.0201.sql	2015-05-06 08:24:15.281596
84	4	0	1	sc.04.00.0001.sql	2015-05-06 08:24:15.28545
85	4	0	2	sc.04.00.0002.sql	2015-05-06 08:24:15.288587
86	4	0	3	sc.04.00.0003.sql	2015-05-06 08:24:15.303227
87	4	0	4	sc.04.00.0004.sql	2015-05-06 08:24:15.306096
88	4	0	10	sc.04.00.0010.sql	2015-05-06 08:24:15.308212
89	4	0	11	sc.04.00.0011.sql	2015-05-06 08:24:15.310593
90	4	0	12	sc.04.00.0012.sql	2015-05-06 08:24:15.312589
91	4	0	13	sc.04.00.0013.sql	2015-05-06 08:24:15.314918
92	4	0	14	sc.04.00.0014.sql	2015-05-06 08:24:15.321891
93	4	0	15	sc.04.00.0015.sql	2015-05-06 08:24:15.323954
94	4	0	16	sc.04.00.0016.sql	2015-05-06 08:24:15.326109
95	4	0	17	sc.04.00.0017.sql	2015-05-06 08:24:15.331365
96	4	0	18	sc.04.00.0018.sql	2015-05-06 08:24:15.337333
97	4	0	19	sc.04.00.0019.sql	2015-05-06 08:24:15.339842
98	4	0	20	sc.04.00.0020.sql	2015-05-06 08:24:15.343991
99	4	1	1	sc.04.01.0001.sql	2015-05-06 08:24:15.355911
100	4	1	2	sc.04.01.0002.sql	2015-05-06 08:24:15.360697
101	4	1	3	sc.04.01.0003.sql	2015-05-06 08:24:15.365392
102	4	2	1	sc.04.02.0001.sql	2015-05-06 08:24:15.375948
103	4	2	10	sc.04.02.0010.sql	2015-05-06 08:24:15.40469
104	4	2	20	sc.04.02.0020.sql	2015-05-06 08:24:15.426791
105	4	2	50	sc.04.02.0050.sql	2015-05-06 08:24:15.429496
106	4	2	55	sc.04.02.0055.sql	2015-05-06 08:24:15.486022
107	4	2	100	sc.04.02.0100.sql	2015-05-06 08:24:15.489533
108	4	2	101	sc.04.02.0101.sql	2015-05-06 08:24:15.49978
109	4	2	102	sc.04.02.0102.sql	2015-05-06 08:24:15.503451
110	4	2	103	sc.04.02.0103.sql	2015-05-06 08:24:15.507123
111	4	2	104	sc.04.02.0104.sql	2015-05-06 08:24:15.516657
112	4	3	50	sc.04.03.0050.sql	2015-05-06 08:24:15.519906
\.


--
-- Name: schema_change_log_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('schema_change_log_id_seq', 112, true);


--
-- Data for Name: sensor; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY sensor (sensorid, netboxid, oid, unit_of_measurement, "precision", data_scale, human_readable, name, internal_name, mib) FROM stdin;
114	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1040	dBm	1	\N	TenGigabitEthernet1/2 Receive Power Sensor	Te1/2 Receive Power Sensor	Te1/2 Receive Power Sensor	CISCO-ENTITY-SENSOR-MIB
115	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4119	dBm	1	\N	TenGigabitEthernet4/5 Receive Power Sensor	Te4/5 Receive Power Sensor	Te4/5 Receive Power Sensor	CISCO-ENTITY-SENSOR-MIB
116	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4115	dBm	1	\N	TenGigabitEthernet4/1 Receive Power Sensor	Te4/1 Receive Power Sensor	Te4/1 Receive Power Sensor	CISCO-ENTITY-SENSOR-MIB
117	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4097	dBm	1	\N	TenGigabitEthernet4/1 Transmit Power Sensor	Te4/1 Transmit Power Sensor	Te4/1 Transmit Power Sensor	CISCO-ENTITY-SENSOR-MIB
118	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4102	dBm	1	\N	TenGigabitEthernet4/6 Transmit Power Sensor	Te4/6 Transmit Power Sensor	Te4/6 Transmit Power Sensor	CISCO-ENTITY-SENSOR-MIB
119	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1027	amperes	1	milli	TenGigabitEthernet1/1 Bias Current Sensor	Te1/1 Bias Current Sensor	Te1/1 Bias Current Sensor	CISCO-ENTITY-SENSOR-MIB
120	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1033	dBm	1	\N	TenGigabitEthernet1/1 Transmit Power Sensor	Te1/1 Transmit Power Sensor	Te1/1 Transmit Power Sensor	CISCO-ENTITY-SENSOR-MIB
121	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1022	voltsDC	2	\N	TenGigabitEthernet1/2 Supply Voltage Sensor	Te1/2 Supply Voltage Sensor	Te1/2 Supply Voltage Sensor	CISCO-ENTITY-SENSOR-MIB
122	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4079	amperes	1	milli	TenGigabitEthernet4/1 Bias Current Sensor	Te4/1 Bias Current Sensor	Te4/1 Bias Current Sensor	CISCO-ENTITY-SENSOR-MIB
123	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1028	amperes	1	milli	TenGigabitEthernet1/2 Bias Current Sensor	Te1/2 Bias Current Sensor	Te1/2 Bias Current Sensor	CISCO-ENTITY-SENSOR-MIB
124	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1021	voltsDC	2	\N	TenGigabitEthernet1/1 Supply Voltage Sensor	Te1/1 Supply Voltage Sensor	Te1/1 Supply Voltage Sensor	CISCO-ENTITY-SENSOR-MIB
125	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1016	celsius	1	\N	TenGigabitEthernet1/2 Module Temperature Sensor	Te1/2 Module Temperature Sensor	Te1/2 Module Temperature Sensor	CISCO-ENTITY-SENSOR-MIB
126	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4120	dBm	1	\N	TenGigabitEthernet4/6 Receive Power Sensor	Te4/6 Receive Power Sensor	Te4/6 Receive Power Sensor	CISCO-ENTITY-SENSOR-MIB
127	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1015	celsius	1	\N	TenGigabitEthernet1/1 Module Temperature Sensor	Te1/1 Module Temperature Sensor	Te1/1 Module Temperature Sensor	CISCO-ENTITY-SENSOR-MIB
128	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4083	amperes	1	milli	TenGigabitEthernet4/5 Bias Current Sensor	Te4/5 Bias Current Sensor	Te4/5 Bias Current Sensor	CISCO-ENTITY-SENSOR-MIB
129	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4084	amperes	1	milli	TenGigabitEthernet4/6 Bias Current Sensor	Te4/6 Bias Current Sensor	Te4/6 Bias Current Sensor	CISCO-ENTITY-SENSOR-MIB
130	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1039	dBm	1	\N	TenGigabitEthernet1/1 Receive Power Sensor	Te1/1 Receive Power Sensor	Te1/1 Receive Power Sensor	CISCO-ENTITY-SENSOR-MIB
131	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4048	celsius	1	\N	TenGigabitEthernet4/6 Module Temperature Sensor	Te4/6 Module Temperature Sensor	Te4/6 Module Temperature Sensor	CISCO-ENTITY-SENSOR-MIB
132	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.17	boolean	0	\N	Power Supply Fan Sensor	Power Supply 2 Fan	Power Supply 2 Fan	CISCO-ENTITY-SENSOR-MIB
133	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4047	celsius	1	\N	TenGigabitEthernet4/5 Module Temperature Sensor	Te4/5 Module Temperature Sensor	Te4/5 Module Temperature Sensor	CISCO-ENTITY-SENSOR-MIB
134	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4101	dBm	1	\N	TenGigabitEthernet4/5 Transmit Power Sensor	Te4/5 Transmit Power Sensor	Te4/5 Transmit Power Sensor	CISCO-ENTITY-SENSOR-MIB
135	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.14	boolean	0	\N	Power Supply Fan Sensor	Power Supply 1 Fan	Power Supply 1 Fan	CISCO-ENTITY-SENSOR-MIB
136	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.1034	dBm	1	\N	TenGigabitEthernet1/2 Transmit Power Sensor	Te1/2 Transmit Power Sensor	Te1/2 Transmit Power Sensor	CISCO-ENTITY-SENSOR-MIB
137	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4043	celsius	1	\N	TenGigabitEthernet4/1 Module Temperature Sensor	Te4/1 Module Temperature Sensor	Te4/1 Module Temperature Sensor	CISCO-ENTITY-SENSOR-MIB
138	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4061	voltsDC	2	\N	TenGigabitEthernet4/1 Supply Voltage Sensor	Te4/1 Supply Voltage Sensor	Te4/1 Supply Voltage Sensor	CISCO-ENTITY-SENSOR-MIB
139	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4065	voltsDC	2	\N	TenGigabitEthernet4/5 Supply Voltage Sensor	Te4/5 Supply Voltage Sensor	Te4/5 Supply Voltage Sensor	CISCO-ENTITY-SENSOR-MIB
140	2	.1.3.6.1.4.1.9.9.91.1.1.1.1.4.4066	voltsDC	2	\N	TenGigabitEthernet4/6 Supply Voltage Sensor	Te4/6 Supply Voltage Sensor	Te4/6 Supply Voltage Sensor	CISCO-ENTITY-SENSOR-MIB
141	3	.1.3.6.1.2.1.99.1.1.1.4.1014	celsius	0	\N	module 1 RP inlet temperature Sensor	module 1 RP inlet temperature Sensor	module 1 RP inlet temperature Sensor	ENTITY-SENSOR-MIB
142	3	.1.3.6.1.2.1.99.1.1.1.4.13	voltsAC	0	\N	power-supply 1 power-input Sensor	power-supply 1 power-input Sensor	power-supply 1 power-input Sensor	ENTITY-SENSOR-MIB
143	3	.1.3.6.1.2.1.99.1.1.1.4.10	boolean	0	\N	power-supply 1 power-output-fail Sensor	power-supply 1 power-output-fail Sensor	power-supply 1 power-output-fail Sensor	ENTITY-SENSOR-MIB
144	3	.1.3.6.1.2.1.99.1.1.1.4.1116	other	1	\N	GigabitEthernet1/30 Transmit Power Sensor	Gi1/30 Transmit Power Sensor	Gi1/30 Transmit Power Sensor	ENTITY-SENSOR-MIB
145	3	.1.3.6.1.2.1.99.1.1.1.4.1101	voltsDC	1	\N	GigabitEthernet1/29 Supply Voltage Sensor	Gi1/29 Supply Voltage Sensor	Gi1/29 Supply Voltage Sensor	ENTITY-SENSOR-MIB
146	3	.1.3.6.1.2.1.99.1.1.1.4.1009	celsius	0	\N	module 1 asic-3 temperature Sensor	module 1 asic-3 temperature Sensor	module 1 asic-3 temperature Sensor	ENTITY-SENSOR-MIB
147	3	.1.3.6.1.2.1.99.1.1.1.4.1103	other	1	\N	GigabitEthernet1/29 Transmit Power Sensor	Gi1/29 Transmit Power Sensor	Gi1/29 Transmit Power Sensor	ENTITY-SENSOR-MIB
148	3	.1.3.6.1.2.1.99.1.1.1.4.1102	amperes	1	milli	GigabitEthernet1/29 Bias Current Sensor	Gi1/29 Bias Current Sensor	Gi1/29 Bias Current Sensor	ENTITY-SENSOR-MIB
149	3	.1.3.6.1.2.1.99.1.1.1.4.1127	voltsDC	1	\N	GigabitEthernet1/31 Supply Voltage Sensor	Gi1/31 Supply Voltage Sensor	Gi1/31 Supply Voltage Sensor	ENTITY-SENSOR-MIB
150	3	.1.3.6.1.2.1.99.1.1.1.4.1126	celsius	1	\N	GigabitEthernet1/31 Module Temperature Sensor	Gi1/31 Module Temperature Sensor	Gi1/31 Module Temperature Sensor	ENTITY-SENSOR-MIB
151	3	.1.3.6.1.2.1.99.1.1.1.4.1006	celsius	0	\N	module 1 inlet temperature Sensor	module 1 inlet temperature Sensor	module 1 inlet temperature Sensor	ENTITY-SENSOR-MIB
152	3	.1.3.6.1.2.1.99.1.1.1.4.1007	celsius	0	\N	module 1 asic-1 temperature Sensor	module 1 asic-1 temperature Sensor	module 1 asic-1 temperature Sensor	ENTITY-SENSOR-MIB
153	3	.1.3.6.1.2.1.99.1.1.1.4.1002	boolean	0	\N	module 1 power-output-fail Sensor	module 1 power-output-fail Sensor	module 1 power-output-fail Sensor	ENTITY-SENSOR-MIB
154	3	.1.3.6.1.2.1.99.1.1.1.4.1141	amperes	1	milli	GigabitEthernet1/32 Bias Current Sensor	Gi1/32 Bias Current Sensor	Gi1/32 Bias Current Sensor	ENTITY-SENSOR-MIB
155	3	.1.3.6.1.2.1.99.1.1.1.4.1140	voltsDC	1	\N	GigabitEthernet1/32 Supply Voltage Sensor	Gi1/32 Supply Voltage Sensor	Gi1/32 Supply Voltage Sensor	ENTITY-SENSOR-MIB
156	3	.1.3.6.1.2.1.99.1.1.1.4.1143	other	1	\N	GigabitEthernet1/32 Receive Power Sensor	Gi1/32 Receive Power Sensor	Gi1/32 Receive Power Sensor	ENTITY-SENSOR-MIB
157	3	.1.3.6.1.2.1.99.1.1.1.4.1142	other	1	\N	GigabitEthernet1/32 Transmit Power Sensor	Gi1/32 Transmit Power Sensor	Gi1/32 Transmit Power Sensor	ENTITY-SENSOR-MIB
158	3	.1.3.6.1.2.1.99.1.1.1.4.21	boolean	0	\N	power-supply 2 power-output-fail Sensor	power-supply 2 power-output-fail Sensor	power-supply 2 power-output-fail Sensor	ENTITY-SENSOR-MIB
159	3	.1.3.6.1.2.1.99.1.1.1.4.20	boolean	0	\N	power-supply 2 fan-fail Sensor	power-supply 2 fan-fail Sensor	power-supply 2 fan-fail Sensor	ENTITY-SENSOR-MIB
160	3	.1.3.6.1.2.1.99.1.1.1.4.24	voltsAC	0	\N	power-supply 2 power-input Sensor	power-supply 2 power-input Sensor	power-supply 2 power-input Sensor	ENTITY-SENSOR-MIB
161	3	.1.3.6.1.2.1.99.1.1.1.4.29	other	0	\N	Sensor for counting number of OK Fans	Sensor for counting number of OK Fans	Sensor for counting number of OK Fans	ENTITY-SENSOR-MIB
162	3	.1.3.6.1.2.1.99.1.1.1.4.1129	other	1	\N	GigabitEthernet1/31 Transmit Power Sensor	Gi1/31 Transmit Power Sensor	Gi1/31 Transmit Power Sensor	ENTITY-SENSOR-MIB
163	3	.1.3.6.1.2.1.99.1.1.1.4.1008	celsius	0	\N	module 1 asic-2 temperature Sensor	module 1 asic-2 temperature Sensor	module 1 asic-2 temperature Sensor	ENTITY-SENSOR-MIB
164	3	.1.3.6.1.2.1.99.1.1.1.4.1100	celsius	1	\N	GigabitEthernet1/29 Module Temperature Sensor	Gi1/29 Module Temperature Sensor	Gi1/29 Module Temperature Sensor	ENTITY-SENSOR-MIB
165	3	.1.3.6.1.2.1.99.1.1.1.4.1139	celsius	1	\N	GigabitEthernet1/32 Module Temperature Sensor	Gi1/32 Module Temperature Sensor	Gi1/32 Module Temperature Sensor	ENTITY-SENSOR-MIB
166	3	.1.3.6.1.2.1.99.1.1.1.4.1018	celsius	0	\N	module 1 EARL inlet temperature Sensor	module 1 EARL inlet temperature Sensor	module 1 EARL inlet temperature Sensor	ENTITY-SENSOR-MIB
167	3	.1.3.6.1.2.1.99.1.1.1.4.1017	celsius	0	\N	module 1 EARL outlet temperature Sensor	module 1 EARL outlet temperature Sensor	module 1 EARL outlet temperature Sensor	ENTITY-SENSOR-MIB
168	3	.1.3.6.1.2.1.99.1.1.1.4.1113	celsius	1	\N	GigabitEthernet1/30 Module Temperature Sensor	Gi1/30 Module Temperature Sensor	Gi1/30 Module Temperature Sensor	ENTITY-SENSOR-MIB
169	3	.1.3.6.1.2.1.99.1.1.1.4.1128	amperes	1	milli	GigabitEthernet1/31 Bias Current Sensor	Gi1/31 Bias Current Sensor	Gi1/31 Bias Current Sensor	ENTITY-SENSOR-MIB
170	3	.1.3.6.1.2.1.99.1.1.1.4.1013	celsius	0	\N	module 1 RP outlet temperature Sensor	module 1 RP outlet temperature Sensor	module 1 RP outlet temperature Sensor	ENTITY-SENSOR-MIB
171	3	.1.3.6.1.2.1.99.1.1.1.4.1117	other	1	\N	GigabitEthernet1/30 Receive Power Sensor	Gi1/30 Receive Power Sensor	Gi1/30 Receive Power Sensor	ENTITY-SENSOR-MIB
172	3	.1.3.6.1.2.1.99.1.1.1.4.1114	voltsDC	1	\N	GigabitEthernet1/30 Supply Voltage Sensor	Gi1/30 Supply Voltage Sensor	Gi1/30 Supply Voltage Sensor	ENTITY-SENSOR-MIB
173	3	.1.3.6.1.2.1.99.1.1.1.4.1115	amperes	1	milli	GigabitEthernet1/30 Bias Current Sensor	Gi1/30 Bias Current Sensor	Gi1/30 Bias Current Sensor	ENTITY-SENSOR-MIB
174	3	.1.3.6.1.2.1.99.1.1.1.4.1130	other	1	\N	GigabitEthernet1/31 Receive Power Sensor	Gi1/31 Receive Power Sensor	Gi1/31 Receive Power Sensor	ENTITY-SENSOR-MIB
175	3	.1.3.6.1.2.1.99.1.1.1.4.9	boolean	0	\N	power-supply 1 fan-fail Sensor	power-supply 1 fan-fail Sensor	power-supply 1 fan-fail Sensor	ENTITY-SENSOR-MIB
176	3	.1.3.6.1.2.1.99.1.1.1.4.1005	celsius	0	\N	module 1 outlet temperature Sensor	module 1 outlet temperature Sensor	module 1 outlet temperature Sensor	ENTITY-SENSOR-MIB
177	3	.1.3.6.1.2.1.99.1.1.1.4.3	boolean	0	\N	fan-tray 1 fan-fail Sensor	fan-tray 1 fan-fail Sensor	fan-tray 1 fan-fail Sensor	ENTITY-SENSOR-MIB
\.


--
-- Name: sensor_sensorid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('sensor_sensorid_seq', 290, true);


--
-- Data for Name: service; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY service (serviceid, netboxid, active, handler, version, up) FROM stdin;
\.


--
-- Name: service_serviceid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('service_serviceid_seq', 1, false);


--
-- Data for Name: serviceproperty; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY serviceproperty (id, serviceid, property, value) FROM stdin;
\.


--
-- Name: serviceproperty_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('serviceproperty_id_seq', 1, false);


--
-- Data for Name: snmpoid; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY snmpoid (snmpoidid, oidkey, snmpoid, oidsource, getnext, decodehex, match_regex, defaultfreq, uptodate, descr, oidname, mib, unit) FROM stdin;
1	3c9300Mac	1.3.6.1.4.1.43.29.4.10.8.1.5.1	3com	t	f	\N	21600	f	Bridge table for 3Com SuperStack 1900	\N	\N	\N
2	3c9300Serial	1.3.6.1.4.1.43.29.4.18.2.1.7.1	\N	f	f	\N	21600	f	3com9300	\N	\N	\N
3	3cDescr	1.3.6.1.4.1.43.10.27.1.1.1.5	3com	t	f	\N	21600	f	Description	\N	\N	\N
4	3cHubMac	1.3.6.1.4.1.43.10.9.5.1.6	3com	t	f	\N	21600	f	Bridge table for 3Com HUBs	\N	\N	\N
5	3cHwVer	1.3.6.1.4.1.43.10.27.1.1.1.11	3com	t	f	\N	21600	f	Hardware version number	\N	\N	\N
6	3cIfDescr	1.3.6.1.2.1.2.2.1.2	3com	t	t	.*(Unit|Port) (\\d+)\\b.*	21600	f	3Com ifDescr for port and unit	ifDescr	IF-MIB	\N
7	3cIfMauType	1.3.6.1.2.1.26.2.1.1.3	3com	t	f	\N	21600	f	Speed and dupelx for SWxx00	ifMauType	MAU-MIB	\N
8	3cMac	1.3.6.1.4.1.43.10.27.1.1.1.2	3com	t	f	\N	21600	f	MACs on this port	\N	\N	\N
9	3cModel	1.3.6.1.4.1.43.10.27.1.1.1.19	3com	t	f	\N	21600	f	Model	\N	\N	\N
11	3cSSMac	1.3.6.1.4.1.43.10.22.2.1.3	3com	t	f	\N	21600	f	Bridge table for 3Com SuperStack	secureAddrMAC	SECURITY-MIB	\N
12	3cSerial	1.3.6.1.4.1.43.10.27.1.1.1.13	3com	t	f	\N	21600	f	Serial number	\N	\N	\N
13	3cSwVer	1.3.6.1.4.1.43.10.27.1.1.1.12	3com	t	f	\N	21600	f	Software version number	\N	\N	\N
14	3comModules	1.3.6.1.4.1.43.10.27.1.1.1.12	\N	t	f	\N	21600	f	unitChange	\N	\N	\N
15	basePortIfIndex	1.3.6.1.2.1.17.1.4.1.2	bridge-mib	t	f	\N	21600	f	Port ifindex mapping	dot1dBasePortIfIndex	BRIDGE-MIB	\N
18	c1900Duplex	1.3.6.1.4.1.437.1.1.3.3.1.1.8	Cisco	t	f	\N	21600	f	Duplex status	swPortFullDuplex	ESSWITCH.MIB	\N
19	c1900Portname	1.3.6.1.4.1.437.1.1.3.3.1.1.3	Cisco	t	f	\N	21600	f	Portname	swPortName	ESSWITCH.MIB	\N
23	cCardContainedByIndex	1.3.6.1.4.1.9.3.6.11.1.8	Cisco	t	f	\N	21600	f	cardIndex of the parent card which directly contains this card, or 0 if contained by the chassis	\N	OLD-CISCO-CHASSIS-MIB	\N
24	cCardDescr	1.3.6.1.4.1.9.3.6.11.1.3	Cisco	t	f	\N	21600	f	Slot card description	cardDescr	OLD-CISCO-CHASSIS-MIB	\N
25	cCardHwVersion	1.3.6.1.4.1.9.3.6.11.1.5	Cisco	t	f	\N	21600	f	Slot card hardware version	cardHwVersion	OLD-CISCO-CHASSIS-MIB	\N
26	cCardIndex	1.3.6.1.4.1.9.3.6.11.1.1	Cisco	t	f	\N	21600	f	Slot card type	cardIndex	OLD-CISCO-CHASSIS-MIB	\N
27	cCardSerial	1.3.6.1.4.1.9.3.6.11.1.4	Cisco	t	f	[^0]|\\w{2,}	21600	f	Slot card serial	cardSerial	OLD-CISCO-CHASSIS-MIB	\N
28	cCardSlotNumber	1.3.6.1.4.1.9.3.6.11.1.7	Cisco	t	f	\N	21600	f	Slot card slotnumber mapping	cardSlotNumber	OLD-CISCO-CHASSIS-MIB	\N
29	cCardSwVersion	1.3.6.1.4.1.9.3.6.11.1.6	Cisco	t	f	\N	21600	f	Slot card software version	cardSwVersion	OLD-CISCO-CHASSIS-MIB	\N
30	cChassisId	1.3.6.1.4.1.9.3.6.3	\N	t	f	\N	21600	f	Cisco	chassisId	OLD-CISCO-CHASSIS-MIB	\N
31	cChassisSlots	1.3.6.1.4.1.9.3.6.12	\N	t	f	\N	21600	f	Cisco	chassisSlots	OLD-CISCO-CHASSIS-MIB	\N
32	cChassisType	1.3.6.1.4.1.9.3.6.1	\N	t	f	\N	21600	f	Cisco	chassisType	OLD-CISCO-CHASSIS-MIB	\N
33	cChassisVersion	1.3.6.1.4.1.9.3.6.2	\N	t	f	\N	21600	f	Cisco	chassisVersion	OLD-CISCO-CHASSIS-MIB	\N
34	cDescr	1.3.6.1.4.1.9.3.6.11.1.3	\N	t	f	\N	21600	f	cgw	cardDescr	OLD-CISCO-CHASSIS-MIB	\N
35	cHsrpGrpStandbyState	1.3.6.1.4.1.9.9.106.1.2.1.1.15	\N	t	f	\N	21600	f	cgw	cHsrpGrpStandbyState	CISCO-HSRP-MIB	\N
36	cHsrpGrpVirtualIpAddr	1.3.6.1.4.1.9.9.106.1.2.1.1.11	\N	t	f	\N	21600	f	cgw	cHsrpGrpVirtualIpAddr	CISCO-HSRP-MIB	\N
37	cHw	1.3.6.1.4.1.9.3.6.11.1.5	\N	t	f	\N	21600	f	cgw	cardHwVersion	OLD-CISCO-CHASSIS-MIB	\N
39	cIpAddressIfIndex	1.3.6.1.4.1.9.10.86.1.1.2.1.3	\N	t	f	\N	21600	f	cgw	cIpAddressIfIndex	CISCO-IETF-IP-MIB	\N
40	cIpAddressPrefix	1.3.6.1.4.1.9.10.86.1.1.2.1.5	\N	t	f	\N	21600	f	cgw	cIpAddressPrefix	CISCO-IETF-IP-MIB	\N
41	cL3FwVer	1.3.6.1.4.1.9.9.92.1.1.1.7	cL3	t	f	\N	21600	f	Firmware version	\N	CISCO-ENTITY-ASSET-MIB	\N
42	cL3HwVer	1.3.6.1.4.1.9.9.92.1.1.1.4	cL3	t	f	\N	21600	f	Hardware version	ceAssetHardwareRevision	CISCO-ENTITY-ASSET-MIB	\N
43	cL3Model	1.3.6.1.4.1.9.9.92.1.1.1.3	cL3	t	f	\N	21600	f	Model number	ceAssetOrderablePartNumber	CISCO-ENTITY-ASSET-MIB	\N
44	cL3Serial	1.3.6.1.4.1.9.9.92.1.1.1.2	cL3	t	f	\N	21600	f	Serial number	ceAssetSerialNumber	CISCO-ENTITY-ASSET-MIB	\N
45	cL3SwVer	1.3.6.1.4.1.9.9.92.1.1.1.8	cL3	t	f	\N	21600	f	Software version	ceAssetFirmwareRevision	CISCO-ENTITY-ASSET-MIB	\N
46	cMenuDuplex	1.3.6.1.4.1.9.5.14.4.1.1.5	Cisco	t	f	\N	21600	f	Port duplex state	ciscoEsPortDuplex	CISCO-ES-STACK-MIB	\N
47	cMenuIfIndex	1.3.6.1.4.1.9.5.14.4.1.1.4	Cisco	t	f	\N	21600	f	Ifindex to port mapping	ciscoEsPortIfIndex	CISCO-ES-STACK-MIB	\N
48	cMenuMac	1.3.6.1.4.1.9.5.14.4.3.1.4.1	cisco	t	f	\N	21600	f	Bridge table for Cisco menu type switch	ciscoEsPortStnLocation	CISCO-ES-STACK-MIB	\N
49	cMenuPortStatus	1.3.6.1.4.1.9.5.14.4.1.1.29	Cisco	t	f	\N	21600	f	Port state, up or down	ciscoEsPortLinkState	CISCO-ES-STACK-MIB	\N
50	cMenuPortType	1.3.6.1.4.1.9.5.14.4.1.1.41	Cisco	t	f	\N	21600	f	Port type, media	ciscoEsPortType	CISCO-ES-STACK-MIB	\N
51	cMenuTrunk	1.3.6.1.4.1.9.5.14.4.1.1.44	Cisco	t	f	\N	21600	f	Port trunk state	ciscoEsPortISLOperStatus	CISCO-ES-STACK-MIB	\N
52	cMenuVlan	1.3.6.1.4.1.9.5.14.8.1.1.3	Cisco	t	f	\N	21600	f	Port trunk state	ciscoEsVLANPortPorts	CISCO-ES-STACK-MIB	\N
53	cModel	1.3.6.1.4.1.9.3.6.11.1.2	\N	t	f	\N	21600	f	cgw	cardType	OLD-CISCO-CHASSIS-MIB	\N
54	cSerial	1.3.6.1.4.1.9.3.6.3	\N	t	f	\N	21600	f	cgw	chassisId	OLD-CISCO-CHASSIS-MIB	\N
55	cSw	1.3.6.1.4.1.9.3.6.11.1.6	\N	t	f	\N	21600	f	cgw	cardSwVersion	OLD-CISCO-CHASSIS-MIB	\N
56	catModuleFwVer	1.3.6.1.4.1.9.5.1.3.1.1.19	cat	t	f	\N	21600	f	Module firmware version	\N	CISCO-STACK-MIB	\N
57	catModuleHwVer	1.3.6.1.4.1.9.5.1.3.1.1.18	cat	t	f	\N	21600	f	Module hardware version	\N	CISCO-STACK-MIB	\N
58	catModuleModel	1.3.6.1.4.1.9.5.1.3.1.1.17	cat	t	f	\N	21600	f	Module model	\N	CISCO-STACK-MIB	\N
16	c1900Bandwidth	1.3.6.1.4.1.437.1.1.3.7.1.0	Cricket	f	f	\N	21600	f		bandwidthUsageCurrent	ESSWITCH.MIB	Mbit/s
17	c1900BandwidthMax	1.3.6.1.4.1.437.1.1.3.7.5.0	Cricket	f	f	\N	21600	f		bandwidthUsageCurrentPeakEntry	ESSWITCH.MIB	Mbit/s
59	catModuleSerial	1.3.6.1.4.1.9.5.1.3.1.1.26	cat	t	f	\N	21600	f	Serial number	\N	CISCO-STACK-MIB	\N
60	catModuleSwVer	1.3.6.1.4.1.9.5.1.3.1.1.20	cat	t	f	\N	21600	f	Module software version	\N	CISCO-STACK-MIB	\N
61	catSerial	1.3.6.1.4.1.9.5.1.2.19	cat	t	f	\N	21600	f	Serial number	\N	\N	\N
62	cdpNeighbour	1.3.6.1.4.1.9.9.23.1.2.1.1.6	cisco	t	f	\N	21600	f	CDP neighbour	cdpCacheDeviceId	CISCO-CDP-MIB	\N
63	cdpRemoteIf	1.3.6.1.4.1.9.9.23.1.2.1.1.7	cisco	t	f	\N	21600	f	CDP remote interface	cdpCacheDevicePort	CISCO-CDP-MIB	\N
66	dnscheck	1.3.6.1.2.1.1.5.0	mib-II	f	t	\N	21600	f	Used by the DNSCheck plugin; is identical to sysname	sysName	SNMPv2-MIB	\N
67	flashFree	1.3.6.1.4.1.9.9.10.1.1.4.1.1.5	cisco	t	f	\N	21600	f	Flash free	ciscoFlashPartitionFreeSpace	CISCO-FLASH-MIB	\N
68	flashName	1.3.6.1.4.1.9.9.10.1.1.4.1.1.10	cisco	t	f	\N	21600	f	Flash name	 ciscoFlashPartitionName	CISCO-FLASH-MIB	\N
69	flashSize	1.3.6.1.4.1.9.9.10.1.1.4.1.1.4	cisco	t	f	\N	21600	f	Flash size	ciscoFlashPartitionSize	CISCO-FLASH-MIB	\N
70	hpFwVer	1.3.6.1.4.1.11.2.14.11.5.1.1.4.0	hp	f	f	\N	21600	f	Firmware revision number	\N	\N	\N
71	hpModules	1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.4	hp	t	f	\N	21600	f	unitChange	\N	\N	\N
72	hpPortType	1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2	hp	t	f	\N	21600	f	Type of each port (media, duplex)	\N	\N	\N
73	hpStack	1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1	hp	t	f	\N	21600	f	Lists modules in the stack	\N	\N	\N
74	hpStackName	1.3.6.1.4.1.11.2.14.11.5.1.10.3.1.0	hp	f	f	\N	21600	f	Name of stack	\N	\N	\N
76	hpSwVer	1.3.6.1.4.1.11.2.14.11.5.1.1.3.0	hp	f	f	\N	21600	f	Software version number	\N	\N	\N
77	hpVlan	1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1	hp	t	f	\N	21600	f	Vlan for each port	\N	\N	\N
81	ifAdminStatus	1.3.6.1.2.1.2.2.1.7	mib-II	t	f	\N	21600	f	standard	ifAdminStatus	IF-MIB	\N
82	ifAlias	1.3.6.1.2.1.31.1.1.1.18	mib-II	t	f	\N	21600	f	standard	ifAlias	IF-MIB	\N
83	ifDescr	1.3.6.1.2.1.2.2.1.2	mib-II	t	f	\N	21600	f	standard	ifDescr	IF-MIB	\N
94	ifIndex	1.3.6.1.2.1.2.2.1.1	mib-II	t	f	\N	21600	f	standard	ifIndex	IF-MIB	\N
96	ifMtu	1.3.6.1.2.1.2.2.1.4	mib-II	t	f	\N	21600	f	standard	ifMtu	IF-MIB	\N
97	ifName	1.3.6.1.2.1.31.1.1.1.1	mib-II	t	f	\N	21600	f	standard	ifName	IF-MIB	\N
98	ifNumber	1.3.6.1.2.1.2.1.0	mib-II	f	f	\N	21600	f	standard	ifNumber	IF-MIB	\N
99	ifOperStatus	1.3.6.1.2.1.2.2.1.8	mib-II	t	f	\N	21600	f	standard	ifOperStatus	IF-MIB	\N
106	ifPhysAddress	1.3.6.1.2.1.2.2.1.6	mib-II	t	f	\N	21600	f	standard	ifPhysAddress	IF-MIB	\N
107	ifPortName	1.3.6.1.4.1.9.2.2.1.1.28	\N	t	f	\N	21600	f	ios-sw	locIfDescr	OLD-CISCO-INTERFACES-MIB	\N
108	ifSerial	1.3.6.1.2.1.47.1.1.1.1.11.1	\N	f	f	\N	21600	f	standard	entPhysicalSerialNum	ENTITY-MIB	\N
109	ifSpeed	1.3.6.1.2.1.2.2.1.5	mib-II	t	f	\N	21600	f	standard	ifSpeed	IF-MIB	\N
110	ifHighSpeed	1.3.6.1.2.1.31.1.1.1.15	mib-II	t	f	\N	21600	f	Interface speed as a number of Mbps	ifHighSpeed	IF-MIB	\N
111	ifTrunk	1.3.6.1.4.1.9.9.46.1.6.1.1.14	\N	t	f	\N	21600	f	cL3-sw	vlanTrunkPortDynamicStatus	CISCO-VTP-MIB	\N
112	ifType	1.3.6.1.2.1.2.2.1.3	mib-II	t	f	\N	21600	f	standard	ifType	IF-MIB	\N
113	ifVlan	1.3.6.1.4.1.9.9.68.1.2.2.1.2	\N	t	f	\N	21600	f	ios-sw	vmVlan	CISCO-VLAN-MEMBERSHIP-MIB	\N
114	ifVlansAllowed	1.3.6.1.4.1.9.9.46.1.6.1.1.4	\N	t	f	\N	21600	f	cL3-sw	vlanTrunkPortVlansEnabled	CISCO-VTP-MIB	\N
115	iosDuplex	1.3.6.1.4.1.9.9.87.1.4.1.1.32.0	\N	t	f	\N	21600	f	ios-sw	c2900PortDuplexStatus	CISCO-C2900-MIB	\N
116	iosPortIfindex	1.3.6.1.4.1.9.9.87.1.4.1.1.25.0	\N	t	f	\N	21600	f	ios-sw	c2900PortIfIndex	CISCO-C2900-MIB	\N
117	iosTrunk	1.3.6.1.4.1.9.9.87.1.4.1.1.6.0	\N	t	f	\N	21600	f	ios-sw	c2900PortMayForwardFrames	CISCO-C2900-MIB	\N
118	ipAdEntIfIndex	1.3.6.1.2.1.4.20.1.2	\N	t	f	\N	21600	f	cgw	ipAdEntIfIndex	IP-MIB	\N
85	ifHCInUcastPkts	1.3.6.1.2.1.31.1.1.1.7	mib-II	t	f	\N	21600	f		ifHCInUcastPkts	IF-MIB	packets
87	ifHCOutUcastPkts	1.3.6.1.2.1.31.1.1.1.11	mib-II	t	f	\N	21600	f		ifHCOutUcastPkts	IF-MIB	packets
88	ifInDiscards	1.3.6.1.2.1.2.2.1.13	mib-II	t	f	\N	21600	f		ifInDiscards	IF-MIB	packets
84	ifHCInOctets	1.3.6.1.2.1.31.1.1.1.6	mib-II	t	f	\N	21600	f	The total number of octets received on the interface, including framing characters. This object is a 64-bit version of ifInOctets.	ifHCInOctets	IF-MIB	bytes/s
119	ipAdEntIfNetMask	1.3.6.1.2.1.4.20.1.3	\N	t	f	\N	21600	f	cgw	ipAdEntNetMas	IP-MIB	\N
121	ipRouteDest	1.3.6.1.2.1.4.21.1.1	\N	t	f	\N	21600	f	The destination IP address of this route	ipRouteDest	RFC1213	\N
122	ipRouteIfIndex	1.3.6.1.2.1.4.21.1.2	\N	t	f	\N	21600	f	The index value which uniquely identifies the local interface through which the next hop of this route should be reached	ipRouteIfIndex	RFC1213	\N
123	ipRouteMask	1.3.6.1.2.1.4.21.1.11	\N	t	f	\N	21600	f	Indicate the mask to be logical-ANDed with the destination address before being compared to the value in the ipRouteDest field	ipRouteMask	RFC1213	\N
124	ipRouteNextHop	1.3.6.1.2.1.4.21.1.7	\N	t	f	\N	21600	f	The IP address of the next hop of this route	ipRouteNextHop	RFC1213	\N
125	ipRouteProto	1.3.6.1.2.1.4.21.1.9	\N	t	f	\N	21600	f	The routing mechanism via which this route was learned	ipRouteProto	RFC1213	\N
126	ipRouteType	1.3.6.1.2.1.4.21.1.8	\N	t	f	\N	21600	f	The type of route, 1=other, 2=invalid, 3=direct, 4=indirect	ipRouteType	RFC1213	\N
127	ipv6AddrPfxLength	1.3.6.1.2.1.55.1.8.1.2	IPV6-MIB	t	f	\N	21600	f	Prefices	ipv6AddrPfxLength	IPV6-MIB	\N
129	macPortEntry	1.3.6.1.2.1.17.4.3.1.2	bridge-mib	t	f	\N	21600	f	Bridge table for various switches	dot1dTpFdbPort	BRIDGE-MIB	\N
132	memFree	1.3.6.1.4.1.9.9.48.1.1.1.6	cisco	t	f	\N	21600	f	Mem free	ciscoMemoryPoolFree	CISCO-MEMORY-POOL-MIB	\N
133	memName	1.3.6.1.4.1.9.9.48.1.1.1.2	cisco	t	f	\N	21600	f	Mem name	ciscoMemoryPoolName	CISCO-MEMORY-POOL-MIB	\N
134	memUsed	1.3.6.1.4.1.9.9.48.1.1.1.5	cisco	t	f	\N	21600	f	Mem used	ciscoMemoryPoolUsed	CISCO-MEMORY-POOL-MIB	\N
136	ospfIfMetricMetric	1.3.6.1.2.1.14.8.1.4	\N	t	f	\N	21600	f	cgw	ospfIfMetricValue	OSPF-MIB	\N
137	physClass	1.3.6.1.2.1.47.1.1.1.1.5	mib-II	t	f	\N	21600	f	An indication of the general hardware type of the physical entity	entPhysicalClass	ENTITY-MIB	\N
138	physContainedIn	1.3.6.1.2.1.47.1.1.1.1.4	mib-II	t	f	\N	21600	f	The value of entPhysicalIndex for the physical entity which contains this physical entity	entPhysicalContainedIn	ENTITY-MIB	\N
139	physDescr	1.3.6.1.2.1.47.1.1.1.1.2	mib-II	t	f	\N	21600	f	A textual description of physical entity	entPhysicalDescr	ENTITY-MIB	\N
140	physFwVer	1.3.6.1.2.1.47.1.1.1.1.9	mib-II	t	f	\N	21600	f	The vendor-specific firmware revision string for the physical entity	entPhysicalFirmwareRev	ENTITY-MIB	\N
141	physHwVer	1.3.6.1.2.1.47.1.1.1.1.8	mib-II	t	f	\N	21600	f	The vendor-specific hardware revision string for the physical entity	entPhysicalHardwareRev	ENTITY-MIB	\N
142	physMfgName	1.3.6.1.2.1.47.1.1.1.1.12	mib-II	t	f	\N	21600	f	The name of the manufacturer of this physical component	entPhysicalMfgName	ENTITY-MIB	\N
143	physModelName	1.3.6.1.2.1.47.1.1.1.1.13	mib-II	t	f	\N	21600	f	The vendor-specific model name identifier string associated with this physical component	entPhysicalModelName	ENTITY-MIB	\N
144	physName	1.3.6.1.2.1.47.1.1.1.1.7	mib-II	t	f	\N	21600	f	The textual name of the physical entity	entPhysicalName	ENTITY-MIB	\N
145	physParentRelPos	1.3.6.1.2.1.47.1.1.1.1.6	mib-II	t	f	\N	21600	f		entPhysicalParentRelPos	ENTITY-MIB	\N
146	physSerial	1.3.6.1.2.1.47.1.1.1.1.11	mib-II	t	f	\N	21600	f	The vendor-specific serial number string for the physical entity	entPhysicalSerialNum	ENTITY-MIB	\N
147	physSwVer	1.3.6.1.2.1.47.1.1.1.1.10	mib-II	t	f	\N	21600	f	The vendor-specific software revision string for the physical entity	entPhysicalSoftwareRev	ENTITY-MIB	\N
148	portDuplex	1.3.6.1.4.1.9.5.1.4.1.1.10	\N	t	f	\N	21600	f	cat-sw	portDuplex	CISCO-STACK-MIB	\N
149	portIfIndex	1.3.6.1.4.1.9.5.1.4.1.1.11	\N	t	f	\N	21600	f	cat-sw	portIfIndex	CISCO-STACK-MIB	\N
150	portPortName	1.3.6.1.4.1.9.5.1.4.1.1.4	\N	t	f	\N	21600	f	cat-sw	portName	CISCO-STACK-MIB	\N
151	portTrunk	1.3.6.1.4.1.9.5.1.9.3.1.8	\N	t	f	\N	21600	f	cat-sw	vlanPortIslOperStatus	CISCO-STACK-MIB	\N
152	portVlan	1.3.6.1.4.1.9.5.1.9.3.1.3	\N	t	f	\N	21600	f	cat-sw	vlanPortVlan	CISCO-STACK-MIB	\N
153	portVlansAllowed	1.3.6.1.4.1.9.5.1.9.3.1.5	\N	t	f	\N	21600	f	cat-sw	vlanPortIslVlansAllowed	CISCO-STACK-MIB	\N
154	stpPortState	1.3.6.1.2.1.17.2.15.1.3	bridge-mib	t	f	\N	21600	f	Spanning tree port state	dot1dStpPortState	BRIDGE-MIB	\N
155	sysDescr	1.3.6.1.2.1.1.1.0	mib-II	f	f	\N	21600	f		sysDescr	SNMPv2-MIB	\N
156	sysLocation	1.3.6.1.2.1.1.6	mib-II	t	f	\N	21600	f	System location	sysLocation	SNMPv2-MIB	\N
158	sysname	1.3.6.1.2.1.1.5.0	\N	f	f	\N	21600	f	all	sysName	SNMPv2-MIB	\N
159	typeoid	1.3.6.1.2.1.1.2.0	\N	f	f	\N	21600	f	all	sysObjectID	SNMPv2-MIB	\N
169	vtpVlanState	1.3.6.1.4.1.9.9.46.1.3.1.1.2	cisco	t	f	\N	21600	f	The state of this VLAN	vtpVlanState	CISCO-VTP-MIB	\N
10	3cPS40PortState	1.3.6.1.2.1.26.1.1.1.6	3com	t	f	\N	3600	f	Port state for 3Com PS40	rpMauMediaAvailable	MAU-MIB	\N
75	hpStackStatsMemberOperStatus	1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.5	hp	t	f	\N	3600	f	HP stack member status	hpStackStatsMemberOperStatus	HP-MIB	\N
135	moduleMon	1.3.6.1.2.1.2.2.1.1	mib-II	t	f	\N	3600	f	Used by the module monitor; is identical to ifIndex	ifIndex	IF-MIB	\N
38	cInetNetToMediaPhysAddress	1.3.6.1.4.1.9.10.86.1.1.3.1.3	\N	t	f	\N	1800	f	ARP cache	cInetNetToMediaPhysAddress	CISCO-IETF-IP-MIB	\N
120	ipNetToMediaPhysAddress	1.3.6.1.2.1.4.22.1.2	mib-II	t	f	\N	1800	f	ARP cache	ipNetToMediaPhysAddress	RFC1213-MIB	\N
128	ipv6NetToMediaPhysAddress	1.3.6.1.2.1.55.1.12.1.2	IPV6-MIB	t	f	\N	1800	f	ARP cache	ipv6NetToMediaPhysAddress	IPV6-MIB	\N
20	c2900Bandwidth	1.3.6.1.4.1.9.9.87.1.5.1.0	Cricket	f	f	\N	21600	f		c2900BandwidthUsageCurrent	CISCO-C2900-MIB	Mbit/s
21	c5000Bandwidth	1.3.6.1.4.1.9.5.1.1.8.0	Cricket	f	f	\N	21600	f		sysTraffic	CISCO-STACK-MIB	Mbit/s
157	sysUpTime	1.3.6.1.2.1.1.3.0	mib-II	f	f	\N	21600	f		sysUpTime	SNMPv2-MIB	timeticks
171	ipIfStatsHCInOctets.ipv6	1.3.6.1.2.1.4.31.3.1.6.2	IP-MIB	t	f	\N	21600	f	\N	\N	IP-MIB	bytes/s
170	ipIfStatsHCInOctets.ipv4	1.3.6.1.2.1.4.31.3.1.6.1	IP-MIB	t	f	\N	21600	f	\N	\N	IP-MIB	bytes/s
86	ifHCOutOctets	1.3.6.1.2.1.31.1.1.1.10	mib-II	t	f	\N	21600	f	The total number of octets transmitted out of the interface, including framing characters. This object is a 64-bit version of ifOutOctets.	ifHCOutOctets	IF-MIB	bytes/s
91	ifInOctets	1.3.6.1.2.1.2.2.1.10	mib-II	t	f	\N	21600	f	Number of octets received on the interface	ifInOctets	IF-MIB	bytes/s
22	c5000BandwidthMax	1.3.6.1.4.1.9.5.1.1.19.0	Cricket	f	f	\N	21600	f		sysTrafficPeak	CISCO-STACK-MIB	Mbit/s
64	cpu1min	1.3.6.1.4.1.9.2.1.57.0	Cricket	f	f	\N	21600	f		avgBusy1	OLD-CISCO-CPU-MIB	%
65	cpu5min	1.3.6.1.4.1.9.2.1.58.0	Cricket	f	f	\N	21600	f		avgBusy5	OLD-CISCO-CPU-MIB	%
78	hpcpu	1.3.6.1.4.1.11.2.14.11.5.1.9.6.1.0	Cricket	f	f	\N	21600	f		\N	\N	%
79	hpmem5minFree	1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6.1	Cricket	f	f	\N	21600	f		\N	\N	bytes
80	hpmem5minUsed	1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.7.1	Cricket	f	f	\N	21600	f		\N	\N	bytes
130	mem5minFree	1.3.6.1.4.1.9.9.48.1.1.1.6.1	Cricket	f	f	\N	21600	f		ciscoMemoryPoolFree	CISCO-MEMORY-POOL-MIB	bytes
131	mem5minUsed	1.3.6.1.4.1.9.9.48.1.1.1.5.1	Cricket	f	f	\N	21600	f		ciscoMemoryPoolUsed	CISCO-MEMORY-POOL-MIB	bytes
160	ucd_cpuIdle	1.3.6.1.4.1.2021.11.11.0	Cricket	f	f	\N	21600	f		\N	\N	%
161	ucd_cpuSystem	1.3.6.1.4.1.2021.11.10.0	Cricket	f	f	\N	21600	f		\N	\N	%
162	ucd_cpuUser	1.3.6.1.4.1.2021.11.9.0	Cricket	f	f	\N	21600	f		\N	\N	%
163	ucd_load15min	1.3.6.1.4.1.2021.10.1.3.3	Cricket	f	f	\N	21600	f		\N	\N	load
164	ucd_load1min	1.3.6.1.4.1.2021.10.1.3.1	Cricket	f	f	\N	21600	f		\N	\N	load
165	ucd_load5min	1.3.6.1.4.1.2021.10.1.3.2	Cricket	f	f	\N	21600	f		\N	\N	load
166	ucd_memrealAvail	1.3.6.1.4.1.2021.4.6.0	Cricket	f	f	\N	21600	f		\N	\N	bytes
167	ucd_memswapAvail	1.3.6.1.4.1.2021.4.4.0	Cricket	f	f	\N	21600	f		\N	\N	bytes
168	ucd_memtotalAvail	1.3.6.1.4.1.2021.4.11.0	Cricket	f	f	\N	21600	f		\N	\N	bytes
89	ifInErrors	1.3.6.1.2.1.2.2.1.14	mib-II	t	f	\N	21600	f	Number of inbound packets that contained errors	ifInErrors	IF-MIB	packets
90	ifInNUcastPkts	1.3.6.1.2.1.2.2.1.12	mib-II	t	f	\N	21600	f		ifInNUcastPkts	IF-MIB	packets
92	ifInUcastPkts	1.3.6.1.2.1.2.2.1.11	mib-II	t	f	\N	21600	f	Packets which were not addressed to a multicast or broadcast address at this sub-layer	ifInUcastPkts	IF-MIB	packets
93	ifInUnknownProtos	1.3.6.1.2.1.2.2.1.15	mib-II	t	f	\N	21600	f		ifInUnknownProtos	IF-MIB	packets
95	ifLastChange	1.3.6.1.2.1.2.2.1.9	mib-II	t	f	\N	21600	f	standard	ifLastChange	IF-MIB	timeticks
100	ifOutDiscards	1.3.6.1.2.1.2.2.1.19	mib-II	t	f	\N	21600	f		ifOutDiscards	IF-MIB	packets
101	ifOutErrors	1.3.6.1.2.1.2.2.1.20	mib-II	t	f	\N	21600	f	Number of outbound packets that could not be transmitted because of errors	ifOutErrors	IF-MIB	packets
102	ifOutNUcastPkts	1.3.6.1.2.1.2.2.1.18	mib-II	t	f	\N	21600	f		ifOutNUcastPkts	IF-MIB	packets
104	ifOutQLen	1.3.6.1.2.1.2.2.1.21	mib-II	t	f	\N	21600	f		ifOutQLen	IF-MIB	packets
105	ifOutUcastPkts	1.3.6.1.2.1.2.2.1.17	mib-II	t	f	\N	21600	f	Packets that higher-level protocols requested be transmitted, and which were not addressed to a multicast or broadcast address at this sub-layer	ifOutUcastPkts	IF-MIB	packets
103	ifOutOctets	1.3.6.1.2.1.2.2.1.16	mib-II	t	f	\N	21600	f	Number of octets transmitted out of the interface	ifOutOctets	IF-MIB	bytes/s
\.


--
-- Name: snmpoid_snmpoidid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('snmpoid_snmpoidid_seq', 171, true);


--
-- Data for Name: subsystem; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY subsystem (name, descr) FROM stdin;
eventEngine	\N
pping	\N
serviceping	\N
moduleMon	\N
thresholdMon	\N
trapParser	\N
cricket	\N
deviceManagement	\N
getDeviceData	\N
devBrowse	\N
maintenance	\N
snmptrapd	\N
macwatch	\N
ipdevpoll	\N
powersupplywatch	\N
\.


--
-- Data for Name: swportallowedvlan; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY swportallowedvlan (interfaceid, hexstring) FROM stdin;
447	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
320	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
449	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
450	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
326	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
327	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
328	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
329	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
332	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
334	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
448	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
338	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
340	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
342	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
478	0400000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
407	0000020000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
409	0000020000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
422	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
423	00000000000000000000c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
424	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
425	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
426	0400000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
427	0400000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
336	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
321	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
481	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
482	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
483	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
484	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
519	7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
\.


--
-- Data for Name: swportblocked; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY swportblocked (interfaceid, vlan, swportblockedid) FROM stdin;
409	109	1
\.


--
-- Name: swportblocked_swportblockedid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('swportblocked_swportblockedid_seq', 1, true);


--
-- Data for Name: swportvlan; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY swportvlan (swportvlanid, interfaceid, vlanid, direction) FROM stdin;
5	521	6	n
6	522	7	n
7	523	8	n
8	354	8	n
9	551	12	n
24	451	6	n
38	356	8	n
39	348	8	n
40	350	8	n
41	352	8	n
50	379	6	n
55	358	8	n
56	360	12	n
57	361	7	n
58	365	8	n
59	367	8	n
60	368	6	n
61	374	6	n
62	375	6	n
63	376	6	n
64	378	6	n
25	326	8	o
26	326	12	o
27	326	6	o
28	326	7	o
29	327	8	o
30	327	12	o
31	327	6	o
32	327	7	o
33	329	8	o
34	329	12	o
35	329	6	o
36	329	7	o
42	481	8	n
43	481	12	n
44	481	6	n
45	481	7	n
46	482	8	n
47	482	12	n
48	482	6	n
49	482	7	n
51	484	8	n
52	484	12	n
53	484	6	n
54	484	7	n
1	519	8	n
2	519	12	n
3	519	6	n
4	519	7	n
16	447	8	o
17	447	12	o
18	447	6	o
19	447	7	o
\.


--
-- Name: swportvlan_swportvlanid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('swportvlan_swportvlanid_seq', 65, true);


--
-- Data for Name: thresholdrule; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY thresholdrule (id, target, alert, clear, raw, description, creator_id, created, period) FROM stdin;
\.


--
-- Name: thresholdrule_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('thresholdrule_id_seq', 1, false);


--
-- Data for Name: type; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY type (typeid, vendorid, typename, sysobjectid, descr) FROM stdin;
1	3com	PS40	1.3.6.1.4.1.43.10.27.4.1	Portstack 40 hub
2	3com	SW1100	1.3.6.1.4.1.43.10.27.4.1.2.1	Portswitch 1100
3	3com	SW3300	1.3.6.1.4.1.43.10.27.4.1.2.2	Portswitch 3300
4	3com	SW9300	1.3.6.1.4.1.43.1.16.2.2.2.1	Portswitch 9300
5	alcatel	alcatel6200	1.3.6.1.4.1.6486.800.1.1.2.2.4.1.4	OmniStack LS 6200
6	alcatel	alcatel6200-X	1.3.6.1.4.1.6486.800.1.1.2.2.4.1.3	Alcatel Omnistack LS 6200 (seems to be multiple IDs for this model)
7	alcatel	alcatel6800	1.3.6.1.4.1.6486.800.1.1.2.1.6.1.1	Alcatel Omniswitch 6800
8	cisco	cat3560G	1.3.6.1.4.1.9.1.617	Catalyst 3560G
9	cisco	cat6504	1.3.6.1.4.1.9.1.657	Catalyst
10	cisco	catalyst2924XL	1.3.6.1.4.1.9.1.183	Catalyst 2924 XL switch
11	cisco	catalyst2924XLv	1.3.6.1.4.1.9.1.217	Catalyst 2924 XLv switch
12	cisco	catalyst295024	1.3.6.1.4.1.9.1.324	Catalyst 2950-24
13	cisco	catalyst295024G	1.3.6.1.4.1.9.1.428	Catalyst 2950G-24-E1 switch
14	cisco	catalyst295048G	1.3.6.1.4.1.9.1.429	Catalyst 295048G
15	cisco	catalyst297024TS	1.3.6.1.4.1.9.1.561	Catalyst 2970
16	cisco	catalyst3508GXL	1.3.6.1.4.1.9.1.246	Catalyst 3508 GXL switch
17	cisco	catalyst3524XL	1.3.6.1.4.1.9.1.248	Catalyst 3524 XL switch
18	cisco	catalyst3524tXLEn	1.3.6.1.4.1.9.1.287	Catalyst 3524tXLEn
19	cisco	catalyst375024ME	1.3.6.1.4.1.9.1.574	Catalyst 3750 Metro
20	cisco	catalyst37xxStack	1.3.6.1.4.1.9.1.516	Catalyst 3750
21	cisco	catalyst4003	1.3.6.1.4.1.9.5.40	Catalyst 4003
22	cisco	catalyst4006	1.3.6.1.4.1.9.1.448	Catalyst 4006 sup 2 L3 switch
23	cisco	catalyst4506	1.3.6.1.4.1.9.1.502	Catalyst 4506 sup4 L3 switch
24	cisco	catalyst4510	1.3.6.1.4.1.9.1.537	Catalyst 4510
25	cisco	catalyst6509	1.3.6.1.4.1.9.1.283	Catalyst 6509
26	cisco	cisco1000	1.3.6.1.4.1.9.1.40	Cisco 1000 Router
27	cisco	cisco1003	1.3.6.1.4.1.9.1.41	Cisco 1003 Router
28	cisco	cisco1005	1.3.6.1.4.1.9.1.49	Cisco 1005 Router
29	cisco	cisco10720	1.3.6.1.4.1.9.1.397	Cisco 10720 (YB) Router
30	cisco	cisco12016	1.3.6.1.4.1.9.1.273	Cisco 12016 (GSR) Router
31	cisco	cisco12404	1.3.6.1.4.1.9.1.423	Cisco 12404 (GSR) Router
32	cisco	cisco12416	1.3.6.1.4.1.9.1.385	Cisco 12416 (GSR) Router
33	cisco	cisco1601	1.3.6.1.4.1.9.1.113	Cisco 1601 Router
34	cisco	cisco1602	1.3.6.1.4.1.9.1.114	Cisco 1602 Router
35	cisco	cisco1603	1.3.6.1.4.1.9.1.115	Cisco 1603 Router
36	cisco	cisco1604	1.3.6.1.4.1.9.1.116	Cisco 1604 Router
37	cisco	cisco1721	1.3.6.1.4.1.9.1.444	Cisco 1721 Router
38	cisco	cisco1751	1.3.6.1.4.1.9.1.326	Cisco 1751 Router
39	cisco	cisco2500	1.3.6.1.4.1.9.1.13	Cisco 2500 Router
40	cisco	cisco2501	1.3.6.1.4.1.9.1.17	Cisco 2501 Router
41	cisco	cisco2502	1.3.6.1.4.1.9.1.18	Cisco 2502 Router
42	cisco	cisco2503	1.3.6.1.4.1.9.1.19	Cisco 2503 Router
43	cisco	cisco2511	1.3.6.1.4.1.9.1.27	Cisco 2511 Router
44	cisco	cisco2514	1.3.6.1.4.1.9.1.30	Cisco 2514 Router
45	cisco	cisco2821	1.3.6.1.4.1.9.1.577	Cisco 2821 router
46	cisco	cisco3620	1.3.6.1.4.1.9.1.122	Cisco 3620 Router
47	cisco	cisco3640	1.3.6.1.4.1.9.1.110	Cisco 3640 Router
48	cisco	cisco4000	1.3.6.1.4.1.9.1.7	Cisco 4000 Router
49	cisco	cisco4500	1.3.6.1.4.1.9.1.14	Cisco 4500 Router
50	cisco	cisco4700	1.3.6.1.4.1.9.1.50	Cisco 4700 Router
51	cisco	cisco7010	1.3.6.1.4.1.9.1.12	Cisco 7010 Router
52	cisco	cisco7204	1.3.6.1.4.1.9.1.125	Cisco 7204 Router
53	cisco	cisco7204VXR	1.3.6.1.4.1.9.1.223	Cisco 7204VXR Router
54	cisco	cisco7206	1.3.6.1.4.1.9.1.108	Cisco 7206 Router
55	cisco	cisco7206VXR	1.3.6.1.4.1.9.1.222	Cisco 7206VXR Router
56	cisco	cisco7505	1.3.6.1.4.1.9.1.48	Cisco 7505 Router
57	cisco	cisco7507	1.3.6.1.4.1.9.1.45	Cisco 7507 Router
58	cisco	cisco7513	1.3.6.1.4.1.9.1.46	Cisco 7513 Router
59	cisco	ciscoAIRAP1130	1.3.6.1.4.1.9.1.618	Cisco AP 1130
60	cisco	ciscoAIRAP1210	1.3.6.1.4.1.9.1.525	Cisco AP 1200
61	cisco	ciscoAIRAP350IOS	1.3.6.1.4.1.9.1.552	Cisco AP 350
62	cisco	ciscoAS5200	1.3.6.1.4.1.9.1.109	Cisco AS5200
63	cisco	ciscoVPN3030	1.3.6.1.4.1.3076.1.2.1.1.1.2	Cisco 3030 VPN concentrator
64	cisco	ciscoWSX5302	1.3.6.1.4.1.9.1.168	Cisco RSM Router
65	cisco	wsc2926	1.3.6.1.4.1.9.5.35	Catalyst 2926 switch
66	cisco	wsc2980g	1.3.6.1.4.1.9.5.49	Catalyst 2980g
67	cisco	wsc2980ga	1.3.6.1.4.1.9.5.51	Catalyst 2980ga
68	cisco	wsc4006	1.3.6.1.4.1.9.5.46	Catalyst 4006 switch
69	cisco	wsc5000	1.3.6.1.4.1.9.5.7	Catalyst 5000 switch
70	cisco	wsc5500	1.3.6.1.4.1.9.5.17	Catalyst 5500 switch
71	cisco	wsc5505	1.3.6.1.4.1.9.5.34	Catalyst 5505 switch
72	hp	hp2524	1.3.6.1.4.1.11.2.3.7.11.19	ProCurve Switch 2524
73	hp	hp2626A	1.3.6.1.4.1.11.2.3.7.11.34	ProCurve Switch 2626 (J4900A)
74	hp	hp2626B	1.3.6.1.4.1.11.2.3.7.11.45	ProCurve Switch 2626 (J4900B)
75	hp	hp2650A	1.3.6.1.4.1.11.2.3.7.11.29	ProCurve Switch 2650 (J4899A)
76	hp	hp2650B	1.3.6.1.4.1.11.2.3.7.11.44	ProCurve Switch 2650 (J4899B)
77	juniper	T640	1.3.6.1.4.1.2636.1.1.1.2.6	Juniper T640
78	juniper	juniperM7i	1.3.6.1.4.1.2636.1.1.1.2.10	Juniper Networks, Inc. m7i internet router
79	juniper	m320	1.3.6.1.4.1.2636.1.1.1.2.9	Juniper Networks, Inc. m320 internet router
80	nortel	nortel5510	1.3.6.1.4.1.45.3.53.1	Nortel Baystack 5510-48T Switch
82	cisco	s6523_rp	1.3.6.1.4.1.9.1.720	s6523_rp Software (s6523_rp-ADVIPSERVICESK9-M)
81	cisco	cat4500e-LANBASEK9-M	1.3.6.1.4.1.9.1.875	Catalyst 4500 L3 Switch Software
83	unknown	1.3.6.1.4.1.2636.1.1.1.2.31	1.3.6.1.4.1.2636.1.1.1.2.31	Juniper Networks, Inc. ex4200-48t Ethernet Switch, kernel JUNOS 12.3R5.7, Build date: 2013-12-18 02:58:32 UTC Copyright (c) 1996-2013 Juniper Networks, Inc.
\.


--
-- Name: type_typeid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('type_typeid_seq', 83, true);


--
-- Data for Name: unrecognized_neighbor; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY unrecognized_neighbor (id, netboxid, interfaceid, remote_id, remote_name, source, since, ignored_since) FROM stdin;
1	2	340	00:1b:78:6e:c0:2f	VcD_804b1694f05c	lldp	2015-05-06 10:40:21.95407	\N
2	2	342	00:1b:78:6e:c0:2f	VcD_804b1694f05c	lldp	2015-05-06 10:40:21.964904	\N
3	2	338	00:1b:78:6e:c0:2f	VcD_804b1694f05c	lldp	2015-05-06 10:40:21.968405	\N
4	2	424	00:1b:78:6e:c0:23	VcD_804b1694f05c	lldp	2015-05-06 10:40:21.971682	\N
5	2	334	00:1b:78:6e:e0:53	VcD_804b1694f05c	lldp	2015-05-06 10:40:21.978063	\N
6	2	365	e8:39:35:e8:0e:b9		lldp	2015-05-06 10:40:21.981315	\N
7	2	321	f8:c0:01:c9:1d:80	teknobyen-sw2	lldp	2015-05-06 10:40:21.988403	\N
8	2	409	54:e0:32:9d:a1:40	sw-ex4550-5	lldp	2015-05-06 10:40:21.995481	\N
9	2	332	00:1b:78:6e:e0:53	VcD_804b1694f05c	lldp	2015-05-06 10:40:22.057637	\N
10	2	425	10.10.1.2	005056820000	cdp	2015-05-06 10:40:22.0964	\N
12	2	320	f8:c0:01:c9:1d:80	teknobyen-sw2	lldp	2015-05-06 10:40:22.106901	\N
13	2	422	00:1c:f9:b2:84:00	trd-gw7.uninett.no	lldp	2015-05-06 10:40:22.114364	\N
15	2	336	00:1b:78:6e:e0:53	VcD_804b1694f05c	lldp	2015-05-06 10:40:22.124504	\N
16	2	407	54:e0:32:9d:a1:40	sw-ex4550-5	lldp	2015-05-06 10:40:22.129061	\N
17	2	425	158.38.129.84	0050568200d3	cdp	2015-05-06 10:40:22.133353	\N
19	2	425	00:1b:78:6e:c0:31	VcD_804b1694f05c	lldp	2015-05-06 10:40:22.145976	\N
30	3	512	128.39.70.9	trd-gw7.uninett.no	cdp	2015-05-06 11:28:45.024642	\N
42	3	511	158.38.1.145	uninett-gw.uninett.no	cdp	2015-05-06 11:46:34.622476	\N
\.


--
-- Name: unrecognized_neighbor_id_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('unrecognized_neighbor_id_seq', 42, true);


--
-- Data for Name: usage; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY usage (usageid, descr) FROM stdin;
\.


--
-- Data for Name: vendor; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY vendor (vendorid) FROM stdin;
alcatel
allied
avaya
breezecom
cisco
dlink
hp
symbol
3com
nortel
juniper
unknown
\.


--
-- Data for Name: vlan; Type: TABLE DATA; Schema: manage; Owner: nav
--

COPY vlan (vlanid, vlan, nettype, orgid, usageid, netident, description) FROM stdin;
13	\N	elink	\N	\N	blaasal-trd2,trd-gw7	lokal fiber
14	\N	loopback	\N	\N	\N	\N
15	\N	elink	\N	\N	uninett-gsw2.uninett-gsw1	lokal lacp
2	\N	link	\N	\N	teknobyen-blaasal2,uninett-gsw2	lokal fiber
6	5	link	\N	\N	uninett.uninettbladserv-management	VRRP ethernet
7	6	link	\N	\N	uninett.uninettbladserv-HostOSManagement	VRRP ethernet
8	8	link	\N	\N	uninett.uninettbladserv-GuestOS	VRRP ethernet
12	131	link	\N	\N	uninett.uninett-sip-server	lokal vlan
\.


--
-- Name: vlan_vlanid_seq; Type: SEQUENCE SET; Schema: manage; Owner: nav
--

SELECT pg_catalog.setval('vlan_vlanid_seq', 20, true);


SET search_path = profiles, pg_catalog;

--
-- Data for Name: account; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY account (id, login, name, password, ext_sync) FROM stdin;
0	default	Default User		\N
1	admin	NAV Administrator	{sha1}s3F6XX/D$L3vU8Rs2bTJ4zArBLVIPbh7cN9Q=	\N
\.


--
-- Name: account_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('account_id_seq', 1000, false);


--
-- Data for Name: account_navlet; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY account_navlet (id, navlet, account, col, displayorder, preferences) FROM stdin;
13	nav.web.navlets.messages.MessagesNavlet	0	1	2	\N
14	nav.web.navlets.navblog.NavBlogNavlet	0	2	0	\N
15	nav.web.navlets.linklist.LinkListNavlet	0	2	1	\N
12	nav.web.navlets.status2.Status2Widget	0	1	1	{"status_filter": "event_type=boxState&stateless_threshold=24", "refresh_interval": 60000}
21	nav.web.navlets.watchdog.WatchDogWidget	1	2	0	{"refresh_interval": 600000}
19	nav.web.navlets.navblog.NavBlogNavlet	1	3	0	\N
17	nav.web.navlets.status2.Status2Widget	1	1	0	{"status_filter": "interval=600&event_type=boxState&stateless_threshold=24", "refresh_interval": 600000}
\.


--
-- Name: account_navlet_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('account_navlet_id_seq', 21, true);


--
-- Data for Name: accountalertqueue; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountalertqueue (id, account_id, alert_id, subscription_id, insertion_time) FROM stdin;
\.


--
-- Name: accountalertqueue_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountalertqueue_id_seq', 1, false);


--
-- Data for Name: accountgroup; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountgroup (id, name, descr) FROM stdin;
1	NAV Administrators	Full access to everything
2	Everyone	Unauthenticated and authenticated users
3	Authenticated users	Any authenticated user (logged in)
1000	SMS	Allowed to receive SMS alerts
\.


--
-- Data for Name: accountgroup_accounts; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountgroup_accounts (id, account_id, accountgroup_id) FROM stdin;
1	0	2
2	1	1
3	1	2
4	1	3
\.


--
-- Name: accountgroup_accounts_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountgroup_accounts_id_seq', 4, true);


--
-- Name: accountgroup_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountgroup_id_seq', 1000, true);


--
-- Data for Name: accountgroupprivilege; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountgroupprivilege (id, accountgroupid, privilegeid, target) FROM stdin;
1	2	2	^/about/.*
2	2	2	^/images/.*
3	2	2	^/js/.*
4	2	2	^/style/.*
5	2	2	^/alertprofiles/wap/.*
6	2	2	^/$
7	2	2	^/toolbox\\b
8	2	2	^/index(.py)?/(index|login|logout|passwd)\\b
9	2	2	^/userinfo/?
10	2	2	^/messages/(active|historic|planned|view|rss)\\b
11	2	2	^/maintenance/(calendar|active|historic|planned|view)\\b
12	2	2	^/geomap$
13	2	2	^/geomap/open
15	1000	3	sms
16	2	2	^/ajax/open/?
14	3	2	^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap|info|netmap)/?
18	2	2	^/navlets/.*
17	2	2	^/search/osm_map_redirect/?
19	3	2	^/graphite/?
20	3	2	^/search/?
\.


--
-- Name: accountgroupprivilege_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountgroupprivilege_id_seq', 20, true);


--
-- Data for Name: accountorg; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountorg (id, account_id, organization_id) FROM stdin;
\.


--
-- Name: accountorg_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountorg_id_seq', 1, false);


--
-- Data for Name: accountproperty; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accountproperty (id, accountid, property, value) FROM stdin;
1	1	widget_columns	3
\.


--
-- Name: accountproperty_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accountproperty_id_seq', 1, true);


--
-- Data for Name: accounttool; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY accounttool (account_tool_id, toolname, accountid, display, priority) FROM stdin;
\.


--
-- Name: accounttool_account_tool_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('accounttool_account_tool_id_seq', 1, false);


--
-- Data for Name: alertaddress; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY alertaddress (id, accountid, type, address) FROM stdin;
\.


--
-- Name: alertaddress_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('alertaddress_id_seq', 1000, false);


--
-- Data for Name: alertpreference; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY alertpreference (accountid, activeprofile, lastsentday, lastsentweek) FROM stdin;
\.


--
-- Data for Name: alertprofile; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY alertprofile (id, accountid, name, daily_dispatch_time, weekly_dispatch_day, weekly_dispatch_time) FROM stdin;
\.


--
-- Name: alertprofile_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('alertprofile_id_seq', 1000, false);


--
-- Data for Name: alertsender; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY alertsender (id, name, handler) FROM stdin;
1	Email	email
2	SMS	sms
3	Jabber	jabber
\.


--
-- Name: alertsender_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('alertsender_id_seq', 1000, false);


--
-- Data for Name: alertsubscription; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY alertsubscription (id, alert_address_id, time_period_id, filter_group_id, subscription_type, ignore_resolved_alerts) FROM stdin;
\.


--
-- Name: alertsubscription_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('alertsubscription_id_seq', 1, false);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
r4giboc7vwwsecjn4l18enax4u2sckwl	YmNhNTM1ODA3MWJlMDY4MWVjNzJlY2JkZTRkOTgyMWQyZDIzN2EyODqAAn1xAShVCG1lc3NhZ2VzXVUKYWNjb3VudF9pZEsBdS4=	2015-05-06 12:38:24.175648+00
\.


--
-- Data for Name: expression; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY expression (id, filter_id, match_field_id, operator, value) FROM stdin;
26	29	13	11	GSW|GW
27	13	12	4	100
25	30	13	11	EDGE|GSW|SW
28	31	13	11	GSW|SW
29	14	11	11	boxDown|boxUp
30	15	11	11	boxShadow|boxSunny
31	25	11	11	boxDownWarning|boxShadowWarning
32	16	10	0	moduleState
43	32	13	0	EDGE
44	33	13	0	WLAN
45	34	13	0	SRV
46	35	13	0	OTHER
47	36	10	0	boxState
52	26	10	0	serviceState
53	27	10	0	thresholdState
55	20	12	2	20
57	21	12	2	40
58	28	10	0	deviceChanged
59	23	12	2	60
61	24	12	2	80
\.


--
-- Name: expression_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('expression_id_seq', 1000, false);


--
-- Data for Name: filter; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY filter (id, owner_id, name) FROM stdin;
13	\N	F01: All alerts
29	\N	F02: All router alerts
30	\N	F03: All switch (core and edge) alerts
31	\N	F04: All core switch alerts
32	\N	F05: All edge switch alerts
33	\N	F06: All alerts from wireless boxes
34	\N	F07: All alerts from servers
35	\N	F08: All alerts from OTHER equipment
36	\N	F09: All boxState alerts
14	\N	F10: All box up/down alerts
15	\N	F11: All box sunny/shadow alerts
25	\N	F12: All boxState early warnings
16	\N	F13: All module outage alerts
26	\N	F14: All services alerts
27	\N	F15: All threshold alerts
28	\N	F16: All device change alerts
20	\N	F17: All alerts with severity >= Warning
21	\N	F18: All alerts with severity >= Errors
23	\N	F19: All alerts with severity >= Critical
24	\N	F20: All alerts with severity = Emergency
\.


--
-- Name: filter_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('filter_id_seq', 1000, false);


--
-- Data for Name: filtergroup; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY filtergroup (id, owner_id, name, description) FROM stdin;
71	\N	G01: All alerts	This filter group matches every alert. The group can i.e. be used to give a group permission to receive all alerts.
62	\N	G02: All router alerts	
63	\N	G03: All switch (core and edge) alerts	
64	\N	G04: All core switch alerts	
65	\N	G05: All edge switch alert	
68	\N	G06: All alerts from wireless boxes	
69	\N	G07: All alerts from servers	
70	\N	G08: All alerts from OTHER equipment	
72	\N	G09: All boxState alerts	
73	\N	G10: All box up/down alerts	
74	\N	G11: All box sunny/shadow alerts	
75	\N	G12: All boxState early warnings	
76	\N	G13: All module outage alerts	
77	\N	G14: All services alerts	
78	\N	G15: All threshold alerts	
79	\N	G16: All device change alerts	
81	\N	G17: All alerts with severity >= Warning	
82	\N	G18: All alerts with severity >= Errors	
83	\N	G19: All alerts with severity >= Critical	
84	\N	G20: All alerts with severity = Emergency	
\.


--
-- Data for Name: filtergroup_group_permission; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY filtergroup_group_permission (id, accountgroup_id, filtergroup_id) FROM stdin;
1	1	71
\.


--
-- Name: filtergroup_group_permission_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('filtergroup_group_permission_id_seq', 1, true);


--
-- Name: filtergroup_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('filtergroup_id_seq', 1000, false);


--
-- Data for Name: filtergroupcontent; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY filtergroupcontent (id, include, positive, priority, filter_id, filter_group_id) FROM stdin;
1	t	t	1	29	62
2	t	t	1	30	63
3	t	t	2	31	64
4	t	t	1	32	65
5	t	t	1	33	68
6	t	t	1	34	69
7	t	t	1	13	71
8	t	t	1	35	70
9	t	t	1	36	72
10	t	t	1	14	73
11	t	t	1	15	74
12	t	t	1	25	75
13	t	t	1	16	76
14	t	t	1	26	77
15	t	t	1	27	78
16	t	t	1	28	79
17	t	t	1	20	81
18	t	t	1	21	82
19	t	t	1	23	83
20	t	t	1	24	84
\.


--
-- Name: filtergroupcontent_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('filtergroupcontent_id_seq', 20, true);


--
-- Data for Name: matchfield; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY matchfield (id, name, description, value_help, value_id, value_name, value_sort, list_limit, data_type, show_list) FROM stdin;
10	Event type	Event type: An event type describes a category of alarms. (Please note that alarm type is a more refined attribute. There are a set of alarm types within an event type.)	\N	eventtype.eventtypeid	eventtype.eventtypedesc	eventtype.eventtypeid	1000	0	t
11	Alert type	Alert type: An alert type describes the various values an event type may take.	\N	alerttype.alerttype	alerttype.alerttypedesc	alerttype.alerttypeid	1000	0	t
12	Severity	Severity: Limit your alarms based on severity.	Range: Severities are in the range 0-100, where 100 is most severe.	alertq.severity	\N	\N	1000	1	f
13	Category	Category: All equipment is categorized in 7 main categories.	\N	cat.catid	cat.descr	cat.catid	1000	0	t
15	Sysname	Sysname: Limit your alarms based on sysname.	Sysname examples:<blockquote>\n<b>Starts with:</b> samson.<br>\n<b>Ends with:</b> .stud.ntnu.no<br>\n<b>Contains:</b> .studby.<br>\n<b>Regexp:</b> [sbm][0-2][0-9]{2}[a-z]\\.studby\\.ntnu\\.no</blockquote>	netbox.sysname	\N	\N	1000	0	f
16	IP address	Limit your alarms based on an IP address/range (prefix)	examples:<blockquote>\n129.241.190.190<br>\n129.241.190.0/24</br>\n129.241.0.0/16</blockquote>	netbox.ip	\N	\N	1000	2	f
17	Room	Room: Limit your alarms based on room.	\N	room.roomid	room.descr	room.roomid	1000	0	t
18	Location	Location: Limit your alarms based on location (a location contains a set of rooms) 	\N	location.locationid	location.descr	location.descr	1000	0	t
19	Organization	Organization: Limit your alarms based on the organization ownership of the alarm in question.	\N	org.orgid	org.descr	org.descr	1000	0	t
20	Usage	Usage: Different network prefixes are mapped to usage areas.	\N	usage.usageid	usage.descr	usage.descr	1000	0	t
21	Type	Type: Limit your alarms equipment type	\N	type.typename	type.descr	type.descr	1000	0	t
22	Equipment vendor	Equipment vendor: Limit alert by the vendor of the netbox.	\N	vendor.vendorid	vendor.vendorid	vendor.vendorid	1000	0	t
14	Group	Group: netboxes may belong to a group that is independent of type and category	\N	netboxgroup.netboxgroupid	netboxgroup.descr	netboxgroup.descr	1000	0	t
\.


--
-- Name: matchfield_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('matchfield_id_seq', 1000, false);


--
-- Data for Name: navbarlink; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY navbarlink (id, accountid, name, uri) FROM stdin;
\.


--
-- Name: navbarlink_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('navbarlink_id_seq', 1000, false);


--
-- Data for Name: netmap_view; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY netmap_view (viewid, owner, title, zoom, is_public, last_modified, topology, display_elinks, display_orphans, description, location_room_filter) FROM stdin;
\.


--
-- Data for Name: netmap_view_categories; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY netmap_view_categories (id, viewid, catid) FROM stdin;
\.


--
-- Name: netmap_view_categories_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('netmap_view_categories_id_seq', 1, false);


--
-- Data for Name: netmap_view_defaultview; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY netmap_view_defaultview (id, viewid, ownerid) FROM stdin;
\.


--
-- Name: netmap_view_defaultview_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('netmap_view_defaultview_id_seq', 1, false);


--
-- Data for Name: netmap_view_nodeposition; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY netmap_view_nodeposition (id, viewid, netboxid, x, y) FROM stdin;
\.


--
-- Name: netmap_view_nodeposition_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('netmap_view_nodeposition_id_seq', 1, false);


--
-- Name: netmap_view_viewid_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('netmap_view_viewid_seq', 1, false);


--
-- Data for Name: operator; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY operator (id, operator_id, match_field_id) FROM stdin;
1	0	10
2	11	10
3	0	11
4	11	11
5	0	12
6	1	12
7	2	12
8	3	12
9	4	12
10	5	12
11	0	13
12	11	13
13	0	14
14	11	14
15	0	15
16	5	15
17	6	15
18	7	15
19	8	15
20	9	15
21	0	16
22	11	16
23	0	17
24	11	17
25	0	18
26	11	18
27	0	19
28	11	19
29	0	20
30	11	20
31	0	21
32	11	21
33	0	22
34	11	22
\.


--
-- Name: operator_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('operator_id_seq', 34, true);


--
-- Name: operator_operator_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('operator_operator_id_seq', 1, false);


--
-- Data for Name: privilege; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY privilege (privilegeid, privilegename) FROM stdin;
2	web_access
3	alert_by
\.


--
-- Name: privilege_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('privilege_id_seq', 10000, false);


--
-- Data for Name: smsq; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY smsq (id, accountid, "time", phone, msg, sent, smsid, timesent, severity) FROM stdin;
\.


--
-- Name: smsq_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('smsq_id_seq', 1, false);


--
-- Data for Name: statuspreference; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY statuspreference (id, name, "position", type, accountid, services, states) FROM stdin;
1	IP devices down	1	netbox	0		n
2	IP devices in shadow	2	netbox	0		s
4	Modules down/in shadow	4	module	0		n,s
5	Services down	5	service	0		n,s
3	IP devices on maintenance	3	netbox_maintenance	0		y,n,s
6	Thresholds exceeded	6	threshold	0		n,s
7	SNMP agents down	7	snmpagent	0		n,s
8	Links down	8	linkstate	0		n,s
\.


--
-- Data for Name: statuspreference_category; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY statuspreference_category (id, statuspreference_id, category_id) FROM stdin;
\.


--
-- Name: statuspreference_category_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('statuspreference_category_id_seq', 1, false);


--
-- Name: statuspreference_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('statuspreference_id_seq', 1000, false);


--
-- Data for Name: statuspreference_organization; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY statuspreference_organization (id, statuspreference_id, organization_id) FROM stdin;
\.


--
-- Name: statuspreference_organization_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('statuspreference_organization_id_seq', 1, false);


--
-- Data for Name: timeperiod; Type: TABLE DATA; Schema: profiles; Owner: nav
--

COPY timeperiod (id, alert_profile_id, start_time, valid_during) FROM stdin;
\.


--
-- Name: timeperiod_id_seq; Type: SEQUENCE SET; Schema: profiles; Owner: nav
--

SELECT pg_catalog.setval('timeperiod_id_seq', 1000, false);


SET search_path = radius, pg_catalog;

--
-- Data for Name: radiusacct; Type: TABLE DATA; Schema: radius; Owner: nav
--

COPY radiusacct (radacctid, acctsessionid, acctuniqueid, username, realm, nasipaddress, nasporttype, cisconasport, acctstarttime, acctstoptime, acctsessiontime, acctinputoctets, acctoutputoctets, calledstationid, callingstationid, acctterminatecause, framedprotocol, framedipaddress, acctstartdelay, acctstopdelay) FROM stdin;
\.


--
-- Name: radiusacct_radacctid_seq; Type: SEQUENCE SET; Schema: radius; Owner: nav
--

SELECT pg_catalog.setval('radiusacct_radacctid_seq', 1, false);


--
-- Data for Name: radiuslog; Type: TABLE DATA; Schema: radius; Owner: nav
--

COPY radiuslog (id, "time", type, message, status, username, client, port) FROM stdin;
\.


--
-- Name: radiuslog_id_seq; Type: SEQUENCE SET; Schema: radius; Owner: nav
--

SELECT pg_catalog.setval('radiuslog_id_seq', 1, false);


SET search_path = arnold, pg_catalog;

--
-- Name: block_pkey; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY block
    ADD CONSTRAINT block_pkey PRIMARY KEY (blockid);


--
-- Name: blocked_reason_pkey; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY blocked_reason
    ADD CONSTRAINT blocked_reason_pkey PRIMARY KEY (blocked_reasonid);


--
-- Name: event_pkey; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY event
    ADD CONSTRAINT event_pkey PRIMARY KEY (eventid);


--
-- Name: identity_mac_swportid_key; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY identity
    ADD CONSTRAINT identity_mac_swportid_key UNIQUE (mac, swportid);


--
-- Name: identity_pkey; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY identity
    ADD CONSTRAINT identity_pkey PRIMARY KEY (identityid);


--
-- Name: quarantine_vlan_unique; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY quarantine_vlans
    ADD CONSTRAINT quarantine_vlan_unique UNIQUE (vlan);


--
-- Name: quarantine_vlans_pkey; Type: CONSTRAINT; Schema: arnold; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY quarantine_vlans
    ADD CONSTRAINT quarantine_vlans_pkey PRIMARY KEY (quarantineid);


SET search_path = logger, pg_catalog;

--
-- Name: category_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY category
    ADD CONSTRAINT category_pkey PRIMARY KEY (category);


--
-- Name: errorerror_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY errorerror
    ADD CONSTRAINT errorerror_pkey PRIMARY KEY (id);


--
-- Name: log_message_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY log_message
    ADD CONSTRAINT log_message_pkey PRIMARY KEY (id);


--
-- Name: log_message_type_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY log_message_type
    ADD CONSTRAINT log_message_type_pkey PRIMARY KEY (type);


--
-- Name: log_message_type_priority_facility_mnemonic_key; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY log_message_type
    ADD CONSTRAINT log_message_type_priority_facility_mnemonic_key UNIQUE (priority, facility, mnemonic);


--
-- Name: origin_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY origin
    ADD CONSTRAINT origin_pkey PRIMARY KEY (origin);


--
-- Name: priority_keyword_key; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY priority
    ADD CONSTRAINT priority_keyword_key UNIQUE (keyword);


--
-- Name: priority_pkey; Type: CONSTRAINT; Schema: logger; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY priority
    ADD CONSTRAINT priority_pkey PRIMARY KEY (priority);


SET search_path = manage, pg_catalog;

--
-- Name: adjacency_candidate_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_pkey PRIMARY KEY (adjacency_candidateid);


--
-- Name: adjacency_candidate_uniq; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_uniq UNIQUE (netboxid, interfaceid, to_netboxid, source);


--
-- Name: alerthist_ack_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthist_ack
    ADD CONSTRAINT alerthist_ack_pkey PRIMARY KEY (alert_id);


--
-- Name: alerthist_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_pkey PRIMARY KEY (alerthistid);


--
-- Name: alerthistmsg_alerthistid_state_msgtype_language_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthistmsg
    ADD CONSTRAINT alerthistmsg_alerthistid_state_msgtype_language_key UNIQUE (alerthistid, state, msgtype, language);


--
-- Name: alerthistmsg_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthistmsg
    ADD CONSTRAINT alerthistmsg_pkey PRIMARY KEY (id);


--
-- Name: alerthistvar_alerthistid_state_var_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthistvar
    ADD CONSTRAINT alerthistvar_alerthistid_state_var_key UNIQUE (alerthistid, state, var);


--
-- Name: alerthistvar_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerthistvar
    ADD CONSTRAINT alerthistvar_pkey PRIMARY KEY (id);


--
-- Name: alertq_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_pkey PRIMARY KEY (alertqid);


--
-- Name: alertqmsg_alertqid_msgtype_language_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertqmsg
    ADD CONSTRAINT alertqmsg_alertqid_msgtype_language_key UNIQUE (alertqid, msgtype, language);


--
-- Name: alertqmsg_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertqmsg
    ADD CONSTRAINT alertqmsg_pkey PRIMARY KEY (id);


--
-- Name: alertqvar_alertqid_var_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertqvar
    ADD CONSTRAINT alertqvar_alertqid_var_key UNIQUE (alertqid, var);


--
-- Name: alertqvar_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertqvar
    ADD CONSTRAINT alertqvar_pkey PRIMARY KEY (id);


--
-- Name: alerttype_eventalert_unique; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerttype
    ADD CONSTRAINT alerttype_eventalert_unique UNIQUE (eventtypeid, alerttype);


--
-- Name: alerttype_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alerttype
    ADD CONSTRAINT alerttype_pkey PRIMARY KEY (alerttypeid);


--
-- Name: apitoken_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY apitoken
    ADD CONSTRAINT apitoken_pkey PRIMARY KEY (id);


--
-- Name: arp_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY arp
    ADD CONSTRAINT arp_pkey PRIMARY KEY (arpid);


--
-- Name: cabling_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY cabling
    ADD CONSTRAINT cabling_pkey PRIMARY KEY (cablingid);


--
-- Name: cabling_roomid_jack_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY cabling
    ADD CONSTRAINT cabling_roomid_jack_key UNIQUE (roomid, jack);


--
-- Name: cam_netboxid_sysname_module_port_mac_start_time_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY cam
    ADD CONSTRAINT cam_netboxid_sysname_module_port_mac_start_time_key UNIQUE (netboxid, sysname, module, port, mac, start_time);


--
-- Name: cam_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY cam
    ADD CONSTRAINT cam_pkey PRIMARY KEY (camid);


--
-- Name: cat_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY cat
    ADD CONSTRAINT cat_pkey PRIMARY KEY (catid);


--
-- Name: device_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY device
    ADD CONSTRAINT device_pkey PRIMARY KEY (deviceid);


--
-- Name: device_serial_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY device
    ADD CONSTRAINT device_serial_key UNIQUE (serial);


--
-- Name: eventq_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_pkey PRIMARY KEY (eventqid);


--
-- Name: eventqvar_eventqid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY eventqvar
    ADD CONSTRAINT eventqvar_eventqid_key UNIQUE (eventqid, var);


--
-- Name: eventqvar_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY eventqvar
    ADD CONSTRAINT eventqvar_pkey PRIMARY KEY (id);


--
-- Name: eventtype_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY eventtype
    ADD CONSTRAINT eventtype_pkey PRIMARY KEY (eventtypeid);


--
-- Name: gwportprefix_gwip_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY gwportprefix
    ADD CONSTRAINT gwportprefix_gwip_key UNIQUE (gwip);


--
-- Name: iftype_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY iana_iftype
    ADD CONSTRAINT iftype_pkey PRIMARY KEY (iftype);


--
-- Name: image_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY image
    ADD CONSTRAINT image_pkey PRIMARY KEY (imageid);


--
-- Name: interface_netboxid_ifindex_unique; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_netboxid_ifindex_unique UNIQUE (netboxid, ifindex);


--
-- Name: interface_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_pkey PRIMARY KEY (interfaceid);


--
-- Name: interface_stack_higher_lower_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY interface_stack
    ADD CONSTRAINT interface_stack_higher_lower_key UNIQUE (higher, lower);


--
-- Name: interface_stack_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY interface_stack
    ADD CONSTRAINT interface_stack_pkey PRIMARY KEY (id);


--
-- Name: ipdevpoll_job_log_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY ipdevpoll_job_log
    ADD CONSTRAINT ipdevpoll_job_log_pkey PRIMARY KEY (id);


--
-- Name: location_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY location
    ADD CONSTRAINT location_pkey PRIMARY KEY (locationid);


--
-- Name: macwatch_match_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY macwatch_match
    ADD CONSTRAINT macwatch_match_pkey PRIMARY KEY (id);


--
-- Name: macwatch_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY macwatch
    ADD CONSTRAINT macwatch_pkey PRIMARY KEY (id);


--
-- Name: macwatch_unique_mac; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY macwatch
    ADD CONSTRAINT macwatch_unique_mac UNIQUE (mac);


--
-- Name: maint_component_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY maint_component
    ADD CONSTRAINT maint_component_pkey PRIMARY KEY (maint_taskid, key, value);


--
-- Name: maint_task_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY maint_task
    ADD CONSTRAINT maint_task_pkey PRIMARY KEY (maint_taskid);


--
-- Name: mem_netboxid_memtype_device_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY mem
    ADD CONSTRAINT mem_netboxid_memtype_device_key UNIQUE (netboxid, memtype, device);


--
-- Name: mem_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY mem
    ADD CONSTRAINT mem_pkey PRIMARY KEY (memid);


--
-- Name: message_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY message
    ADD CONSTRAINT message_pkey PRIMARY KEY (messageid);


--
-- Name: message_to_maint_task_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY message_to_maint_task
    ADD CONSTRAINT message_to_maint_task_pkey PRIMARY KEY (messageid, maint_taskid);


--
-- Name: module_deviceid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY module
    ADD CONSTRAINT module_deviceid_key UNIQUE (deviceid);


--
-- Name: module_netboxid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY module
    ADD CONSTRAINT module_netboxid_key UNIQUE (netboxid, name);


--
-- Name: module_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY module
    ADD CONSTRAINT module_pkey PRIMARY KEY (moduleid);


--
-- Name: netbios_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbios
    ADD CONSTRAINT netbios_pkey PRIMARY KEY (netbiosid);


--
-- Name: netbox_deviceid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_deviceid_key UNIQUE (deviceid);


--
-- Name: netbox_ip_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_ip_key UNIQUE (ip);


--
-- Name: netbox_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_pkey PRIMARY KEY (netboxid);


--
-- Name: netbox_sysname_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_sysname_key UNIQUE (sysname);


--
-- Name: netbox_vtpvlan_netboxid_vtpvlan_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox_vtpvlan
    ADD CONSTRAINT netbox_vtpvlan_netboxid_vtpvlan_key UNIQUE (netboxid, vtpvlan);


--
-- Name: netbox_vtpvlan_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netbox_vtpvlan
    ADD CONSTRAINT netbox_vtpvlan_pkey PRIMARY KEY (id);


--
-- Name: netboxcategory_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxcategory
    ADD CONSTRAINT netboxcategory_pkey PRIMARY KEY (netboxid, category);


--
-- Name: netboxinfo_netboxid_key_var_val_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxinfo
    ADD CONSTRAINT netboxinfo_netboxid_key_var_val_key UNIQUE (netboxid, key, var, val);


--
-- Name: netboxinfo_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxinfo
    ADD CONSTRAINT netboxinfo_pkey PRIMARY KEY (netboxinfoid);


--
-- Name: netboxsnmpoid_netboxid_snmpoidid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxsnmpoid
    ADD CONSTRAINT netboxsnmpoid_netboxid_snmpoidid_key UNIQUE (netboxid, snmpoidid);


--
-- Name: netboxsnmpoid_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxsnmpoid
    ADD CONSTRAINT netboxsnmpoid_pkey PRIMARY KEY (id);


--
-- Name: nettype_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY nettype
    ADD CONSTRAINT nettype_pkey PRIMARY KEY (nettypeid);


--
-- Name: org_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY org
    ADD CONSTRAINT org_pkey PRIMARY KEY (orgid);


--
-- Name: patch_interfaceid_cablingid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY patch
    ADD CONSTRAINT patch_interfaceid_cablingid_key UNIQUE (interfaceid, cablingid);


--
-- Name: patch_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY patch
    ADD CONSTRAINT patch_pkey PRIMARY KEY (patchid);


--
-- Name: powersupply_or_fan_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY powersupply_or_fan
    ADD CONSTRAINT powersupply_or_fan_pkey PRIMARY KEY (powersupplyid);


--
-- Name: prefix_netaddr_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY prefix
    ADD CONSTRAINT prefix_netaddr_key UNIQUE (netaddr);


--
-- Name: prefix_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY prefix
    ADD CONSTRAINT prefix_pkey PRIMARY KEY (prefixid);


--
-- Name: room_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY room
    ADD CONSTRAINT room_pkey PRIMARY KEY (roomid);


--
-- Name: rproto_attr_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY rproto_attr
    ADD CONSTRAINT rproto_attr_pkey PRIMARY KEY (id);


--
-- Name: rrd_datasource_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY rrd_datasource
    ADD CONSTRAINT rrd_datasource_pkey PRIMARY KEY (rrd_datasourceid);


--
-- Name: rrd_file_path_filename_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY rrd_file
    ADD CONSTRAINT rrd_file_path_filename_key UNIQUE (path, filename);


--
-- Name: rrd_file_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY rrd_file
    ADD CONSTRAINT rrd_file_pkey PRIMARY KEY (rrd_fileid);


--
-- Name: schema_change_log_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY schema_change_log
    ADD CONSTRAINT schema_change_log_pkey PRIMARY KEY (id);


--
-- Name: sensor_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY sensor
    ADD CONSTRAINT sensor_pkey PRIMARY KEY (sensorid);


--
-- Name: service_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY service
    ADD CONSTRAINT service_pkey PRIMARY KEY (serviceid);


--
-- Name: serviceproperty_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY serviceproperty
    ADD CONSTRAINT serviceproperty_pkey PRIMARY KEY (serviceid, property);


--
-- Name: snmpoid_oidkey_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY snmpoid
    ADD CONSTRAINT snmpoid_oidkey_key UNIQUE (oidkey);


--
-- Name: snmpoid_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY snmpoid
    ADD CONSTRAINT snmpoid_pkey PRIMARY KEY (snmpoidid);


--
-- Name: subcat_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netboxgroup
    ADD CONSTRAINT subcat_pkey PRIMARY KEY (netboxgroupid);


--
-- Name: subsystem_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY subsystem
    ADD CONSTRAINT subsystem_pkey PRIMARY KEY (name);


--
-- Name: swportallowedvlan_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY swportallowedvlan
    ADD CONSTRAINT swportallowedvlan_pkey PRIMARY KEY (interfaceid);


--
-- Name: swportblocked_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY swportblocked
    ADD CONSTRAINT swportblocked_pkey PRIMARY KEY (swportblockedid);


--
-- Name: swportblocked_uniq; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY swportblocked
    ADD CONSTRAINT swportblocked_uniq UNIQUE (interfaceid, vlan);


--
-- Name: swportvlan_interfaceid_vlanid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY swportvlan
    ADD CONSTRAINT swportvlan_interfaceid_vlanid_key UNIQUE (interfaceid, vlanid);


--
-- Name: swportvlan_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY swportvlan
    ADD CONSTRAINT swportvlan_pkey PRIMARY KEY (swportvlanid);


--
-- Name: thresholdrule_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY thresholdrule
    ADD CONSTRAINT thresholdrule_pkey PRIMARY KEY (id);


--
-- Name: type_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY type
    ADD CONSTRAINT type_pkey PRIMARY KEY (typeid);


--
-- Name: type_sysobjectid_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY type
    ADD CONSTRAINT type_sysobjectid_key UNIQUE (sysobjectid);


--
-- Name: type_vendorid_typename_key; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY type
    ADD CONSTRAINT type_vendorid_typename_key UNIQUE (vendorid, typename);


--
-- Name: unrecognized_neighbor_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY unrecognized_neighbor
    ADD CONSTRAINT unrecognized_neighbor_pkey PRIMARY KEY (id);


--
-- Name: usage_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY usage
    ADD CONSTRAINT usage_pkey PRIMARY KEY (usageid);


--
-- Name: vendor_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY vendor
    ADD CONSTRAINT vendor_pkey PRIMARY KEY (vendorid);


--
-- Name: vlan_pkey; Type: CONSTRAINT; Schema: manage; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_pkey PRIMARY KEY (vlanid);


SET search_path = profiles, pg_catalog;

--
-- Name: account_login_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY account
    ADD CONSTRAINT account_login_key UNIQUE (login);


--
-- Name: account_navlet_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY account_navlet
    ADD CONSTRAINT account_navlet_pkey PRIMARY KEY (id);


--
-- Name: account_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: accountalertqueue_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountalertqueue
    ADD CONSTRAINT accountalertqueue_pkey PRIMARY KEY (id);


--
-- Name: accountgroup_accounts_account_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountgroup_accounts
    ADD CONSTRAINT accountgroup_accounts_account_id_key UNIQUE (account_id, accountgroup_id);


--
-- Name: accountgroup_accounts_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountgroup_accounts
    ADD CONSTRAINT accountgroup_accounts_pkey PRIMARY KEY (id);


--
-- Name: accountgroup_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountgroup
    ADD CONSTRAINT accountgroup_pkey PRIMARY KEY (id);


--
-- Name: accountgroupprivilege_accountgroupid_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountgroupprivilege
    ADD CONSTRAINT accountgroupprivilege_accountgroupid_key UNIQUE (accountgroupid, privilegeid, target);


--
-- Name: accountgroupprivilege_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountgroupprivilege
    ADD CONSTRAINT accountgroupprivilege_pkey PRIMARY KEY (id);


--
-- Name: accountorg_accountid_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountorg
    ADD CONSTRAINT accountorg_accountid_key UNIQUE (account_id, organization_id);


--
-- Name: accountorg_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountorg
    ADD CONSTRAINT accountorg_pkey PRIMARY KEY (id);


--
-- Name: accountproperty_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accountproperty
    ADD CONSTRAINT accountproperty_pkey PRIMARY KEY (id);


--
-- Name: accounttool_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY accounttool
    ADD CONSTRAINT accounttool_pkey PRIMARY KEY (account_tool_id);


--
-- Name: alertaddress_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertaddress
    ADD CONSTRAINT alertaddress_pkey PRIMARY KEY (id);


--
-- Name: alertpreference_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertpreference
    ADD CONSTRAINT alertpreference_pkey PRIMARY KEY (accountid);


--
-- Name: alertprofile_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertprofile
    ADD CONSTRAINT alertprofile_pkey PRIMARY KEY (id);


--
-- Name: alertsender_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertsender
    ADD CONSTRAINT alertsender_pkey PRIMARY KEY (id);


--
-- Name: alertsender_unique_handler; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertsender
    ADD CONSTRAINT alertsender_unique_handler UNIQUE (handler);


--
-- Name: alertsender_unique_name; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertsender
    ADD CONSTRAINT alertsender_unique_name UNIQUE (name);


--
-- Name: alertsubscription_alert_address_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertsubscription
    ADD CONSTRAINT alertsubscription_alert_address_id_key UNIQUE (alert_address_id, time_period_id, filter_group_id);


--
-- Name: alertsubscription_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY alertsubscription
    ADD CONSTRAINT alertsubscription_pkey PRIMARY KEY (id);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: expression_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY expression
    ADD CONSTRAINT expression_pkey PRIMARY KEY (id);


--
-- Name: filter_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filter
    ADD CONSTRAINT filter_pkey PRIMARY KEY (id);


--
-- Name: filtergroup_group_permission_accountgroup_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filtergroup_group_permission
    ADD CONSTRAINT filtergroup_group_permission_accountgroup_id_key UNIQUE (accountgroup_id, filtergroup_id);


--
-- Name: filtergroup_group_permission_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filtergroup_group_permission
    ADD CONSTRAINT filtergroup_group_permission_pkey PRIMARY KEY (id);


--
-- Name: filtergroup_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filtergroup
    ADD CONSTRAINT filtergroup_pkey PRIMARY KEY (id);


--
-- Name: filtergroupcontent_filter_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filtergroupcontent
    ADD CONSTRAINT filtergroupcontent_filter_id_key UNIQUE (filter_id, filter_group_id);


--
-- Name: filtergroupcontent_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY filtergroupcontent
    ADD CONSTRAINT filtergroupcontent_pkey PRIMARY KEY (id);


--
-- Name: matchfield_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY matchfield
    ADD CONSTRAINT matchfield_pkey PRIMARY KEY (id);


--
-- Name: navbarlink_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY navbarlink
    ADD CONSTRAINT navbarlink_pkey PRIMARY KEY (id);


--
-- Name: netmap_view_categories_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netmap_view_categories
    ADD CONSTRAINT netmap_view_categories_pkey PRIMARY KEY (viewid, catid);


--
-- Name: netmap_view_defaultview_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netmap_view_defaultview
    ADD CONSTRAINT netmap_view_defaultview_pkey PRIMARY KEY (viewid, ownerid);


--
-- Name: netmap_view_nodeposition_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netmap_view_nodeposition
    ADD CONSTRAINT netmap_view_nodeposition_pkey PRIMARY KEY (viewid, netboxid);


--
-- Name: netmap_view_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY netmap_view
    ADD CONSTRAINT netmap_view_pkey PRIMARY KEY (viewid);


--
-- Name: operator_operator_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY operator
    ADD CONSTRAINT operator_operator_id_key UNIQUE (operator_id, match_field_id);


--
-- Name: operator_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY operator
    ADD CONSTRAINT operator_pkey PRIMARY KEY (id);


--
-- Name: privilege_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY privilege
    ADD CONSTRAINT privilege_pkey PRIMARY KEY (privilegeid);


--
-- Name: privilege_privilegename_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY privilege
    ADD CONSTRAINT privilege_privilegename_key UNIQUE (privilegename);


--
-- Name: smsq_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY smsq
    ADD CONSTRAINT smsq_pkey PRIMARY KEY (id);


--
-- Name: statuspreference_category_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY statuspreference_category
    ADD CONSTRAINT statuspreference_category_pkey PRIMARY KEY (id);


--
-- Name: statuspreference_category_statuspreference_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY statuspreference_category
    ADD CONSTRAINT statuspreference_category_statuspreference_id_key UNIQUE (statuspreference_id, category_id);


--
-- Name: statuspreference_organization_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY statuspreference_organization
    ADD CONSTRAINT statuspreference_organization_pkey PRIMARY KEY (id);


--
-- Name: statuspreference_organization_statuspreference_id_key; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY statuspreference_organization
    ADD CONSTRAINT statuspreference_organization_statuspreference_id_key UNIQUE (statuspreference_id, organization_id);


--
-- Name: statuspreference_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY statuspreference
    ADD CONSTRAINT statuspreference_pkey PRIMARY KEY (id);


--
-- Name: timeperiod_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY timeperiod
    ADD CONSTRAINT timeperiod_pkey PRIMARY KEY (id);


SET search_path = radius, pg_catalog;

--
-- Name: radiusacct_pkey; Type: CONSTRAINT; Schema: radius; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY radiusacct
    ADD CONSTRAINT radiusacct_pkey PRIMARY KEY (radacctid);


--
-- Name: radiuslog_pkey; Type: CONSTRAINT; Schema: radius; Owner: nav; Tablespace: 
--

ALTER TABLE ONLY radiuslog
    ADD CONSTRAINT radiuslog_pkey PRIMARY KEY (id);


SET search_path = logger, pg_catalog;

--
-- Name: log_message_expiration_btree; Type: INDEX; Schema: logger; Owner: nav; Tablespace: 
--

CREATE INDEX log_message_expiration_btree ON log_message USING btree (newpriority, "time");


--
-- Name: log_message_origin_btree; Type: INDEX; Schema: logger; Owner: nav; Tablespace: 
--

CREATE INDEX log_message_origin_btree ON log_message USING btree (origin);


--
-- Name: log_message_time_btree; Type: INDEX; Schema: logger; Owner: nav; Tablespace: 
--

CREATE INDEX log_message_time_btree ON log_message USING btree ("time");


--
-- Name: log_message_type_btree; Type: INDEX; Schema: logger; Owner: nav; Tablespace: 
--

CREATE INDEX log_message_type_btree ON log_message USING btree (type);


SET search_path = manage, pg_catalog;

--
-- Name: alerthist_end_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alerthist_end_time_btree ON alerthist USING btree (end_time);


--
-- Name: alerthist_open_states_by_eventtype; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alerthist_open_states_by_eventtype ON alerthist USING btree (netboxid, eventtypeid) WHERE (end_time >= 'infinity'::timestamp without time zone);


--
-- Name: alerthist_start_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alerthist_start_time_btree ON alerthist USING btree (start_time);


--
-- Name: alerthistmsg_alerthistid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alerthistmsg_alerthistid_btree ON alerthistmsg USING btree (alerthistid);


--
-- Name: alerthistvar_alerthistid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alerthistvar_alerthistid_btree ON alerthistvar USING btree (alerthistid);


--
-- Name: alertqmsg_alertqid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alertqmsg_alertqid_btree ON alertqmsg USING btree (alertqid);


--
-- Name: alertqvar_alertqid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX alertqvar_alertqid_btree ON alertqvar USING btree (alertqid);


--
-- Name: arp_end_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_end_time_btree ON arp USING btree (end_time);


--
-- Name: arp_ip_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_ip_btree ON arp USING btree (ip);


--
-- Name: arp_mac_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_mac_btree ON arp USING btree (mac);


--
-- Name: arp_netboxid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_netboxid_btree ON arp USING btree (netboxid);


--
-- Name: arp_prefixid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_prefixid_btree ON arp USING btree (prefixid);


--
-- Name: arp_start_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX arp_start_time_btree ON arp USING btree (start_time);


--
-- Name: cam_end_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_end_time_btree ON cam USING btree (end_time);


--
-- Name: cam_mac_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_mac_btree ON cam USING btree (mac);


--
-- Name: cam_misscnt_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_misscnt_btree ON cam USING btree (misscnt);


--
-- Name: cam_netboxid_ifindex_end_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_netboxid_ifindex_end_time_btree ON cam USING btree (netboxid, ifindex, end_time);


--
-- Name: cam_netboxid_start_time_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);


--
-- Name: cam_open_records_by_netbox; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX cam_open_records_by_netbox ON cam USING btree (netboxid) WHERE ((end_time >= 'infinity'::timestamp without time zone) OR (misscnt >= 0));


--
-- Name: eventq_target_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX eventq_target_btree ON eventq USING btree (target);


--
-- Name: eventqvar_eventqid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX eventqvar_eventqid_btree ON eventqvar USING btree (eventqid);


--
-- Name: gwportprefix_interfaceid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX gwportprefix_interfaceid_btree ON gwportprefix USING btree (interfaceid);


--
-- Name: gwportprefix_prefixid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX gwportprefix_prefixid_btree ON gwportprefix USING btree (prefixid);


--
-- Name: interface_stack_higher; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX interface_stack_higher ON interface_stack USING btree (higher);


--
-- Name: interface_stack_lower; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX interface_stack_lower ON interface_stack USING btree (lower);


--
-- Name: interface_to_interfaceid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX interface_to_interfaceid_btree ON interface USING btree (to_interfaceid);


--
-- Name: ipdevpoll_job_log_netboxjob_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX ipdevpoll_job_log_netboxjob_btree ON ipdevpoll_job_log USING btree (netboxid, job_name);


--
-- Name: netbios_ip; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX netbios_ip ON netbios USING btree (ip);


--
-- Name: netboxsnmpoid_snmpoidid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX netboxsnmpoid_snmpoidid_btree ON netboxsnmpoid USING btree (snmpoidid);


--
-- Name: prefix_vlanid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX prefix_vlanid_btree ON prefix USING btree (vlanid);


--
-- Name: rrd_datasource_rrd_fileid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX rrd_datasource_rrd_fileid_btree ON rrd_datasource USING btree (rrd_fileid);


--
-- Name: rrd_file_value; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX rrd_file_value ON rrd_file USING btree (value);


--
-- Name: swportvlan_interfaceid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX swportvlan_interfaceid_btree ON swportvlan USING btree (interfaceid);


--
-- Name: swportvlan_vlanid_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX swportvlan_vlanid_btree ON swportvlan USING btree (vlanid);


--
-- Name: vlan_vlan_btree; Type: INDEX; Schema: manage; Owner: nav; Tablespace: 
--

CREATE INDEX vlan_vlan_btree ON vlan USING btree (vlan);


SET search_path = profiles, pg_catalog;

--
-- Name: account_idx; Type: INDEX; Schema: profiles; Owner: nav; Tablespace: 
--

CREATE INDEX account_idx ON account USING btree (login);


SET search_path = radius, pg_catalog;

--
-- Name: radiusacct_active_user_idx; Type: INDEX; Schema: radius; Owner: nav; Tablespace: 
--

CREATE INDEX radiusacct_active_user_idx ON radiusacct USING btree (username) WHERE (acctstoptime IS NULL);


--
-- Name: radiusacct_start_user_index; Type: INDEX; Schema: radius; Owner: nav; Tablespace: 
--

CREATE INDEX radiusacct_start_user_index ON radiusacct USING btree (acctstarttime, lower((username)::text));


--
-- Name: radiusacct_stop_user_index; Type: INDEX; Schema: radius; Owner: nav; Tablespace: 
--

CREATE INDEX radiusacct_stop_user_index ON radiusacct USING btree (acctstoptime, lower((username)::text));


--
-- Name: radiuslog_time_index; Type: INDEX; Schema: radius; Owner: nav; Tablespace: 
--

CREATE INDEX radiuslog_time_index ON radiuslog USING btree ("time");


--
-- Name: radiuslog_username_index; Type: INDEX; Schema: radius; Owner: nav; Tablespace: 
--

CREATE INDEX radiuslog_username_index ON radiuslog USING btree (lower((username)::text));


SET search_path = manage, pg_catalog;

--
-- Name: close_alerthist_modules; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE close_alerthist_modules AS ON DELETE TO module DO UPDATE alerthist SET end_time = now() WHERE ((((alerthist.eventtypeid)::text = ANY ((ARRAY['moduleState'::character varying, 'linkState'::character varying])::text[])) AND (alerthist.end_time = 'infinity'::timestamp without time zone)) AND (alerthist.deviceid = old.deviceid));


--
-- Name: close_alerthist_netboxes; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE close_alerthist_netboxes AS ON DELETE TO netbox DO UPDATE alerthist SET end_time = now() WHERE ((alerthist.netboxid = old.netboxid) AND (alerthist.end_time = 'infinity'::timestamp without time zone));


--
-- Name: close_alerthist_services; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE close_alerthist_services AS ON DELETE TO service DO UPDATE alerthist SET end_time = now() WHERE ((((alerthist.eventtypeid)::text = 'serviceState'::text) AND (alerthist.end_time = 'infinity'::timestamp without time zone)) AND ((alerthist.subid)::text = (old.serviceid)::text));


--
-- Name: close_arp_prefices; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE close_arp_prefices AS ON DELETE TO prefix DO UPDATE arp SET end_time = now(), prefixid = NULL::integer WHERE ((arp.prefixid = old.prefixid) AND (arp.end_time = 'infinity'::timestamp without time zone));


--
-- Name: eventq_notify; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE eventq_notify AS ON INSERT TO eventq DO NOTIFY new_event;


--
-- Name: netbox_close_arp; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE netbox_close_arp AS ON DELETE TO netbox DO UPDATE arp SET end_time = now() WHERE ((arp.netboxid = old.netboxid) AND (arp.end_time = 'infinity'::timestamp without time zone));


--
-- Name: netbox_close_cam; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE netbox_close_cam AS ON DELETE TO netbox DO UPDATE cam SET end_time = now() WHERE ((cam.netboxid = old.netboxid) AND (cam.end_time = 'infinity'::timestamp without time zone));


--
-- Name: netbox_status_close_arp; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE netbox_status_close_arp AS ON UPDATE TO netbox WHERE (new.up = 'n'::bpchar) DO UPDATE arp SET end_time = now() WHERE ((arp.netboxid = old.netboxid) AND (arp.end_time = 'infinity'::timestamp without time zone));


--
-- Name: prefix_on_delete_do_clean_rrd_file; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE prefix_on_delete_do_clean_rrd_file AS ON DELETE TO prefix DO DELETE FROM rrd_file WHERE ((((rrd_file.category)::text = 'activeip'::text) AND ((rrd_file.key)::text = 'prefix'::text)) AND ((rrd_file.value)::integer = old.prefixid));


--
-- Name: reprofile_netboxes_on_snmpoid_insert; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE reprofile_netboxes_on_snmpoid_insert AS ON INSERT TO snmpoid DO UPDATE netbox SET uptodate = false;


--
-- Name: reprofile_netboxes_on_snmpoid_update; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE reprofile_netboxes_on_snmpoid_update AS ON UPDATE TO snmpoid DO UPDATE netbox SET uptodate = false;


--
-- Name: rrdfile_deleter; Type: RULE; Schema: manage; Owner: nav
--

CREATE RULE rrdfile_deleter AS ON DELETE TO service DO DELETE FROM rrd_file WHERE (((rrd_file.key)::text = 'serviceid'::text) AND ((rrd_file.value)::text = (old.serviceid)::text));


--
-- Name: alerthist_subid_fix; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER alerthist_subid_fix BEFORE INSERT OR UPDATE ON alerthist FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();


--
-- Name: alertq_subid_fix; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER alertq_subid_fix BEFORE INSERT OR UPDATE ON alertq FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();


--
-- Name: eventq_subid_fix; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER eventq_subid_fix BEFORE INSERT OR UPDATE ON eventq FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();


--
-- Name: trig_close_snmpagentstates_on_community_clear; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_close_snmpagentstates_on_community_clear AFTER UPDATE ON netbox FOR EACH ROW EXECUTE PROCEDURE close_snmpagentstates_on_community_clear();


--
-- Name: trig_close_thresholdstate_on_threshold_delete; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_close_thresholdstate_on_threshold_delete AFTER DELETE OR UPDATE ON rrd_datasource FOR EACH ROW EXECUTE PROCEDURE close_thresholdstate_on_threshold_delete();


--
-- Name: trig_close_thresholdstate_on_thresholdrule_delete; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_close_thresholdstate_on_thresholdrule_delete AFTER DELETE OR UPDATE ON thresholdrule FOR EACH ROW EXECUTE PROCEDURE close_thresholdstate_on_thresholdrule_delete();


--
-- Name: trig_message_replace; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_message_replace AFTER INSERT OR UPDATE ON message FOR EACH ROW EXECUTE PROCEDURE message_replace();


--
-- Name: trig_module_delete_prune_devices; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_module_delete_prune_devices AFTER DELETE ON module FOR EACH STATEMENT EXECUTE PROCEDURE remove_floating_devices();


--
-- Name: trig_netbox_delete_prune_devices; Type: TRIGGER; Schema: manage; Owner: nav
--

CREATE TRIGGER trig_netbox_delete_prune_devices AFTER DELETE ON netbox FOR EACH STATEMENT EXECUTE PROCEDURE remove_floating_devices();


SET search_path = profiles, pg_catalog;

--
-- Name: add_default_navlets_on_account_create; Type: TRIGGER; Schema: profiles; Owner: nav
--

CREATE TRIGGER add_default_navlets_on_account_create AFTER INSERT ON account FOR EACH ROW EXECUTE PROCEDURE manage.insert_default_navlets_for_new_users();


--
-- Name: group_membership; Type: TRIGGER; Schema: profiles; Owner: nav
--

CREATE TRIGGER group_membership AFTER INSERT ON account FOR EACH ROW EXECUTE PROCEDURE group_membership();


SET search_path = arnold, pg_catalog;

--
-- Name: block_quarantineid_fkey; Type: FK CONSTRAINT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY block
    ADD CONSTRAINT block_quarantineid_fkey FOREIGN KEY (quarantineid) REFERENCES quarantine_vlans(quarantineid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: block_reasonid_fkey; Type: FK CONSTRAINT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY block
    ADD CONSTRAINT block_reasonid_fkey FOREIGN KEY (reasonid) REFERENCES blocked_reason(blocked_reasonid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: event_blocked_reasonid_fkey; Type: FK CONSTRAINT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY event
    ADD CONSTRAINT event_blocked_reasonid_fkey FOREIGN KEY (blocked_reasonid) REFERENCES blocked_reason(blocked_reasonid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: event_identityid_fkey; Type: FK CONSTRAINT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY event
    ADD CONSTRAINT event_identityid_fkey FOREIGN KEY (identityid) REFERENCES identity(identityid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: identity_blocked_reasonid_fkey; Type: FK CONSTRAINT; Schema: arnold; Owner: nav
--

ALTER TABLE ONLY identity
    ADD CONSTRAINT identity_blocked_reasonid_fkey FOREIGN KEY (blocked_reasonid) REFERENCES blocked_reason(blocked_reasonid) ON UPDATE CASCADE ON DELETE SET NULL;


SET search_path = logger, pg_catalog;

--
-- Name: log_message_newpriority_fkey; Type: FK CONSTRAINT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message
    ADD CONSTRAINT log_message_newpriority_fkey FOREIGN KEY (newpriority) REFERENCES priority(priority) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: log_message_origin_fkey; Type: FK CONSTRAINT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message
    ADD CONSTRAINT log_message_origin_fkey FOREIGN KEY (origin) REFERENCES origin(origin) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: log_message_type_fkey; Type: FK CONSTRAINT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message
    ADD CONSTRAINT log_message_type_fkey FOREIGN KEY (type) REFERENCES log_message_type(type) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: log_message_type_priority_fkey; Type: FK CONSTRAINT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY log_message_type
    ADD CONSTRAINT log_message_type_priority_fkey FOREIGN KEY (priority) REFERENCES priority(priority) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: origin_category_fkey; Type: FK CONSTRAINT; Schema: logger; Owner: nav
--

ALTER TABLE ONLY origin
    ADD CONSTRAINT origin_category_fkey FOREIGN KEY (category) REFERENCES category(category) ON UPDATE CASCADE ON DELETE SET NULL;


SET search_path = manage, pg_catalog;

--
-- Name: adjacency_candidate_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: adjacency_candidate_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: adjacency_candidate_to_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_to_interfaceid_fkey FOREIGN KEY (to_interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: adjacency_candidate_to_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY adjacency_candidate
    ADD CONSTRAINT adjacency_candidate_to_netboxid_fkey FOREIGN KEY (to_netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthist_alerttypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_alerttypeid_fkey FOREIGN KEY (alerttypeid) REFERENCES alerttype(alerttypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthist_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthist_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES eventtype(eventtypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthist_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: alerthist_source_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist
    ADD CONSTRAINT alerthist_source_fkey FOREIGN KEY (source) REFERENCES subsystem(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthistmsg_alerthistid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthistmsg
    ADD CONSTRAINT alerthistmsg_alerthistid_fkey FOREIGN KEY (alerthistid) REFERENCES alerthist(alerthistid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthistory_ack_alert; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist_ack
    ADD CONSTRAINT alerthistory_ack_alert FOREIGN KEY (alert_id) REFERENCES alerthist(alerthistid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthistory_ack_user; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthist_ack
    ADD CONSTRAINT alerthistory_ack_user FOREIGN KEY (account_id) REFERENCES profiles.account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerthistvar_alerthistid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerthistvar
    ADD CONSTRAINT alerthistvar_alerthistid_fkey FOREIGN KEY (alerthistid) REFERENCES alerthist(alerthistid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertq_alerthistid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_alerthistid_fkey FOREIGN KEY (alerthistid) REFERENCES alerthist(alerthistid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: alertq_alerttypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_alerttypeid_fkey FOREIGN KEY (alerttypeid) REFERENCES alerttype(alerttypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertq_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertq_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES eventtype(eventtypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertq_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertq_source_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertq
    ADD CONSTRAINT alertq_source_fkey FOREIGN KEY (source) REFERENCES subsystem(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertqmsg_alertqid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertqmsg
    ADD CONSTRAINT alertqmsg_alertqid_fkey FOREIGN KEY (alertqid) REFERENCES alertq(alertqid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertqvar_alertqid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alertqvar
    ADD CONSTRAINT alertqvar_alertqid_fkey FOREIGN KEY (alertqid) REFERENCES alertq(alertqid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alerttype_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY alerttype
    ADD CONSTRAINT alerttype_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES eventtype(eventtypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: apitoken_client_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY apitoken
    ADD CONSTRAINT apitoken_client_fkey FOREIGN KEY (client) REFERENCES profiles.account(id);


--
-- Name: arp_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY arp
    ADD CONSTRAINT arp_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: arp_prefixid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY arp
    ADD CONSTRAINT arp_prefixid_fkey FOREIGN KEY (prefixid) REFERENCES prefix(prefixid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: cabling_roomid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY cabling
    ADD CONSTRAINT cabling_roomid_fkey FOREIGN KEY (roomid) REFERENCES room(roomid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: cam_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY cam
    ADD CONSTRAINT cam_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: eventq_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: eventq_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES eventtype(eventtypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: eventq_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: eventq_source_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_source_fkey FOREIGN KEY (source) REFERENCES subsystem(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: eventq_target_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventq
    ADD CONSTRAINT eventq_target_fkey FOREIGN KEY (target) REFERENCES subsystem(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: eventqvar_eventqid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY eventqvar
    ADD CONSTRAINT eventqvar_eventqid_fkey FOREIGN KEY (eventqid) REFERENCES eventq(eventqid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gwportprefix_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY gwportprefix
    ADD CONSTRAINT gwportprefix_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gwportprefix_prefixid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY gwportprefix
    ADD CONSTRAINT gwportprefix_prefixid_fkey FOREIGN KEY (prefixid) REFERENCES prefix(prefixid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: image_roomid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY image
    ADD CONSTRAINT image_roomid_fkey FOREIGN KEY (roomid) REFERENCES room(roomid);


--
-- Name: image_uploader_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY image
    ADD CONSTRAINT image_uploader_fkey FOREIGN KEY (uploader) REFERENCES profiles.account(id);


--
-- Name: interface_moduleid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_moduleid_fkey FOREIGN KEY (moduleid) REFERENCES module(moduleid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: interface_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: interface_stack_higher_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface_stack
    ADD CONSTRAINT interface_stack_higher_fkey FOREIGN KEY (higher) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: interface_stack_lower_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface_stack
    ADD CONSTRAINT interface_stack_lower_fkey FOREIGN KEY (lower) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: interface_to_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_to_interfaceid_fkey FOREIGN KEY (to_interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: interface_to_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_to_netboxid_fkey FOREIGN KEY (to_netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: ipdevpoll_job_log_netbox_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY ipdevpoll_job_log
    ADD CONSTRAINT ipdevpoll_job_log_netbox_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: macwatch_match_cam_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY macwatch_match
    ADD CONSTRAINT macwatch_match_cam_fkey FOREIGN KEY (cam) REFERENCES cam(camid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: macwatch_match_macwatch_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY macwatch_match
    ADD CONSTRAINT macwatch_match_macwatch_fkey FOREIGN KEY (macwatch) REFERENCES macwatch(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: macwatch_userid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY macwatch
    ADD CONSTRAINT macwatch_userid_fkey FOREIGN KEY (userid) REFERENCES profiles.account(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: maint_component_maint_taskid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY maint_component
    ADD CONSTRAINT maint_component_maint_taskid_fkey FOREIGN KEY (maint_taskid) REFERENCES maint_task(maint_taskid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: mem_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY mem
    ADD CONSTRAINT mem_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: message_replaced_by_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message
    ADD CONSTRAINT message_replaced_by_fkey FOREIGN KEY (replaced_by) REFERENCES message(messageid);


--
-- Name: message_replaces_message_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message
    ADD CONSTRAINT message_replaces_message_fkey FOREIGN KEY (replaces_message) REFERENCES message(messageid);


--
-- Name: message_to_maint_task_maint_taskid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message_to_maint_task
    ADD CONSTRAINT message_to_maint_task_maint_taskid_fkey FOREIGN KEY (maint_taskid) REFERENCES maint_task(maint_taskid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: message_to_maint_task_messageid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY message_to_maint_task
    ADD CONSTRAINT message_to_maint_task_messageid_fkey FOREIGN KEY (messageid) REFERENCES message(messageid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: module_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY module
    ADD CONSTRAINT module_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: module_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY module
    ADD CONSTRAINT module_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netbox_catid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_catid_fkey FOREIGN KEY (catid) REFERENCES cat(catid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netbox_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netbox_orgid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_orgid_fkey FOREIGN KEY (orgid) REFERENCES org(orgid) ON UPDATE CASCADE;


--
-- Name: netbox_roomid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_roomid_fkey FOREIGN KEY (roomid) REFERENCES room(roomid) ON UPDATE CASCADE;


--
-- Name: netbox_typeid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox
    ADD CONSTRAINT netbox_typeid_fkey FOREIGN KEY (typeid) REFERENCES type(typeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netbox_vtpvlan_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netbox_vtpvlan
    ADD CONSTRAINT netbox_vtpvlan_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netboxcategory_category_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxcategory
    ADD CONSTRAINT netboxcategory_category_fkey FOREIGN KEY (category) REFERENCES netboxgroup(netboxgroupid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netboxcategory_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxcategory
    ADD CONSTRAINT netboxcategory_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netboxinfo_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxinfo
    ADD CONSTRAINT netboxinfo_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netboxsnmpoid_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxsnmpoid
    ADD CONSTRAINT netboxsnmpoid_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netboxsnmpoid_snmpoidid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY netboxsnmpoid
    ADD CONSTRAINT netboxsnmpoid_snmpoidid_fkey FOREIGN KEY (snmpoidid) REFERENCES snmpoid(snmpoidid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: org_parent_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY org
    ADD CONSTRAINT org_parent_fkey FOREIGN KEY (parent) REFERENCES org(orgid) ON UPDATE CASCADE;


--
-- Name: patch_cablingid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY patch
    ADD CONSTRAINT patch_cablingid_fkey FOREIGN KEY (cablingid) REFERENCES cabling(cablingid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: patch_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY patch
    ADD CONSTRAINT patch_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: powersupply_or_fan_deviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY powersupply_or_fan
    ADD CONSTRAINT powersupply_or_fan_deviceid_fkey FOREIGN KEY (deviceid) REFERENCES device(deviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: powersupply_or_fan_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY powersupply_or_fan
    ADD CONSTRAINT powersupply_or_fan_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: prefix_vlanid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY prefix
    ADD CONSTRAINT prefix_vlanid_fkey FOREIGN KEY (vlanid) REFERENCES vlan(vlanid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: room_locationid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY room
    ADD CONSTRAINT room_locationid_fkey FOREIGN KEY (locationid) REFERENCES location(locationid);


--
-- Name: rproto_attr_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rproto_attr
    ADD CONSTRAINT rproto_attr_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: rrd_datasource_rrd_fileid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rrd_datasource
    ADD CONSTRAINT rrd_datasource_rrd_fileid_fkey FOREIGN KEY (rrd_fileid) REFERENCES rrd_file(rrd_fileid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: rrd_file_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rrd_file
    ADD CONSTRAINT rrd_file_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: rrd_file_subsystem_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY rrd_file
    ADD CONSTRAINT rrd_file_subsystem_fkey FOREIGN KEY (subsystem) REFERENCES subsystem(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sensor_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY sensor
    ADD CONSTRAINT sensor_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: service_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY service
    ADD CONSTRAINT service_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: serviceproperty_serviceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY serviceproperty
    ADD CONSTRAINT serviceproperty_serviceid_fkey FOREIGN KEY (serviceid) REFERENCES service(serviceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: swportallowedvlan_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportallowedvlan
    ADD CONSTRAINT swportallowedvlan_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: swportblocked_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportblocked
    ADD CONSTRAINT swportblocked_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: swportvlan_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportvlan
    ADD CONSTRAINT swportvlan_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: swportvlan_vlanid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY swportvlan
    ADD CONSTRAINT swportvlan_vlanid_fkey FOREIGN KEY (vlanid) REFERENCES vlan(vlanid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: thresholdrule_creator_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY thresholdrule
    ADD CONSTRAINT thresholdrule_creator_fkey FOREIGN KEY (creator_id) REFERENCES profiles.account(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: type_vendorid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY type
    ADD CONSTRAINT type_vendorid_fkey FOREIGN KEY (vendorid) REFERENCES vendor(vendorid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: unrecognized_neighbor_interfaceid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY unrecognized_neighbor
    ADD CONSTRAINT unrecognized_neighbor_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: unrecognized_neighbor_netboxid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY unrecognized_neighbor
    ADD CONSTRAINT unrecognized_neighbor_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vlan_nettype_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_nettype_fkey FOREIGN KEY (nettype) REFERENCES nettype(nettypeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vlan_orgid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_orgid_fkey FOREIGN KEY (orgid) REFERENCES org(orgid);


--
-- Name: vlan_usageid_fkey; Type: FK CONSTRAINT; Schema: manage; Owner: nav
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_usageid_fkey FOREIGN KEY (usageid) REFERENCES usage(usageid);


SET search_path = profiles, pg_catalog;

--
-- Name: account_navlet_account_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY account_navlet
    ADD CONSTRAINT account_navlet_account_fkey FOREIGN KEY (account) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountalertqueue_account_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountalertqueue
    ADD CONSTRAINT accountalertqueue_account_id_fkey FOREIGN KEY (account_id) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountalertqueue_alert_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountalertqueue
    ADD CONSTRAINT accountalertqueue_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES manage.alertq(alertqid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountalertqueue_subscription_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountalertqueue
    ADD CONSTRAINT accountalertqueue_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES alertsubscription(id);


--
-- Name: accountgroup_accounts_account_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroup_accounts
    ADD CONSTRAINT accountgroup_accounts_account_id_fkey FOREIGN KEY (account_id) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountgroup_accounts_accountgroup_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroup_accounts
    ADD CONSTRAINT accountgroup_accounts_accountgroup_id_fkey FOREIGN KEY (accountgroup_id) REFERENCES accountgroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountgroupprivilege_accountgroupid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroupprivilege
    ADD CONSTRAINT accountgroupprivilege_accountgroupid_fkey FOREIGN KEY (accountgroupid) REFERENCES accountgroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountgroupprivilege_privilegeid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountgroupprivilege
    ADD CONSTRAINT accountgroupprivilege_privilegeid_fkey FOREIGN KEY (privilegeid) REFERENCES privilege(privilegeid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountorg_account_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountorg
    ADD CONSTRAINT accountorg_account_id_fkey FOREIGN KEY (account_id) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountorg_organization_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountorg
    ADD CONSTRAINT accountorg_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES manage.org(orgid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accountproperty_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accountproperty
    ADD CONSTRAINT accountproperty_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: accounttool_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY accounttool
    ADD CONSTRAINT accounttool_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertaddress_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertaddress
    ADD CONSTRAINT alertaddress_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertaddress_type_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertaddress
    ADD CONSTRAINT alertaddress_type_fkey FOREIGN KEY (type) REFERENCES alertsender(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertpreference_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertpreference
    ADD CONSTRAINT alertpreference_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertpreference_activeprofile_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertpreference
    ADD CONSTRAINT alertpreference_activeprofile_fkey FOREIGN KEY (activeprofile) REFERENCES alertprofile(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: alertprofile_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertprofile
    ADD CONSTRAINT alertprofile_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertsubscription_alert_address_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertsubscription
    ADD CONSTRAINT alertsubscription_alert_address_id_fkey FOREIGN KEY (alert_address_id) REFERENCES alertaddress(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertsubscription_filter_group_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertsubscription
    ADD CONSTRAINT alertsubscription_filter_group_id_fkey FOREIGN KEY (filter_group_id) REFERENCES filtergroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: alertsubscription_time_period_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY alertsubscription
    ADD CONSTRAINT alertsubscription_time_period_id_fkey FOREIGN KEY (time_period_id) REFERENCES timeperiod(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: expression_filter_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY expression
    ADD CONSTRAINT expression_filter_id_fkey FOREIGN KEY (filter_id) REFERENCES filter(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: expression_match_field_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY expression
    ADD CONSTRAINT expression_match_field_id_fkey FOREIGN KEY (match_field_id) REFERENCES matchfield(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filter_owner_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filter
    ADD CONSTRAINT filter_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES account(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: filtergroup_group_permission_accountgroup_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroup_group_permission
    ADD CONSTRAINT filtergroup_group_permission_accountgroup_id_fkey FOREIGN KEY (accountgroup_id) REFERENCES accountgroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filtergroup_group_permission_filtergroup_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroup_group_permission
    ADD CONSTRAINT filtergroup_group_permission_filtergroup_id_fkey FOREIGN KEY (filtergroup_id) REFERENCES filtergroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filtergroup_owner_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroup
    ADD CONSTRAINT filtergroup_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filtergroupcontent_filter_group_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroupcontent
    ADD CONSTRAINT filtergroupcontent_filter_group_id_fkey FOREIGN KEY (filter_group_id) REFERENCES filtergroup(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filtergroupcontent_filter_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY filtergroupcontent
    ADD CONSTRAINT filtergroupcontent_filter_id_fkey FOREIGN KEY (filter_id) REFERENCES filter(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: navbarlink_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY navbarlink
    ADD CONSTRAINT navbarlink_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmap_view_defaultview_ownerid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_defaultview
    ADD CONSTRAINT netmap_view_defaultview_ownerid_fkey FOREIGN KEY (ownerid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmap_view_defaultview_viewid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_defaultview
    ADD CONSTRAINT netmap_view_defaultview_viewid_fkey FOREIGN KEY (viewid) REFERENCES netmap_view(viewid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmap_view_nodeposition_netboxid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_nodeposition
    ADD CONSTRAINT netmap_view_nodeposition_netboxid_fkey FOREIGN KEY (netboxid) REFERENCES manage.netbox(netboxid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmap_view_nodeposition_viewid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_nodeposition
    ADD CONSTRAINT netmap_view_nodeposition_viewid_fkey FOREIGN KEY (viewid) REFERENCES netmap_view(viewid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmap_view_owner_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view
    ADD CONSTRAINT netmap_view_owner_fkey FOREIGN KEY (owner) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmapview_category_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_categories
    ADD CONSTRAINT netmapview_category_fkey FOREIGN KEY (catid) REFERENCES manage.cat(catid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: netmapview_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY netmap_view_categories
    ADD CONSTRAINT netmapview_fkey FOREIGN KEY (viewid) REFERENCES netmap_view(viewid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: operator_match_field_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY operator
    ADD CONSTRAINT operator_match_field_id_fkey FOREIGN KEY (match_field_id) REFERENCES matchfield(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: smsq_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY smsq
    ADD CONSTRAINT smsq_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: statuspreference_accountid_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference
    ADD CONSTRAINT statuspreference_accountid_fkey FOREIGN KEY (accountid) REFERENCES account(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: statuspreference_category_category_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_category
    ADD CONSTRAINT statuspreference_category_category_id_fkey FOREIGN KEY (category_id) REFERENCES manage.cat(catid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: statuspreference_category_statuspreference_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_category
    ADD CONSTRAINT statuspreference_category_statuspreference_id_fkey FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: statuspreference_organization_organization_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_organization
    ADD CONSTRAINT statuspreference_organization_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES manage.org(orgid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: statuspreference_organization_statuspreference_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY statuspreference_organization
    ADD CONSTRAINT statuspreference_organization_statuspreference_id_fkey FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: timeperiod_alert_profile_id_fkey; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY timeperiod
    ADD CONSTRAINT timeperiod_alert_profile_id_fkey FOREIGN KEY (alert_profile_id) REFERENCES alertprofile(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

