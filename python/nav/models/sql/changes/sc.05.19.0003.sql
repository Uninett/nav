ALTER TABLE sensor
  ADD threshold_type INT,
  ADD threshold_alert_type INT,
  ADD threshold_for_id INT,
  ADD CONSTRAINT sensor_threshold_for_id_fkey
    FOREIGN KEY (threshold_for_id) REFERENCES sensor(sensorid) ON DELETE CASCADE
;
