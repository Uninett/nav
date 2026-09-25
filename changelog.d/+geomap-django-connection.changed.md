The geomap data view now uses Django's thread-local, pooled database connection instead of the legacy `nav.db` connection cache, removing the last multithreaded web caller of that cache.
