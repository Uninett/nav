-- Grant web access to /info for authenticated users
UPDATE AccountGroupPrivilege SET
        target = '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap|info|netmap)/?'
  WHERE target = '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap)/?'
;
