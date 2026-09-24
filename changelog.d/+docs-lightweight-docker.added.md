Added and documented a new, more lightweight way to use docker compose for
development. Only the database and graphite is handled by docker, ``nav``
itself is run from CLI.

Note: Incompatible with the old, heavyweight method. Rename an existing `.venv`
if any.
