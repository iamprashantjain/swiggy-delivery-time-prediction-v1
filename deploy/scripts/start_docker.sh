#!/bin/bash
set -e

source /home/ubuntu/app/deploy/scripts/.env

echo "=== Logging in to AWS ECR ==="
aws ecr get-login-password --region ap-south-1 | \
docker login \
  --username AWS \
  --password-stdin 739275446561.dkr.ecr.ap-south-1.amazonaws.com

if [ "$(docker ps -q -f name=delivery-time-prediction-api)" ]; then
    docker stop delivery-time-prediction-api
fi

if [ "$(docker ps -aq -f name=delivery-time-prediction-api)" ]; then
    docker rm delivery-time-prediction-api
fi

echo "Cleaning unused Docker images..."
docker image prune -af

echo "Pulling latest image..."
docker pull 739275446561.dkr.ecr.ap-south-1.amazonaws.com/prashant-ecr:latest

echo "Starting new container..."
docker run -d \
  -p 8000:8000 \
  -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
  --name delivery-time-prediction-api \
  --restart always \
  739275446561.dkr.ecr.ap-south-1.amazonaws.com/prashant-ecr:latest

echo "Waiting for FastAPI..."

for i in {1..60}; do
    if curl -s --fail http://localhost:8000/health > /dev/null 2>&1; then
        echo "FastAPI is healthy!"
        exit 0
    fi

    echo "Waiting... attempt $i/60"
    sleep 2
done

echo "FastAPI failed to start"
docker logs delivery-time-prediction-api --tail 50
exit 1