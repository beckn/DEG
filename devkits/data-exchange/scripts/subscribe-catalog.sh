#!/usr/bin/env bash
# Subscribe a discover service to the catalog service for the testnet-deg
# network. This is a one-time, network-level setup call against the hosted
# catalog at fabric.nfh.global; it does not flow through the local BAP/BPP
# adapters and is not part of the transactional workflow exercised by
# usecase{1,2}/run-arazzo.sh. Re-running is idempotent.

set -euo pipefail

catalogServiceUrl="https://fabric.nfh.global/beckn/catalog/subscription"
discoverServiceUrl="https://34.14.221.66.sslip.io/catalog/push"
networkID="nfh.global/testnet-deg"

curl --location "$catalogServiceUrl" \
  --header 'Content-Type: application/json' \
  --data @- <<EOF
{
  "context": {
    "version": "2.0.0",
    "action": "catalog/subscription",
    "messageId": "b1ae5c45-dc23-4047-89f8-53a90bcf99cf",
    "transactionId": "38c4bf31-cdbc-4432-b555-57b495b68029",
    "timestamp": "2026-03-26T10:00:00.000Z",
    "bapId": "bap.myapp.in",
    "bapUri": "$discoverServiceUrl"
  },
  "message": {
    "subscription": {
      "networkIds": [
        "$networkID"
      ]
    }
  }
}
EOF
