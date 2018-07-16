-- Notify the eventEngine immediately as new events are inserted in the queue
CREATE OR REPLACE RULE eventq_notify AS ON INSERT TO eventq DO ALSO NOTIFY new_event;
