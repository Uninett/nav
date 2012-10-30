-- automatically close thresholdState when threshold in rrd_datasource is removed.
CREATE OR REPLACE FUNCTION close_thresholdstate_on_threshold_delete()
RETURNS TRIGGER AS E'
  BEGIN
    IF TG_OP = \'DELETE\' THEN
      UPDATE alerthist
        SET end_time = NOW()
          WHERE subid = CAST(OLD.rrd_datasourceid AS text)
            AND eventtypeid = \'thresholdState\'
              AND end_time >= \'infinity\';
    END IF;
    IF TG_OP = \'UPDATE\' THEN
        IF COALESCE(OLD.threshold, \'\') IS 
            DISTINCT FROM COALESCE(NEW.threshold, \'\')
                AND COALESCE(NEW.threshold, \'\') = \'\' THEN
            UPDATE alerthist
                SET end_time = NOW()
                    WHERE subid = CAST(NEW.rrd_datasourceid AS text)
                        AND eventtypeid = \'thresholdState\'
                            AND end_time >= \'infinity\';
        END IF;
    END IF;
    RETURN NULL;
  END;
  'language 'plpgsql';

CREATE TRIGGER trig_close_thresholdstate_on_threshold_delete
    AFTER UPDATE OR DELETE ON rrd_datasource
    FOR EACH ROW
    EXECUTE PROCEDURE close_thresholdstate_on_threshold_delete();

-- also close any currently wrongfully open threshold states
UPDATE alerthist
    SET end_time = NOW()
    FROM rrd_datasource
        WHERE eventtypeid = 'thresholdState'
            AND end_time >= 'infinity'
            AND subid NOT IN 
                (SELECT CAST(rrd_datasource.rrd_datasourceid AS text)
                    FROM rrd_datasource);

UPDATE alerthist
    SET end_time = NOW()
    FROM rrd_datasource
        WHERE eventtypeid = 'thresholdState'
            AND end_time >= 'infinity'
            AND alerthist.subid = CAST(rrd_datasource.rrd_datasourceid AS text)
            AND COALESCE(rrd_datasource.threshold, '') = '';
