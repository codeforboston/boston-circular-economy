#!/usr/bin/env bash

# Query: Appliance repair shops in Boston city proper
# Notes: Initial exploration, Essentials SKU only

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$GOOGLE_API_KEY" ]; then
  echo "Error: GOOGLE_API_KEY is not set" >&2
  exit 1
fi

curl -X POST \
  'https://places.googleapis.com/v1/places:searchText' \
  -H 'Content-Type: application/json' \
  -H "X-Goog-Api-Key: $GOOGLE_API_KEY" \
  -H 'X-Goog-FieldMask: places.displayName,places.formattedAddress,places.types' \
  -d '{
    "textQuery": "appliance repair",
    "locationBias": {
      "circle": {
        "center": { "latitude": 42.3601, "longitude": -71.0589 },
        "radius": 10000
      }
    }
  }' \
  | jq '.' \
  > "$SCRIPT_DIR/appliance-repair-00.json"
