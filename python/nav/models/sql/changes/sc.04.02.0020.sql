-- clean up some alert- and event-type descriptions
UPDATE alerttype SET alerttypedesc = 'The IP device has coldstarted'
WHERE alerttype='coldStart';

UPDATE alerttype SET alerttypedesc = 'The IP device has warmstarted'
WHERE alerttype='warmStart';

UPDATE alerttype SET alerttypedesc = 'The device is now in operation with an active IP address'
WHERE alerttype='deviceInIPOperation';

UPDATE alerttype SET alerttypedesc = 'The device is now in operation as a chassis module'
WHERE alerttype='deviceInStack';
