#!/bin/bash
# Docker Maintenance Script - Keep Docker clean and optimized

echo "🐳 Docker Maintenance Tool"
echo "=========================="
echo ""

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -gt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1073741824" | bc) GB"
    elif [ $bytes -gt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc) MB"
    else
        echo "$(echo "scale=2; $bytes/1024" | bc) KB"
    fi
}

# Check Docker status
echo "📊 Docker System Status:"
docker system df
echo ""

# Show running containers
echo "📦 Running Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"
echo ""

# Function to clean Docker
clean_docker() {
    echo "🧹 Starting Docker cleanup..."
    echo ""
    
    # Stop all containers
    echo "1. Stopping all containers..."
    docker stop $(docker ps -aq) 2>/dev/null || echo "   No containers to stop"
    
    # Remove stopped containers
    echo "2. Removing stopped containers..."
    docker container prune -f
    
    # Remove unused images
    echo "3. Removing unused images..."
    docker image prune -a -f
    
    # Remove unused volumes
    echo "4. Removing unused volumes..."
    docker volume prune -f
    
    # Remove unused networks
    echo "5. Removing unused networks..."
    docker network prune -f
    
    # Remove build cache
    echo "6. Removing build cache..."
    docker builder prune -a -f
    
    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "📊 After cleanup:"
    docker system df
}

# Function to update all images
update_images() {
    echo "🔄 Updating all Docker images..."
    echo ""
    
    # Get list of images
    images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")
    
    for image in $images; do
        echo "Pulling latest: $image"
        docker pull $image
    done
    
    echo ""
    echo "✅ All images updated!"
}

# Function to backup important containers
backup_containers() {
    echo "💾 Backing up containers..."
    BACKUP_DIR="$HOME/docker-backups"
    mkdir -p "$BACKUP_DIR"
    
    # Get running containers
    containers=$(docker ps --format "{{.Names}}")
    
    for container in $containers; do
        echo "Backing up: $container"
        docker export $container | gzip > "$BACKUP_DIR/${container}_$(date +%Y%m%d).tar.gz"
    done
    
    echo "✅ Backups saved to: $BACKUP_DIR"
}

# Interactive menu
while true; do
    echo ""
    echo "🔧 Docker Maintenance Options:"
    echo "================================"
    echo "1) View system status"
    echo "2) Clean up Docker (remove unused resources)"
    echo "3) Update all images"
    echo "4) Backup running containers"
    echo "5) Restart Docker Desktop"
    echo "6) Show Docker logs"
    echo "7) Prune everything (aggressive cleanup)"
    echo "8) Exit"
    echo ""
    read -p "Select option [1-8]: " choice
    
    case $choice in
        1)
            echo ""
            docker system df
            docker ps -a
            ;;
        2)
            clean_docker
            ;;
        3)
            update_images
            ;;
        4)
            backup_containers
            ;;
        5)
            echo "Restarting Docker Desktop..."
            osascript -e 'quit app "Docker"'
            sleep 2
            open -a Docker
            echo "Docker Desktop restarting..."
            ;;
        6)
            echo "Recent Docker logs:"
            tail -n 50 ~/Library/Containers/com.docker.docker/Data/log/host/docker.log 2>/dev/null || echo "Logs not accessible"
            ;;
        7)
            echo "⚠️  This will remove ALL Docker data!"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                docker system prune -a --volumes -f
                echo "✅ Everything pruned!"
            fi
            ;;
        8)
            echo "Goodbye! 👋"
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
done
