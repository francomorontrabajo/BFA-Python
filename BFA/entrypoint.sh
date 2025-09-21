#!/bin/sh
set -e

# Genesis initialization
if [ ! -d "$NODE_DIRECTORY/geth" ]; then
    echo "Sincronizando desde genesis..."
    geth --datadir "$NODE_DIRECTORY" init "$TESTNET_DIRECTORY/genesis.json"
fi

# Geth initialization
echo "Sincronizando geth..."
exec geth \
    --datadir "$NODE_DIRECTORY" \
    --networkid "$NETWORK_ID" \
    --http \
    --http.addr 0.0.0.0 \
    --http.port 8545 \
    --http.corsdomain "*" \
    --http.vhosts "*" \
    --config "$TESTNET_DIRECTORY/config.toml" \
    --ipcpath "$NODE_DIRECTORY/geth.ipc"