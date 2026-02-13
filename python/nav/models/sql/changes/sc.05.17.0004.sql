ALTER TABLE manage.auditlog_logentry ADD COLUMN actor_sortkey VARCHAR;
ALTER TABLE manage.auditlog_logentry ADD COLUMN object_sortkey VARCHAR;
ALTER TABLE manage.auditlog_logentry ADD COLUMN target_sortkey VARCHAR;

CREATE INDEX auditlog_logentry_actor_sortkey ON manage.auditlog_logentry (actor_sortkey);
CREATE INDEX auditlog_logentry_object_sortkey ON manage.auditlog_logentry (object_sortkey);
CREATE INDEX auditlog_logentry_target_sortkey ON manage.auditlog_logentry (target_sortkey);
