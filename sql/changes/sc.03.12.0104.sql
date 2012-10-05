-- create new event and alert types for fan and psu alerts

INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('psuState', 'Reports state changes in power supply units', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuNotOK', 'A PSU has entered a non-OK state');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuOK', 'A PSU has returned to an OK state');


INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('fanState', 'Reports state changes in fan units', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanNotOK', 'A fan unit has entered a non-OK state');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanOK', 'A fan unit has returned to an OK state');
