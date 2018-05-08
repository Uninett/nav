-- Rename verbs in audit log entries
UPDATE auditlog_logentry SET verb='enable-interface' WHERE verb='change-status-to-up';
UPDATE auditlog_logentry SET verb='disable-interface' WHERE verb='change-status-to-down';
