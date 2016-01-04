-- Set refresh interval on existing message widgets
UPDATE account_navlet
SET preferences = '{"refresh_interval": 60000}'
WHERE navlet = 'nav.web.navlets.messages.MessagesNavlet';
