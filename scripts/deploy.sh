#!/usr/bin/env sh
set -eu

environment="${1:?usage: scripts/deploy.sh staging|production}"
case "$environment" in
  staging|production) ;;
  *) echo "environment must be staging or production" >&2; exit 2 ;;
esac

env_file=".env.${environment}"
if [ ! -f "$env_file" ]; then
  echo "Missing $env_file. Copy .env.production.example and set deployment secrets." >&2
  exit 1
fi

docker compose --env-file "$env_file" -f docker-compose.prod.yml build --pull
docker compose --env-file "$env_file" -f docker-compose.prod.yml up -d
echo "Deployment to $environment is running. Check: docker compose -f docker-compose.prod.yml ps"
