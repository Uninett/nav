-- Add field for storing user preference for subtracting maintenance
-- downtime from report
ALTER TABLE report_subscription ADD COLUMN exclude_maintenance BOOLEAN;
