-- Redact API token secrets from audit log entries (for currently existing tokens,
-- not deleted ones). Related to issue #3683.
--
-- This migration replaces actual API token strings in audit log entries
-- with the new safe format "token #<id> (<comment>)"

DO $$
DECLARE
    token_rec RECORD;
    new_token_str TEXT;
    truncated_comment TEXT;
BEGIN
    -- Iterate through all API tokens and replace their actual token strings
    -- in audit log entries with the safe identifier format
    FOR token_rec IN
        SELECT id, token, comment FROM apitoken
    LOOP
        -- Build the new token string in the same format as APIToken.__str__()
        IF token_rec.comment IS NOT NULL AND token_rec.comment != '' THEN
            -- Truncate comment to 25 characters total (approximating Python's Truncator(comment).chars(25))
            -- Django's Truncator includes the ellipsis in the total count
            IF LENGTH(token_rec.comment) > 25 THEN
                -- Reserve 1 character for ellipsis, truncate content to 24 chars
                truncated_comment := SUBSTRING(token_rec.comment FROM 1 FOR 24) || '…';
            ELSE
                truncated_comment := token_rec.comment;
            END IF;
            new_token_str := 'token #' || token_rec.id || ' (' || truncated_comment || ')';
        ELSE
            new_token_str := 'token #' || token_rec.id;
        END IF;

        -- Update summary field (only for entries that reference this specific token)
        UPDATE auditlog_logentry
        SET summary = REPLACE(summary, token_rec.token, new_token_str)
        WHERE object_model = 'apitoken'
          AND object_pk = token_rec.id::TEXT
          AND summary LIKE '%' || token_rec.token || '%';

        -- Update before field (only for entries that reference this specific token)
        UPDATE auditlog_logentry
        SET before = REPLACE(before, token_rec.token, new_token_str)
        WHERE object_model = 'apitoken'
          AND object_pk = token_rec.id::TEXT
          AND before LIKE '%' || token_rec.token || '%';

        -- Update after field (only for entries that reference this specific token)
        UPDATE auditlog_logentry
        SET after = REPLACE(after, token_rec.token, new_token_str)
        WHERE object_model = 'apitoken'
          AND object_pk = token_rec.id::TEXT
          AND after LIKE '%' || token_rec.token || '%';
    END LOOP;
END $$;
