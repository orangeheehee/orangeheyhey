#!/bin/bash

# Convert human-readable time to Unix timestamp
TIMEOUT_READABLE=$(date -d '+7 days')
timeout_unix=$(date -d "$TIMEOUT_READABLE" +%s)

# Public Ethereum JSON-RPC endpoint
ETH_NODE_URL="https://rpc.ankr.com/eth"

# Continuously check until the target time is reached
while true; do
    # Fetch the latest block's timestamp
    timestamp_hex=$(curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest", true],"id":1}' $ETH_NODE_URL | jq -r '.result.timestamp')

    # Remove "0x" prefix and convert to decimal
    current_timestamp=$((16#${timestamp_hex#0x}))

    # Check if current Ethereum timestamp has reached the timeout
    if (( current_timestamp >= timeout_unix )); then
        echo "Time release triggered!"
	cat agent/mykey.hex
	echo TWITTER_PASSWORD $TWITTER_PASSWORD
	echo X_PASSWORD $X_PASSWORD
	echo X_AUTH_TOKENS $X_AUTH_TOKENS
	echo PROTONMAIL_PASSWORD $PROTONMAIL_PASSWORD
        break
    else
        echo "Not yet. Waiting until $TIMEOUT_READABLE (Current Ethereum time: $(date -d @$current_timestamp))"
    fi

    # Wait before checking again
    sleep 600
done
