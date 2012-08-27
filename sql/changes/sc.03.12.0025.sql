-- Rename hsrp to virtual to indicate that "some router redundancy protocol
-- tells us this is a virtual router address"
ALTER TABLE gwportprefix RENAME COLUMN hsrp TO virtual;
