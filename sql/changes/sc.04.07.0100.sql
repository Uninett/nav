CREATE TABLE "manage"."auditlog_logentry" (
  "id" serial NOT NULL PRIMARY KEY,
  "actor_model" VARCHAR NOT NULL,
  "actor_pk" VARCHAR NOT NULL,
  "object_model" VARCHAR NULL,
  "object_pk" VARCHAR NULL,
  "target_model" VARCHAR NULL,
  "target_pk" VARCHAR NULL,
  "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,
  "verb" VARCHAR(50) NOT NULL,
  "summary" TEXT NOT NULL,
  "subsystem" VARCHAR NULL,
  "before" TEXT NULL,
  "after" TEXT NULL
);

CREATE INDEX "auditlog_logentry_b512ddf1" ON "manage"."auditlog_logentry" ("verb");
CREATE INDEX "auditlog_logentry_verb_210dd763c4f184d9_like" ON "manage"."auditlog_logentry" ("verb" varchar_pattern_ops);
INSERT INTO subsystem (name) VALUES ('auditlog');
