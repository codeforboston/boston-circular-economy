#!/usr/bin/env bash
# Query: Broad circular economy shops in Greater Boston via OpenStreetMap
# Notes: Free, no API key required. Casts wide net by shop type.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

curl -s -X POST \
  'https://overpass-api.de/api/interpreter' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'data=[out:json][timeout:25];
(
  nwr["shop"="tailor"](42.2,-71.2,42.5,-70.9);
  nwr["shop"="second_hand"](42.2,-71.2,42.5,-70.9);
  nwr["shop"="charity"](42.2,-71.2,42.5,-70.9);
  nwr["repair"](42.2,-71.2,42.5,-70.9);
);
out center;' | jq '.' > "$SCRIPT_DIR/broad-search-00.json"
