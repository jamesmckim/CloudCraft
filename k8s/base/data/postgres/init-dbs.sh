#!/bin/bash
set -e

# The default POSTGRES_USER and POSTGRES_DB are automatically created first.
# This script uses those default credentials to create our secondary database.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER syncer_user WITH PASSWORD '${SYNCER_DB_PASSWORD}';
    CREATE DATABASE thunderstore;
    GRANT ALL PRIVILEGES ON DATABASE thunderstore TO syncer_user;
    
    -- Optional: If you want your main API to be able to read the mods easily
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "$POSTGRES_USER";
EOSQL