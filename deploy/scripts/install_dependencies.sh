#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive

echo "=== Updating packages ==="
apt-get update -y

echo "=== Installing Docker ==="
apt-get install -y docker.io

echo "=== Starting Docker ==="
systemctl enable docker
systemctl start docker

echo "=== Installing utilities ==="
apt-get install -y unzip curl

echo "=== Installing AWS CLI ==="

if command -v aws >/dev/null 2>&1; then
    echo "AWS CLI already installed: $(aws --version)"
else
    curl -fsSL \
        "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
        -o /tmp/awscliv2.zip

    rm -rf /tmp/aws

    unzip -q /tmp/awscliv2.zip -d /tmp

    /tmp/aws/install

    rm -rf /tmp/aws /tmp/awscliv2.zip
fi

echo "=== Docker version ==="
docker --version

echo "=== AWS CLI version ==="
aws --version

echo "=== Installation completed successfully ==="