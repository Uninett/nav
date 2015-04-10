CREATE OR REPLACE FUNCTION never_use_null_subid()
RETURNS trigger AS $$
  BEGIN
    NEW.subid = COALESCE(NEW.subid, '');
    RETURN NEW;
  END;
$$ language plpgsql;

CREATE TRIGGER eventq_subid_fix BEFORE INSERT OR UPDATE ON eventq
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();

CREATE TRIGGER alertq_subid_fix BEFORE INSERT OR UPDATE ON alertq
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();

CREATE TRIGGER alerthist_subid_fix BEFORE INSERT OR UPDATE ON alerthist
    FOR EACH ROW EXECUTE PROCEDURE never_use_null_subid();
