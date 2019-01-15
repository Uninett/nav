-- Django database-backed sessions are now being used by NAV.
CREATE TABLE profiles.django_session (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" timestamp with time zone NOT NULL
);
