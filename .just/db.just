# Database management recipes

[private]
default:
    @just --list db --unsorted

# Sync/initialize the database schema
sync:
    uv run navsyncdb

# Restore database from a backup file
restore:
    tools/restore-db.sh

# Reset database from remote
reset-remote:
    tools/reset-db-from-remote.sh

# Reset JWT signing keys
reset-jwt:
    tools/reset-jwt-keys.sh
