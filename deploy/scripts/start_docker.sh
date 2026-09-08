#!/bin/bash

# Exit immediately if any command fails
set -e

# Variables
ECR_REGISTRY="739275446561.dkr.ecr.ap-south-1.amazonaws.com"
ECR_REPOSITORY="prashant-ecr"
IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:latest"
CONTAINER_NAME="swiggy-delivery-api"
REGION="ap-south-1"

echo "Logging into AWS ECR..."

# Login to ECR
aws ecr get-login-password --region "$REGION" | \
docker login \
    --username AWS \
    --password-stdin "$ECR_REGISTRY"

echo "Pulling latest Docker image..."

# Pull latest image
docker pull "$IMAGE"

echo "Stopping existing container if running..."

# Stop existing container
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    docker stop "$CONTAINER_NAME"
fi

echo "Removing existing container if present..."

# Remove existing container
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    docker rm "$CONTAINER_NAME"
fi

echo "Starting new FastAPI container..."

# Run FastAPI Docker container
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart always \
    -p 8000:8000 \
    -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
    "$IMAGE"

echo "Docker container started."

echo "Waiting for FastAPI application to become healthy..."

# Wait for application startup
for i in {1..30}
do
    if curl -f http://localhost:8000/health > /dev/null 2>&1
    then
        echo "FastAPI application is healthy."
        exit 0
    fi

    echo "Waiting for application... ($i/30)"
    sleep 2
done

echo "FastAPI application failed health check."

# Show container logs for debugging
docker logs "$CONTAINER_NAME"

exit 1