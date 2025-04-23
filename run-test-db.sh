#!/bin/bash

# Exit on error
set -e

# Optional: Clean previous test containers
echo "🧹 Cleaning up previous test environment..."
docker compose -f docker-compose.test.yml down -v

# Run test database
echo "🚀 Starting test database..."
docker compose -f docker-compose.test.yml up
