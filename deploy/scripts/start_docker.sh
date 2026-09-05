#!/bin/bash
# Login to AWS ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 739275446561.dkr.ecr.ap-south-1.amazonaws.com

# Pull the latest image
docker pull 739275446561.dkr.ecr.ap-south-1.amazonaws.com/prashant-ecr:latest

# Check if the container 'campusx-app' is running
if [ "$(docker ps -q -f name=my-flask-app)" ]; then
    # Stop the running container
    docker stop my-flask-app
fi

# Check if the container 'my-flask-app' exists (stopped or running)
if [ "$(docker ps -aq -f name=my-flask-app)" ]; then
    # Remove the container if it exists
    docker rm my-flask-app
fi

# Run a new container
docker run -d -p 80:5000 \
  --name my-flask-app \
  --restart always \
  -e DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
  739275446561.dkr.ecr.ap-south-1.amazonaws.com/prashant-ecr:latest