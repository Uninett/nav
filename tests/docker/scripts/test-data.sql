-- -*- coding: utf-8 -*-
\set ON_ERROR_STOP on

-- Add non-ASCII chars to the admin user's login name to test encoding
-- compliance for all pages
UPDATE account SET name = 'Administrator ÆØÅ' WHERE login = 'admin';

-- Add some non-ASCII test data to reveal more potential problems during
-- the shift to Python 3
INSERT INTO location (locationid) VALUES ('bø');
INSERT INTO room (roomid, locationid) VALUES ('bø-123', 'bø');
