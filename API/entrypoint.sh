#!/bin/sh

echo "Esperando a que Geth RPC esté listo..."
while ! nc -z bfa 8545; do
  sleep 1
done

echo "Geth RPC disponible, arrancando API..."
exec "$@"