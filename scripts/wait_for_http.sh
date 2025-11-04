#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: $0 <url> <timeout-seconds>" >&2
  exit 2
fi

url="$1"
limit="$2"

for i in $(seq 1 "$limit"); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
    echo "OK: $url -> $code"
    exit 0
  fi
  echo "Waiting for $url (got $code) [$i/$limit]"; sleep 1
 done

echo "ERROR: $url not healthy in ${limit}s" >&2
exit 1
