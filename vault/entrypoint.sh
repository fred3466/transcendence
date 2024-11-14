#!/bin/sh
vault server -dev -dev-listen-address="0.0.0.0:8200" -log-level="info" \
  -dev-root-token-id="roottoken" &

# Set the API address to be accessible via the Docker service name "vault"
export VAULT_ADDR="http://vault:8200"

echo "Waiting for Vault to be ready..."
until curl -s http://127.0.0.1:8200/v1/sys/health > /dev/null; do
  sleep 1
done

# Insert secrets into Vault once it's ready
vault kv put secret/django \
  DB_NAME=${POSTGRES_DB} \
  DB_USER=${POSTGRES_USER} \
  DB_PASSWORD=${POSTGRES_PASSWORD} \
  DB_HOST=${POSTGRES_HOST} \
  DB_PORT=${POSTGRES_PORT}

# Keep the Vault process running in the foreground
wait