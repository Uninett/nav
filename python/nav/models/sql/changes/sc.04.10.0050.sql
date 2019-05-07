ALTER TABLE sensor ADD COLUMN on_message_user VARCHAR;
ALTER TABLE sensor ADD COLUMN on_message_sys VARCHAR;
ALTER TABLE sensor ADD COLUMN off_message_user VARCHAR;
ALTER TABLE sensor ADD COLUMN off_message_sys VARCHAR;
ALTER TABLE sensor ADD COLUMN on_state_user INT;
ALTER TABLE sensor ADD COLUMN on_state_sys INT;
ALTER TABLE sensor ADD COLUMN alert_type INT;
