#!/bin/bash
set -e

echo "==> Pulling latest code..."
git pull origin main

echo "==> Building Docker image..."
docker compose build --no-cache

echo "==> Restarting bot..."
docker compose down
docker compose up -d

echo "==> Bot is running. Logs:"
docker compose logs --tail=20
