-- Change notification rule to include target subsystem as payload
CREATE OR REPLACE RULE eventq_notify AS
  ON INSERT TO eventq
  DO ALSO SELECT pg_notify('new_event', NEW.target);
