BEGIN;
CREATE TABLE "auditlog_logentry" ("id" serial NOT NULL PRIMARY KEY, "actor_model" varchar NOT NULL, "actor_pk" varchar NOT NULL, "object_model" varchar NULL, "object_pk" varchar NULL, "target_model" varchar NULL, "target_pk" varchar NULL, "timestamp" timestamp with time zone NOT NULL, "verb" varchar(50) NOT NULL, "summary" text NOT NULL, "subsystem" varchar(50) NULL, "before" text NULL, "after" text NULL);
CREATE INDEX "auditlog_logentry_b512ddf1" ON "auditlog_logentry" ("verb");
CREATE INDEX "auditlog_logentry_verb_210dd763c4f184d9_like" ON "auditlog_logentry" ("verb" varchar_pattern_ops);

COMMIT;
