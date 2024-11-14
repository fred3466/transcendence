#!/bin/sh

DB_HOST="db"
DB_PORT="5432"
VAULT_HOST="vault"
VAULT_PORT="8200"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while true; do
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -d "$POSTGRES_DB" -U "$POSTGRES_USER" -c "SELECT 1;" 2>/dev/null 1>/dev/null
    if [ $? -eq 0 ]; then
        echo "Connected to PostgreSQL database."
        break
    fi
    sleep 1
done

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
while true; do
    curl -s http://$VAULT_HOST:$VAULT_PORT/v1/sys/health > /dev/null
    if [ $? -eq 0 ]; then
        echo "Vault is ready."
        break
    fi
    sleep 1
done

# Proceed to start Django application
echo "Starting Django application..."
python3 -m pip install --no-cache-dir daphne
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8000