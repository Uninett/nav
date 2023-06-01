INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('juniperYellowAlarmState','Tells us if a Juniper device has any open yellow alarms.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('juniperRedAlarmState','Tells us if a Juniper device has any open red alarms.','y');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('juniperYellowAlarmState','juniperYellowAlarmOn','The Juniper device has some yellow alarms.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('juniperYellowAlarmState','juniperYellowAlarmOff','The Juniper device has no yellow alarms.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('juniperRedAlarmState','juniperRedAlarmOn','The Juniper device has some red alarms.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('juniperRedAlarmState','juniperRedAlarmOff','The Juniper device has no red alarms.');