-- Add new deviceState alert
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceDeletedFan','The device has been removed as a fan.');
  INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceDeletedPsu','The device has been removed as a power supply.');
