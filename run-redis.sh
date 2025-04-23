#!/bin/bash

# Exit on error
set -e

# Redis container name
REDIS_CONTAINER_NAME="bugzot-redis"

# Check if Redis is already running
if [ "$(docker ps -q -f name=$REDIS_CONTAINER_NAME)" ]; then
  echo "🟢 Redis is already running in container '$REDIS_CONTAINER_NAME'"
  exit 0
fi

# If container exists but stopped, remove it
if [ "$(docker ps -aq -f status=exited -f name=$REDIS_CONTAINER_NAME)" ]; then
  echo "♻️ Removing stopped Redis container..."
  docker rm $REDIS_CONTAINER_NAME
fi

# Run Redis container
echo "🚀 Starting Redis container '$REDIS_CONTAINER_NAME'..."
docker run -d \
  --name $REDIS_CONTAINER_NAME \
  -p 6379:6379 \
  redis:7-alpine

echo "✅ Redis is running at localhost:6379"
