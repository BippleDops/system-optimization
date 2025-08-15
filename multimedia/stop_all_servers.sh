#!/bin/bash

# Stop All Media Generation and Automation Servers

echo "🛑 Stopping all servers..."
echo "========================="

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to stop a server
stop_server() {
    local name=$1
    local pid_file="${BASE_DIR}/logs/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping ${name} (PID: $pid)..."
            kill $pid
            rm "$pid_file"
            echo "✅ ${name} stopped"
        else
            echo "⚠️  ${name} not running (stale PID file)"
            rm "$pid_file"
        fi
    else
        echo "⚠️  No PID file for ${name}"
    fi
}

# Stop each server
stop_server "Audio Generation Server"
stop_server "Obsidian Management Server"
stop_server "Mac Automation Server"
stop_server "Unified Media Pipeline"
stop_server "comfyui"
stop_server "sdwebui"

# Also try to stop by port if PID files are missing
echo ""
echo "Checking for processes on known ports..."
for port in 8001 8002 8003 8004 8188 7860; do
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Stopping process on port $port (PID: $pid)"
        kill $pid
    fi
done

echo ""
echo "✅ All servers stopped"
