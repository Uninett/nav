/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.7.0 to 3.7.1.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.7.1.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.7.1.sql nav
 *
*/
BEGIN;
-- Insert schema changes here.

------------------------------------------------------------------------------
-- Simple but stupid operators for POINT data type comparisons.
-- Needed because Django will issue DISTINCT queries that require
-- ordering operators for the room.point column.
------------------------------------------------------------------------------
CREATE FUNCTION point_stupid_lt(point, point) RETURNS bool
    AS $$
BEGIN
  RETURN $1::text < $2::text;
END;
$$
    LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE FUNCTION point_stupid_gt(point, point) RETURNS bool
    AS $$
BEGIN
  RETURN $1::text > $2::text;
END;
$$
    LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE FUNCTION point_stupid_gte(point, point) RETURNS bool
    AS $$
BEGIN
  RETURN $1::text >= $2::text;
END;
$$
    LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE FUNCTION point_stupid_lte(point, point) RETURNS bool
    AS $$
BEGIN
  RETURN $1::text <= $2::text;
END;
$$
    LANGUAGE plpgsql IMMUTABLE STRICT;


CREATE OPERATOR < (
   leftarg = point, rightarg = point, procedure = point_stupid_lt,
   commutator = > , negator = >= ,
   restrict = scalarltsel, join = scalarltjoinsel
);

CREATE OPERATOR > (
   leftarg = point, rightarg = point, procedure = point_stupid_gt,
   commutator = < , negator = <= ,
   restrict = scalarltsel, join = scalarltjoinsel
);

CREATE OPERATOR <= (
   leftarg = point, rightarg = point, procedure = point_stupid_lte,
   commutator = >= , negator = > ,
   restrict = scalarltsel, join = scalarltjoinsel
);

CREATE OPERATOR >= (
   leftarg = point, rightarg = point, procedure = point_stupid_gte,
   commutator = <= , negator = < ,
   restrict = scalarltsel, join = scalarltjoinsel
);

CREATE OPERATOR = (
   leftarg = point, rightarg = point, procedure = point_eq,
   negator = <> ,
   restrict = scalarltsel, join = scalarltjoinsel
);

CREATE FUNCTION point_cmp(point, point)
    RETURNS integer
    AS $$
BEGIN
  RETURN bttextcmp($1::text, $2::text);
END
$$
    LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OPERATOR CLASS point_abs_ops
    DEFAULT FOR TYPE point USING btree AS
        OPERATOR        1       < ,
        OPERATOR        2       <= ,
        OPERATOR        3       = ,
        OPERATOR        4       >= ,
        OPERATOR        5       > ,
        FUNCTION        1       point_cmp(point, point);

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.7.1');

COMMIT;
