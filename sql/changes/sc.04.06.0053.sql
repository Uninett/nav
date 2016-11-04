-- Set description to be optional for Locations and set default value to be an
-- empty string as that is what is used in Django for empty char-fields
ALTER TABLE manage.location ALTER descr DROP NOT NULL,
                            ALTER descr SET DEFAULT '';
