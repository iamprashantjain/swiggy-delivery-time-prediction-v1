# #!/bin/bash

# set -e

# # Configuration
# REGION="ap-south-1"
# ECR_REGISTRY="739275446561.dkr.ecr.ap-south-1.amazonaws.com"
# ECR_REPOSITORY="prashant-ecr"
# IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:latest"
# CONTAINER_NAME="delivery-time-prediction-api"


# # Login to AWS ECR
# echo "Logging in to AWS ECR..."

# aws ecr get-login-password \
#     --region "$REGION" | \
# docker login \
#     --username AWS \
#     --password-stdin "$ECR_REGISTRY"


# # Pull latest Docker image
# echo "Pulling latest Docker image..."
# docker pull "$IMAGE"


# # Stop existing container
# echo "Checking existing container..."

# if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then

#     echo "Stopping existing container..."

#     docker stop "$CONTAINER_NAME"

# fi


# # Remove existing container
# if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then

#     echo "Removing existing container..."

#     docker rm "$CONTAINER_NAME"

# fi


# # Run new container
# echo "Starting new FastAPI container..."

# docker run -d \
#     --name "$CONTAINER_NAME" \
#     --restart always \
#     -p 8000:8000 \
#     -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
#     "$IMAGE"


# # Wait for FastAPI
# echo "Waiting for FastAPI to start..."

# for i in {1..30}
# do

#     if curl -s --fail http://localhost:8000/health > /dev/null
#     then

#         echo "FastAPI is healthy!"
#         exit 0

#     fi

#     echo "Waiting... attempt $i/30"

#     sleep 2

# done


# # Health check failed
# echo "FastAPI failed to start."

# echo "Container logs:"
# docker logs "$CONTAINER_NAME"

# exit 1



# =============


#!/bin/bash

set -e

# -----------------------------
# LOAD DAGSHUB_TOKEN FROM .env
# -----------------------------
echo "Loading DAGSHUB_TOKEN..."

# Try multiple locations for .env file
ENV_FILE=""

for path in \
    "/home/ubuntu/app/deploy/scripts/.env" \
    "/opt/codedeploy-agent/deployment-root/*/deployment-archive/deploy/scripts/.env" \
    "./deploy/scripts/.env" \
    "./.env"; do
    
    # Expand wildcard path
    for expanded_path in $path; do
        if [ -f "$expanded_path" ]; then
            ENV_FILE="$expanded_path"
            echo "Found .env at: $ENV_FILE"
            break 2
        fi
    done
done

if [ -z "$ENV_FILE" ]; then
    echo "❌ .env file not found! Cannot get DAGSHUB_TOKEN."
    echo "Looking in: /home/ubuntu/app/deploy/scripts/.env"
    ls -la /home/ubuntu/app/deploy/scripts/ 2>/dev/null || echo "Directory not found"
    exit 1
fi

# Source the .env file
source "$ENV_FILE"

# Verify token was loaded
if [ -z "$DAGSHUB_TOKEN" ]; then
    echo "❌ DAGSHUB_TOKEN is not set in .env file!"
    cat "$ENV_FILE"
    exit 1
fi

echo "✅ DAGSHUB_TOKEN loaded successfully (length: ${#DAGSHUB_TOKEN})"

# -----------------------------
# Configuration
# -----------------------------
REGION="ap-south-1"
ECR_REGISTRY="739275446561.dkr.ecr.ap-south-1.amazonaws.com"
ECR_REPOSITORY="prashant-ecr"
IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:latest"
CONTAINER_NAME="delivery-time-prediction-api"

# Use sudo for docker if needed
DOCKER="sudo docker"

# -----------------------------
# Login to AWS ECR
# -----------------------------
echo "Logging in to AWS ECR..."

aws ecr get-login-password \
    --region "$REGION" | \
$DOCKER login \
    --username AWS \
    --password-stdin "$ECR_REGISTRY"

# -----------------------------
# Pull latest Docker image
# -----------------------------
echo "Pulling latest Docker image..."
$DOCKER pull "$IMAGE"

# -----------------------------
# Stop existing container
# -----------------------------
echo "Checking existing container..."

if [ "$($DOCKER ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing container..."
    $DOCKER stop "$CONTAINER_NAME"
fi

# -----------------------------
# Remove existing container
# -----------------------------
if [ "$($DOCKER ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Removing existing container..."
    $DOCKER rm "$CONTAINER_NAME"
fi

# -----------------------------
# Run new container WITH TOKEN
# -----------------------------
echo "Starting new FastAPI container..."
echo "DAGSHUB_TOKEN is set: ${DAGSHUB_TOKEN:0:10}..."  # Show first 10 chars

$DOCKER run -d \
    --name "$CONTAINER_NAME" \
    --restart always \
    -p 8000:8000 \
    -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
    -e AWS_REGION="$REGION" \
    "$IMAGE"

# -----------------------------
# Wait for FastAPI
# -----------------------------
echo "Waiting for FastAPI to start..."

for i in {1..30}; do
    if curl -s --fail http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ FastAPI is healthy!"
        exit 0
    fi
    echo "Waiting... attempt $i/30"
    sleep 2
done

# -----------------------------
# Health check failed
# -----------------------------
echo "❌ FastAPI failed to start."

echo "Container logs:"
$DOCKER logs "$CONTAINER_NAME" --tail 50

echo "Checking if container is running:"
$DOCKER ps -a | grep "$CONTAINER_NAME"

echo "Checking environment variables in container:"
$DOCKER exec "$CONTAINER_NAME" env | grep DAGSHUB || echo "DAGSHUB_TOKEN not found in container!"

exit 1