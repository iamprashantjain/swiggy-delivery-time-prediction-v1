#!/bin/bash

set -e

# Configuration
REGION="ap-south-1"
ECR_REGISTRY="739275446561.dkr.ecr.ap-south-1.amazonaws.com"
ECR_REPOSITORY="prashant-ecr"
IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:latest"
CONTAINER_NAME="delivery-time-prediction-api"


# Login to AWS ECR
echo "Logging in to AWS ECR..."

aws ecr get-login-password \
    --region "$REGION" | \
docker login \
    --username AWS \
    --password-stdin "$ECR_REGISTRY"


# Pull latest Docker image
echo "Pulling latest Docker image..."
docker pull "$IMAGE"


# Stop existing container
echo "Checking existing container..."

if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then

    echo "Stopping existing container..."

    docker stop "$CONTAINER_NAME"

fi


# Remove existing container
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then

    echo "Removing existing container..."

    docker rm "$CONTAINER_NAME"

fi


# Run new container
echo "Starting new FastAPI container..."

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart always \
    -p 8000:8000 \
    -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
    "$IMAGE"


# Wait for FastAPI
echo "Waiting for FastAPI to start..."

for i in {1..30}
do

    if curl -s --fail http://localhost:8000/health > /dev/null
    then

        echo "FastAPI is healthy!"
        exit 0

    fi

    echo "Waiting... attempt $i/30"

    sleep 2

done


# Health check failed
echo "FastAPI failed to start."

echo "Container logs:"
docker logs "$CONTAINER_NAME"

exit 1