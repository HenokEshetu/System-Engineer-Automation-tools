#!/bin/bash

IMAGE="myapp:latest"
CONTAINER="myapp-container"

echo "Pulling latest image..."
docker pull $IMAGE

echo "Stopping and removing old container..."
docker stop $CONTAINER && docker rm $CONTAINER

echo "Starting new container..."
docker run -d --name $CONTAINER -p 80:80 $IMAGE

echo "Deployment complete!"
