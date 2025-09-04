BEGIN;

CREATE TABLE profiles.social_auth_association (
    id bigint NOT NULL,
    server_url character varying(255) NOT NULL,
    handle character varying(255) NOT NULL,
    secret character varying(255) NOT NULL,
    issued integer NOT NULL,
    lifetime integer NOT NULL,
    assoc_type character varying(64) NOT NULL
);

ALTER TABLE profiles.social_auth_association OWNER TO nav;

--
-- Name: social_auth_association_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE profiles.social_auth_association_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE profiles.social_auth_association_id_seq OWNER TO nav;

--
-- Name: social_auth_association_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE profiles.social_auth_association_id_seq OWNED BY profiles.social_auth_association.id;

--
-- Name: social_auth_code; Type: TABLE; Schema: profiles; Owner: nav
--

CREATE TABLE profiles.social_auth_code (
    id bigint NOT NULL,
    email character varying(254) NOT NULL,
    code character varying(32) NOT NULL,
    verified boolean NOT NULL,
    "timestamp" timestamp with time zone NOT NULL
);

ALTER TABLE profiles.social_auth_code OWNER TO nav;

--
-- Name: social_auth_code_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE profiles.social_auth_code_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE profiles.social_auth_code_id_seq OWNER TO nav;

--
-- Name: social_auth_code_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE profiles.social_auth_code_id_seq OWNED BY profiles.social_auth_code.id;

--
-- Name: social_auth_nonce; Type: TABLE; Schema: profiles; Owner: nav
--
CREATE TABLE profiles.social_auth_nonce (
    id bigint NOT NULL,
    server_url character varying(255) NOT NULL,
    "timestamp" integer NOT NULL,
    salt character varying(65) NOT NULL
);

ALTER TABLE profiles.social_auth_nonce OWNER TO nav;

--
-- Name: social_auth_nonce_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE profiles.social_auth_nonce_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE profiles.social_auth_nonce_id_seq OWNER TO nav;

--
-- Name: social_auth_nonce_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE profiles.social_auth_nonce_id_seq OWNED BY profiles.social_auth_nonce.id;

--
-- Name: social_auth_partial; Type: TABLE; Schema: profiles; Owner: nav
--

CREATE TABLE profiles.social_auth_partial (
    id bigint NOT NULL,
    token character varying(32) NOT NULL,
    next_step smallint NOT NULL,
    backend character varying(32) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    data jsonb NOT NULL,
    CONSTRAINT social_auth_partial_next_step_check CHECK ((next_step >= 0))
);

ALTER TABLE profiles.social_auth_partial OWNER TO nav;

--
-- Name: social_auth_partial_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE profiles.social_auth_partial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE profiles.social_auth_partial_id_seq OWNER TO nav;

--
-- Name: social_auth_partial_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE profiles.social_auth_partial_id_seq OWNED BY profiles.social_auth_partial.id;

--
-- Name: social_auth_usersocialauth; Type: TABLE; Schema: profiles; Owner: nav
--

CREATE TABLE profiles.social_auth_usersocialauth (
    id bigint NOT NULL,
    provider character varying(32) NOT NULL,
    uid character varying(255) NOT NULL,
    user_id integer NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    extra_data jsonb NOT NULL
);

ALTER TABLE profiles.social_auth_usersocialauth OWNER TO nav;

--
-- Name: social_auth_usersocialauth_id_seq; Type: SEQUENCE; Schema: profiles; Owner: nav
--

CREATE SEQUENCE profiles.social_auth_usersocialauth_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE profiles.social_auth_usersocialauth_id_seq OWNER TO nav;

--
-- Name: social_auth_usersocialauth_id_seq; Type: SEQUENCE OWNED BY; Schema: profiles; Owner: nav
--

ALTER SEQUENCE profiles.social_auth_usersocialauth_id_seq OWNED BY profiles.social_auth_usersocialauth.id;

--
-- Name: social_auth_association id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_association ALTER COLUMN id SET DEFAULT nextval('profiles.social_auth_association_id_seq'::regclass);

--
-- Name: social_auth_code id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_code ALTER COLUMN id SET DEFAULT nextval('profiles.social_auth_code_id_seq'::regclass);


--
-- Name: social_auth_nonce id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_nonce ALTER COLUMN id SET DEFAULT nextval('profiles.social_auth_nonce_id_seq'::regclass);

--
-- Name: social_auth_partial id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_partial ALTER COLUMN id SET DEFAULT nextval('profiles.social_auth_partial_id_seq'::regclass);

--
-- Name: social_auth_usersocialauth id; Type: DEFAULT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_usersocialauth ALTER COLUMN id SET DEFAULT nextval('profiles.social_auth_usersocialauth_id_seq'::regclass);

-- Set constraints

--
-- Name: social_auth_association social_auth_association_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_association
    ADD CONSTRAINT social_auth_association_pkey PRIMARY KEY (id);

--
-- Name: social_auth_association social_auth_association_server_url_handle_078befa2_uniq; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_association
    ADD CONSTRAINT social_auth_association_server_url_handle_078befa2_uniq UNIQUE (server_url, handle);

--
-- Name: social_auth_code social_auth_code_email_code_801b2d02_uniq; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_code
    ADD CONSTRAINT social_auth_code_email_code_801b2d02_uniq UNIQUE (email, code);

--
-- Name: social_auth_code social_auth_code_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav
--
ALTER TABLE ONLY profiles.social_auth_code
    ADD CONSTRAINT social_auth_code_pkey PRIMARY KEY (id);

--
-- Name: social_auth_nonce social_auth_nonce_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_nonce
    ADD CONSTRAINT social_auth_nonce_pkey PRIMARY KEY (id);

--
-- Name: social_auth_nonce social_auth_nonce_server_url_timestamp_salt_f6284463_uniq; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_nonce
    ADD CONSTRAINT social_auth_nonce_server_url_timestamp_salt_f6284463_uniq UNIQUE (server_url, "timestamp", salt);

--
-- Name: social_auth_partial social_auth_partial_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_partial
    ADD CONSTRAINT social_auth_partial_pkey PRIMARY KEY (id);

--
-- Name: social_auth_usersocialauth social_auth_usersocialauth_pkey; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_usersocialauth
    ADD CONSTRAINT social_auth_usersocialauth_pkey PRIMARY KEY (id);

--
-- Name: social_auth_usersocialauth social_auth_usersocialauth_provider_uid_e6b5e668_uniq; Type: CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_usersocialauth
    ADD CONSTRAINT social_auth_usersocialauth_provider_uid_e6b5e668_uniq UNIQUE (provider, uid);

-- Create indexes

--
-- Name: social_auth_code_code_a2393167; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_code_code_a2393167 ON profiles.social_auth_code USING btree (code);
--
-- Name: social_auth_code_code_a2393167_like; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_code_code_a2393167_like ON profiles.social_auth_code USING btree (code varchar_pattern_ops);

--
-- Name: social_auth_code_timestamp_176b341f; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_code_timestamp_176b341f ON profiles.social_auth_code USING btree ("timestamp");

--
-- Name: social_auth_partial_timestamp_50f2119f; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_partial_timestamp_50f2119f ON profiles.social_auth_partial USING btree ("timestamp");
--
-- Name: social_auth_partial_token_3017fea3; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_partial_token_3017fea3 ON profiles.social_auth_partial USING btree (token);

--
-- Name: social_auth_partial_token_3017fea3_like; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_partial_token_3017fea3_like ON profiles.social_auth_partial USING btree (token varchar_pattern_ops);

--
-- Name: social_auth_usersocialauth_uid_796e51dc; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_usersocialauth_uid_796e51dc ON profiles.social_auth_usersocialauth USING btree (uid);

--
-- Name: social_auth_usersocialauth_uid_796e51dc_like; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_usersocialauth_uid_796e51dc_like ON profiles.social_auth_usersocialauth USING btree (uid varchar_pattern_ops);
--
-- Name: social_auth_usersocialauth_user_id_17d28448; Type: INDEX; Schema: profiles; Owner: nav
--

CREATE INDEX social_auth_usersocialauth_user_id_17d28448 ON profiles.social_auth_usersocialauth USING btree (user_id);

--
-- Name: social_auth_usersocialauth social_auth_usersoci_user_id_17d28448_fk_argus_aut; Type: FK CONSTRAINT; Schema: profiles; Owner: nav
--

ALTER TABLE ONLY profiles.social_auth_usersocialauth
    ADD CONSTRAINT social_auth_usersoci_user_id_17d28448_fk_account FOREIGN KEY (user_id) REFERENCES profiles.account(id) DEFERRABLE INITIALLY DEFERRED;

COMMIT;
