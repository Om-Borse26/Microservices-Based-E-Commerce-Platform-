#!/usr/bin/env bash
set -euo pipefail

# Minimal smoke test exercising core API flow
# Assumes services exposed on localhost via docker compose

log() { echo "[smoke] $*"; }

wait() { bash scripts/wait_for_http.sh "$1" "${2:-60}"; }

log "health checks"
wait http://localhost:5000/health 60
wait http://localhost:5001/health 60
wait http://localhost:5002/health 60
wait http://localhost:5003/health 60
wait http://localhost:5005/health 60

log "seed products"
curl -s -X POST http://localhost:5000/init-data -H 'Content-Type: application/json' | jq . >/dev/null 2>&1 || true

log "register user"
resp=$(curl -s -X POST http://localhost:5001/register -H 'Content-Type: application/json' \
  -d '{"name":"Alice","email":"alice@example.com","password":"Passw0rd!"}')
log "$resp"

log "login user"
login=$(curl -s -X POST http://localhost:5001/login -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"Passw0rd!"}')
log "$login"

log "create order"
order=$(curl -s -X POST http://localhost:5002/orders -H 'Content-Type: application/json' \
  -d '{"user_email":"alice@example.com","items":[{"product_id":1,"quantity":1}]}' )
log "$order"

order_id=$(echo "$order" | jq -r '.order_id // .id // empty')
if [ -z "$order_id" ] || [ "$order_id" = "null" ]; then
  log "could not extract order_id; payload: $order"
  exit 1
fi

log "process payment"
payment=$(curl -s -X POST http://localhost:5003/payments -H 'Content-Type: application/json' \
  -d "{\"order_id\":$order_id,\"amount\":49.99,\"method\":\"card\"}")
log "$payment"

log "smoke tests completed"
