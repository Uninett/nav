-- automatically close thresholdState when threshold rules are removed
CREATE OR REPLACE FUNCTION close_thresholdstate_on_thresholdrule_delete()
RETURNS TRIGGER AS $$
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
$$ language 'plpgsql';

CREATE TRIGGER trig_close_thresholdstate_on_thresholdrule_delete
    AFTER UPDATE OR DELETE ON manage.thresholdrule
    FOR EACH ROW
    EXECUTE PROCEDURE close_thresholdstate_on_thresholdrule_delete();

-- also close any currently open thresholdStates from old NAV versions, since
-- these cannot be evaluated any more.
UPDATE alerthist
SET end_time = NOW()
WHERE eventtypeid = 'thresholdState' AND end_time >= 'infinity';
