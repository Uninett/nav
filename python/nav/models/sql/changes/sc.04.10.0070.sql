ALTER TABLE alertsender
  ADD COLUMN supported BOOLEAN DEFAULT true;

UPDATE alertsender
  SET supported=false WHERE handler='jabber';
