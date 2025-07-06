# scripts/setup-database.sh
#!/bin/bash

echo "🏗️ Setting up A2AIs database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U a2ais_user -d a2ais_db; do
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run init script
echo "🔧 Running database initialization..."
docker compose exec postgres psql -U a2ais_user -d a2ais_db -f /docker-entrypoint-initdb.d/init-db.sql

# Run migration
echo "📊 Running Python migration..."
docker compose run --rm migration

echo "🎉 Database setup complete!"