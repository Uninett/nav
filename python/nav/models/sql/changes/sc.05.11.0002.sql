-- Add new deviceState alert
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceDeletedChassis','The device has been removed as a chassis.');
  INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceDeletedModule','The device has been removed as a module.');
