-- Make MAC addresses optional for netbios entries
ALTER TABLE netbios ALTER COLUMN mac DROP NOT NULL;
