#!/usr/bin/env bash

set -euo pipefail

docker compose -f docker-compose-prod.yml up -d --build

# Resolve the application's current IP after its container is recreated.
docker compose -f docker-compose-prod.yml restart nginx
