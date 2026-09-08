#!/bin/bash

# Exit immediately if any command fails
set -e

# Ensure that the script runs in non-interactive mode
export DEBIAN_FRONTEND=noninteractive

echo "Installing dependencies..."

# Update package lists
sudo apt-get update -y

# Install Docker and required utilities
sudo apt-get install -y \
    docker.io \
    unzip \
    curl

# Start and enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Install AWS CLI v2
if ! command -v aws &> /dev/null
then
    echo "Installing AWS CLI..."

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
        -o "/home/ubuntu/awscliv2.zip"

    unzip -o /home/ubuntu/awscliv2.zip \
        -d /home/ubuntu/

    sudo /home/ubuntu/aws/install

    # Clean AWS CLI installation files
    rm -rf /home/ubuntu/awscliv2.zip
    rm -rf /home/ubuntu/aws
else
    echo "AWS CLI already installed."
fi

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

echo "Dependencies installation completed."