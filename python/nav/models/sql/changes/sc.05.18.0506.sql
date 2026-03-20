-- Backfill actor_sortkey from account
UPDATE manage.auditlog_logentry le
SET actor_sortkey = a.login
FROM profiles.account a
WHERE le.actor_model = 'account'
  AND le.actor_pk = a.id::text
  AND le.actor_sortkey IS NULL;

-- Backfill object/target sortkeys from account
UPDATE manage.auditlog_logentry le
SET object_sortkey = a.login
FROM profiles.account a
WHERE le.object_model = 'account'
  AND le.object_pk = a.id::text
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = a.login
FROM profiles.account a
WHERE le.target_model = 'account'
  AND le.target_pk = a.id::text
  AND le.target_sortkey IS NULL;

-- Backfill from netbox (sysname)
UPDATE manage.auditlog_logentry le
SET object_sortkey = n.sysname
FROM manage.netbox n
WHERE le.object_model = 'netbox'
  AND le.object_pk = n.netboxid::text
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = n.sysname
FROM manage.netbox n
WHERE le.target_model = 'netbox'
  AND le.target_pk = n.netboxid::text
  AND le.target_sortkey IS NULL;

-- Backfill from interface (sysname:ifname, matching audit_logname format)
UPDATE manage.auditlog_logentry le
SET object_sortkey = n.sysname || ':' || i.ifname
FROM manage.interface i
JOIN manage.netbox n ON i.netboxid = n.netboxid
WHERE le.object_model = 'interface'
  AND le.object_pk = i.interfaceid::text
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = n.sysname || ':' || i.ifname
FROM manage.interface i
JOIN manage.netbox n ON i.netboxid = n.netboxid
WHERE le.target_model = 'interface'
  AND le.target_pk = i.interfaceid::text
  AND le.target_sortkey IS NULL;

-- Backfill from room (id with optional description)
UPDATE manage.auditlog_logentry le
SET object_sortkey = CASE WHEN r.descr != '' THEN r.roomid || ' (' || r.descr || ')' ELSE r.roomid END
FROM manage.room r
WHERE le.object_model = 'room'
  AND le.object_pk = r.roomid
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = CASE WHEN r.descr != '' THEN r.roomid || ' (' || r.descr || ')' ELSE r.roomid END
FROM manage.room r
WHERE le.target_model = 'room'
  AND le.target_pk = r.roomid
  AND le.target_sortkey IS NULL;

-- Backfill from location (id with optional description)
UPDATE manage.auditlog_logentry le
SET object_sortkey = CASE WHEN l.descr != '' THEN l.locationid || ' (' || l.descr || ')' ELSE l.locationid END
FROM manage.location l
WHERE le.object_model = 'location'
  AND le.object_pk = l.locationid
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = CASE WHEN l.descr != '' THEN l.locationid || ' (' || l.descr || ')' ELSE l.locationid END
FROM manage.location l
WHERE le.target_model = 'location'
  AND le.target_pk = l.locationid
  AND le.target_sortkey IS NULL;

-- Backfill from org (id with optional description)
UPDATE manage.auditlog_logentry le
SET object_sortkey = CASE WHEN o.descr != '' THEN o.orgid || ' (' || o.descr || ')' ELSE o.orgid END
FROM manage.org o
WHERE le.object_model = 'org'
  AND le.object_pk = o.orgid
  AND le.object_sortkey IS NULL;

UPDATE manage.auditlog_logentry le
SET target_sortkey = CASE WHEN o.descr != '' THEN o.orgid || ' (' || o.descr || ')' ELSE o.orgid END
FROM manage.org o
WHERE le.target_model = 'org'
  AND le.target_pk = o.orgid
  AND le.target_sortkey IS NULL;
