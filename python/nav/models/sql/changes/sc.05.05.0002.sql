ALTER TABLE sensor
  ADD threshold_type INT,
  ADD threshold_alert_type INT,
  ADD threshold_for_oid_id INT,
  ADD CONSTRAINT fk_threshold_for_oid_id FOREIGN KEY (threshold_for_oid_id) REFERENCES sensor(sensorid);
