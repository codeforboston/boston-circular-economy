#!/usr/bin/env bash
# Query: Repair shops in Greater Boston via OpenStreetMap Overpass API
# Notes: Free, no API key required. Uses repair=* tag.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

curl -s -X POST \
  'https://overpass-api.de/api/interpreter' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'data=[out:json][timeout:25];
    nwr["repair"](42.2,-71.2,42.5,-70.9);
    out center;' \
  | jq '.' > "$SCRIPT_DIR/repair-00.json"
