#!/usr/bin/env bash

# Usage Example:

# Basic usage
# ./deploy.sh
# 
# Custom configuration
# IMAGE_TAG="v1.2.3" \
# HEALTH_CHECK_PATH="/status" \
# SLACK_WEBHOOK="https://hooks.slack.com/..." \
# ./deploy.sh

set -euo pipefail
IFS=$'\n\t'

# Configuration
IMAGE_REPO="myapp"
IMAGE_TAG="latest"
CONTAINER_NAME="myapp-container"
PORT_MAPPING="80:80"
HEALTH_CHECK_PATH="/health"
HEALTH_TIMEOUT=120
SLACK_WEBHOOK=""
LOG_FILE="/var/log/deployments.log"
MAX_RETRIES=3
BACKUP_DIR="/opt/app_backups"
DOCKER_NETWORK="app-network"

# Initialize logging
exec > >(tee -a "$LOG_FILE") 2>&1
echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] === Starting deployment ==="

# Validate dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: $1 not found. Please install it and try again."
        exit 1
    fi
}

check_dependency docker
check_dependency curl
check_dependency jq

# Functions
send_notification() {
    local message="$1"
    echo "$message"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" "$SLACK_WEBHOOK" > /dev/null
    fi
}

cleanup() {
    if docker ps -aq --filter "name=${CONTAINER_NAME}-old" | grep -q .; then
        echo "Cleaning up old container"
        docker rm -f "${CONTAINER_NAME}-old" || true
    fi
}

rollback() {
    echo "Initiating rollback..."
    
    # Stop new container if exists
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    
    # Restore previous container
    if docker ps -aq --filter "name=${CONTAINER_NAME}-old" | grep -q .; then
        echo "Restoring previous version"
        docker rename "${CONTAINER_NAME}-old" "$CONTAINER_NAME"
        docker start "$CONTAINER_NAME"
        send_notification "Rollback successful. Previous version restored."
        return 0
    fi
    
    send_notification "Rollback failed! No backup container available."
    return 1
}

health_check() {
    local container_id="$1"
    local attempt=0
    
    echo "Performing health check..."
    
    while [[ $attempt -lt $MAX_RETRIES ]]; do
        attempt=$((attempt + 1))
        local health_status
        
        # Check Docker health status if defined
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown")
        
        if [[ "$health_status" == "healthy" ]]; then
            echo "Container health status: healthy"
            return 0
        fi
        
        # Application-specific health check
        if [[ -n "$HEALTH_CHECK_PATH" ]]; then
            local container_ip
            container_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_id")
            
            if curl -sSf "http://$container_ip$HEALTH_CHECK_PATH" >/dev/null; then
                echo "Application health check passed"
                return 0
            fi
        fi
        
        echo "Health check attempt $attempt failed. Retrying in 5s..."
        sleep 5
    done
    
    return 1
}

# Main deployment
main() {
    # Backup current container if exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Creating backup of current container"
        docker stop "$CONTAINER_NAME" || true
        docker rename "$CONTAINER_NAME" "${CONTAINER_NAME}-old"
        BACKUP_EXISTS=true
    fi

    # Create Docker network if not exists
    if ! docker network inspect "$DOCKER_NETWORK" &>/dev/null; then
        docker network create "$DOCKER_NETWORK"
    fi

    # Pull new image with retry logic
    local pull_success=false
    for i in $(seq 1 $MAX_RETRIES); do
        echo "Pulling image (attempt $i)..."
        if docker pull "${IMAGE_REPO}:${IMAGE_TAG}"; then
            pull_success=true
            break
        fi
        sleep 10
    done

    if [[ "$pull_success" != "true" ]]; then
        send_notification "Deployment failed: Could not pull image"
        rollback || true
        exit 1
    fi

    # Get image digest for verification
    IMAGE_DIGEST=$(docker inspect --format='{{.RepoDigests}}' "${IMAGE_REPO}:${IMAGE_TAG}" | awk -F'[@]' '{print $2}')

    # Run new container
    echo "Starting new container"
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$DOCKER_NETWORK" \
        -p "$PORT_MAPPING" \
        --restart unless-stopped \
        --log-driver json-file \
        --log-opt max-size=10m \
        --log-opt max-file=3 \
        --health-cmd "curl -f http://localhost${HEALTH_CHECK_PATH} || exit 1" \
        --health-interval 5s \
        --health-retries 3 \
        --health-timeout 2s \
        "${IMAGE_REPO}:${IMAGE_TAG}"

    # Wait for container to initialize
    sleep 5

    # Verify container started
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        send_notification "Deployment failed: Container did not start"
        rollback || true
        exit 1
    fi

    # Perform health check
    if ! health_check "$CONTAINER_NAME"; then
        send_notification "Deployment failed: Health check did not pass"
        rollback
        exit 1
    fi

    # Cleanup old container
    cleanup

    # Final success message
    local new_version
    new_version=$(docker inspect --format='{{.Config.Image}}' "$CONTAINER_NAME")
    send_notification "Deployment successful! Version: ${new_version} Digest: ${IMAGE_DIGEST}"
}

# Execute main function
main