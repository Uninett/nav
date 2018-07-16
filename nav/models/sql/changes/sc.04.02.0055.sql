---
-- Replace old status widget with new one.
---
UPDATE account_navlet
  SET navlet='nav.web.navlets.status2.Status2Widget',
      preferences = '{"status_filter": "event_type=boxState&stateless_threshold=24", "refresh_interval": 60000}'
  WHERE navlet='nav.web.navlets.status.StatusNavlet';
