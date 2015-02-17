---
-- Add field to unrecognized_neighbor indicating ignored state
---
ALTER TABLE unrecognized_neighbor ADD ignored_since TIMESTAMP DEFAULT NULL;
