-- scripts/init-db.sql
-- Initialize A2AIs database with extensions

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for additional functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'a2ais_user') THEN

      CREATE ROLE a2ais_user LOGIN PASSWORD 'a2ais_password';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE a2ais_db TO a2ais_user;
GRANT ALL ON SCHEMA public TO a2ais_user;