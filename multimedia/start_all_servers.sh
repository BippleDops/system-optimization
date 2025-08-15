#!/bin/bash

# Start All Media Generation and Automation Servers
# This script launches all servers in the background

echo "🚀 Starting Media Generation and Automation Servers..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to start a server
start_server() {
    local name=$1
    local script=$2
    local port=$3
    local log_file="${BASE_DIR}/logs/${name}.log"
    
    echo -e "${BLUE}Starting ${name} on port ${port}...${NC}"
    
    # Create logs directory if it doesn't exist
    mkdir -p "${BASE_DIR}/logs"
    
    # Check if port is already in use
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port ${port} is already in use. Skipping ${name}.${NC}"
        return
    fi
    
    # Start the server in background
    nohup python3 "${BASE_DIR}/${script}" > "${log_file}" 2>&1 &
    local pid=$!
    
    # Save PID for later
    echo $pid > "${BASE_DIR}/logs/${name}.pid"
    
    # Wait a moment and check if it started
    sleep 2
    
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ ${name} started successfully (PID: $pid)${NC}"
        echo -e "   Log: ${log_file}"
    else
        echo -e "${YELLOW}⚠️  Failed to start ${name}${NC}"
        echo -e "   Check log: ${log_file}"
    fi
}

# Install required dependencies if needed
echo -e "${BLUE}Checking dependencies...${NC}"
pip3 list | grep -q fastapi || pip3 install fastapi uvicorn
pip3 list | grep -q aiohttp || pip3 install aiohttp
pip3 list | grep -q psutil || pip3 install psutil
pip3 list | grep -q frontmatter || pip3 install python-frontmatter
pip3 list | grep -q Pillow || pip3 install Pillow

echo ""
echo "Starting servers..."
echo "------------------"

# Start each server
start_server "Audio Generation Server" "audio_generation_server.py" 8001
start_server "Obsidian Management Server" "obsidian_server.py" 8002
start_server "Mac Automation Server" "mac_automation_server.py" 8003
start_server "Unified Media Pipeline" "unified_media_pipeline.py" 8004

# Start ComfyUI if available
if [ -d ~/ComfyUI ]; then
    echo -e "${BLUE}Starting ComfyUI...${NC}"
    cd ~/ComfyUI
    nohup python3 main.py --listen > "${BASE_DIR}/logs/comfyui.log" 2>&1 &
    echo $! > "${BASE_DIR}/logs/comfyui.pid"
    echo -e "${GREEN}✅ ComfyUI started${NC}"
    cd - > /dev/null
fi

# Start Stable Diffusion WebUI if available
if [ -d ~/stable-diffusion-webui ]; then
    echo -e "${BLUE}Starting Stable Diffusion WebUI...${NC}"
    cd ~/stable-diffusion-webui
    nohup ./webui.sh --api > "${BASE_DIR}/logs/sdwebui.log" 2>&1 &
    echo $! > "${BASE_DIR}/logs/sdwebui.pid"
    echo -e "${GREEN}✅ Stable Diffusion WebUI started${NC}"
    cd - > /dev/null
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 All servers started!${NC}"
echo ""
echo "Access your services at:"
echo "  🎵 Audio Generation:    http://localhost:8001"
echo "  📝 Obsidian Management: http://localhost:8002"
echo "  🖥️  Mac Automation:      http://localhost:8003"
echo "  🎬 Media Pipeline:      http://localhost:8004"
echo "  🎨 ComfyUI:            http://localhost:8188"
echo "  🖼️  SD WebUI:           http://localhost:7860"
echo ""
echo "API Documentation:"
echo "  http://localhost:8001/docs"
echo "  http://localhost:8002/docs"
echo "  http://localhost:8003/docs"
echo "  http://localhost:8004/docs"
echo ""
echo "To stop all servers, run: ./stop_all_servers.sh"
echo "To check status, run: ./check_servers.sh"
echo "=================================================="
